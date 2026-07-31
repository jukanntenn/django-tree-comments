from __future__ import annotations

import contextlib
import functools
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from django import http
from django.apps import apps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, resolve_url
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from . import get_comment_flag_model, get_comment_form, get_comment_model, signals

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


class CommentPostBadRequest(http.HttpResponseBadRequest):
    """
    Response returned when a comment post is invalid. If ``DEBUG`` is on a
    nice-ish error message will be displayed (for debugging purposes), but in
    production mode a simple opaque 400 page will be displayed.
    """

    def __init__(self, why: str) -> None:
        super().__init__()
        if settings.DEBUG:
            self.content = render_to_string("tree_comments/400-debug.html", {"why": why})


class BadRequestError(Exception):
    """
    Exception raised for a bad post request holding the CommentPostBadRequest
    object.
    """

    def __init__(self, why: str) -> None:
        self.response = CommentPostBadRequest(why)


def resolve_comment_target(ctype: str | None, object_pk: str | None, using: str | None = None) -> Any:
    """Resolve ``content_type`` + ``object_pk`` to the target object.

    Raises :class:`BadRequestError` (carrying a ``CommentPostBadRequest`` response)
    when the values are missing or do not resolve to a valid object.
    """
    if ctype is None or object_pk is None:
        raise BadRequestError("Missing content_type or object_pk field.")
    try:
        model = apps.get_model(*ctype.split(".", 1))  # type: ignore[arg-type]
        manager = model._default_manager
        if using is not None:
            manager = manager.using(using)
        return manager.get(pk=object_pk)
    except (LookupError, TypeError):
        raise BadRequestError(f"Invalid content_type value: {escape(ctype)!r}") from None
    except AttributeError:
        raise BadRequestError(f"The given content-type {escape(ctype)!r} does not resolve to a valid model.") from None
    except ObjectDoesNotExist:
        raise BadRequestError(
            f"No object matching content-type {escape(ctype)!r} and object PK {escape(object_pk)!r} exists."
        ) from None
    except (ValueError, ValidationError) as e:
        raise BadRequestError(
            f"Attempting to get content-type {escape(ctype)!r} and object PK {escape(object_pk)!r}"
            f" raised {e.__class__.__name__}"
        ) from e


def inject_comment_target(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(view: Any, *args: Any, **kwargs: Any) -> Any:
        request = view.request
        if request.method.upper() == "POST":
            ctype = request.POST.get("content_type")
            object_pk = request.POST.get("object_pk")
        else:
            ctype = request.GET.get("content_type")
            object_pk = request.GET.get("object_pk")

        try:
            target = resolve_comment_target(ctype, object_pk)
            view.kwargs["target"] = target
        except BadRequestError as exc:
            return exc.response
        return func(view, *args, **kwargs)

    wrapper.__wrapped__ = func
    return wrapper


class CommentFormTemplateView(TemplateView):
    template_name = "tree_comments/form.html"

    @inject_comment_target
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        target = self.kwargs.pop("target")

        # Optional parent for reply
        parent_obj = None
        parent_pk = request.GET.get("parent")
        if parent_pk:
            try:
                parent_obj = get_comment_model().objects.get(pk=parent_pk)  # type: ignore[attr-defined]
            except (ObjectDoesNotExist, ValueError):
                parent_obj = None

        form = get_comment_form()(target, parent=parent_obj)  # type: ignore[call-arg]
        accept_header = request.headers.get("accept", "")
        if "application/json" in accept_header:
            return JsonResponse(form.as_json(), status=200)  # type: ignore[attr-defined]
        context = self.get_context_data(**kwargs)
        context["form"] = form
        context["parent"] = parent_obj
        return self.render_to_response(context)


class CommentPostView(FormView):  # type: ignore[type-arg]
    http_method_names = ["post"]  # noqa: RUF012

    target_object: Any = None
    data: Any = None
    object: Any = None

    def wants_html_fragments(self) -> bool:
        fmt = self.request.GET.get("format", "")
        return isinstance(fmt, str) and fmt.lower() == "html"

    def get_form_fragment_template_names(self) -> list[str]:
        model = type(self.target_object)
        return [
            f"tree_comments/{model._meta.app_label}/{model._meta.model_name}/form.html",
            f"tree_comments/{model._meta.app_label}/form.html",
            "tree_comments/form.html",
        ]

    def get_form_fragment_context(self, form: Any) -> dict[str, Any]:
        return {
            "form": form,
            "next": self.data.get("next", self.kwargs.get("next")),
        }

    def get_comment_fragment_template_names(self) -> list[str]:
        model = type(self.target_object)
        return [
            f"tree_comments/{model._meta.app_label}/{model._meta.model_name}/comment.html",
            f"tree_comments/{model._meta.app_label}/comment.html",
            "tree_comments/comment.html",
        ]

    def get_comment_fragment_context(self) -> dict[str, Any]:
        return {
            "comment": self.object,
            "next": self.data.get("next", self.kwargs.get("next")),
        }

    def get_target_object(self, data: Any) -> Any:
        # Look up the object we're trying to comment about.
        return resolve_comment_target(
            data.get("content_type"),
            data.get("object_pk"),
            using=self.kwargs.get("using"),
        )

    def get_form_kwargs(self) -> Any:
        data = self.request.POST.copy()
        if self.request.user.is_authenticated:
            if not data.get("name", ""):
                data["name"] = self.request.user.get_full_name() or self.request.user.get_username()
            if not data.get("email", ""):
                data["email"] = self.request.user.email
        return data

    def get_form_class(self) -> Any:
        """Return the form class to use."""
        return get_comment_form()

    def get_form(self, form_class: Any = None) -> Any:
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.target_object, data=self.data)

    def get_success_url(self) -> str:
        """Return the URL to redirect to after processing a valid form."""
        next_url: str | None = self.data.get("next")
        fallback = self.request.GET.get("next") or self.kwargs.get("next") or "tree-comments-comment-done"
        get_kwargs = {"c": self.object._get_pk_val()}

        if not url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={self.request.get_host()}):
            next_url = resolve_url(fallback)

        if next_url is not None and "#" in next_url:
            tmp = next_url.rsplit("#", 1)
            next_url = tmp[0]
            anchor = "#" + tmp[1]
        else:
            anchor = ""

        safe_url = next_url or ""
        joiner = (("?" in safe_url) and "&") or "?"

        return safe_url + joiner + urlencode(get_kwargs) + anchor

    def create_comment(self, form: Any) -> Any:
        comment = form.get_comment_object(
            site_id=get_current_site(self.request).id  # type: ignore[union-attr]
        )
        comment.ip_address = self.request.META.get("REMOTE_ADDR", None) or None
        if self.request.user.is_authenticated:
            comment.user = self.request.user

        # Signal that the comment is about to be saved
        responses = signals.comment_will_be_posted.send(sender=comment.__class__, comment=comment, request=self.request)

        for receiver, response in responses:
            if response is False:  # type: ignore[comparison-overlap]
                raise BadRequestError(f"comment_will_be_posted receiver {receiver.__name__!r} killed the comment")

        # Save the comment and signal that it was saved
        comment.save()
        signals.comment_was_posted.send(sender=comment.__class__, comment=comment, request=self.request)
        return comment

    def get_template_names(self) -> list[str]:
        if self.template_name is None:
            model = type(self.target_object)
            return [
                # These first two exist for purely historical reasons.
                # Django v1.0 and v1.1 allowed the underscore format for
                # preview templates, so we have to preserve that format.
                f"tree_comments/{model._meta.app_label}_{model._meta.model_name}_preview.html",
                f"tree_comments/{model._meta.app_label}_preview.html",
                # Now the usual directory based template hierarchy.
                f"tree_comments/{model._meta.app_label}/{model._meta.model_name}/preview.html",
                f"tree_comments/{model._meta.app_label}/preview.html",
                "tree_comments/preview.html",
            ]
        return [self.template_name]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = context.get("form") or kwargs.get("form")
        context["comment"] = form.data.get("comment", "") if form else ""
        context["next"] = self.data.get("next", self.kwargs.get("next"))
        return context

    def form_invalid(self, form: Any) -> HttpResponse:
        if self.wants_html_fragments():
            html = render_to_string(
                self.get_form_fragment_template_names(),
                self.get_form_fragment_context(form),
                request=self.request,
            )
            return http.HttpResponse(html, content_type="text/html; charset=utf-8")
        return super().form_invalid(form)

    def form_valid(self, form: Any) -> HttpResponse:
        if self.wants_html_fragments():
            html = render_to_string(
                self.get_comment_fragment_template_names(),
                self.get_comment_fragment_context(),
                request=self.request,
            )
            return http.HttpResponse(html, content_type="text/html; charset=utf-8")
        return super().form_valid(form)

    @method_decorator(csrf_protect)
    def dispatch(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(*args, **kwargs)  # type: ignore[return-value]

    def post(self, request: HttpRequest, **kwargs: Any) -> HttpResponse:
        self.object = None
        self.target_object = None
        self.data = self.get_form_kwargs()
        try:
            self.target_object = self.get_target_object(self.data)
        except BadRequestError as exc:
            return exc.response

        form = self.get_form()

        # Check security information
        if form.security_errors():
            return CommentPostBadRequest(
                f"The comment form failed security verification: {escape(str(form.security_errors()))}"
            )

        if not form.is_valid() or "preview" in self.data:
            return self.form_invalid(form)
        try:
            self.object = self.create_comment(form)
        except BadRequestError as exc:
            return exc.response
        else:
            return self.form_valid(form)


class CommentActionRedirectMixin:
    def build_success_url(self, *, fallback: str | None, comment_pk: int | None) -> str:
        next_url = self.request.POST.get("next") or self.request.GET.get("next")  # type: ignore[attr-defined]

        if not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},  # type: ignore[attr-defined]
        ):
            next_url = resolve_url(fallback)  # type: ignore[arg-type]

        get_kwargs = {"c": comment_pk}

        if next_url is not None and "#" in next_url:
            tmp = next_url.rsplit("#", 1)
            next_url = tmp[0]
            anchor = "#" + tmp[1]
        else:
            anchor = ""

        safe_url: str = next_url or ""
        joiner: str = (("?" in safe_url) and "&") or "?"
        result: str = safe_url + joiner + urlencode(get_kwargs) + anchor

        return result


class CommentModerationPermissionMixin(LoginRequiredMixin):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        perm = f"{get_comment_model()._meta.app_label}.can_moderate"
        if request.user.is_authenticated and not request.user.has_perm(perm):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)  # type: ignore[return-value]


class BaseCommentActionView(CommentActionRedirectMixin, TemplateView):
    http_method_names = ["get", "post"]  # noqa: RUF012
    fallback_success_url_name: str | None = None

    comment: Any

    def get_comment(self) -> Any:
        return get_object_or_404(
            get_comment_model(),
            pk=self.kwargs["comment_id"],
            site__pk=get_current_site(self.request).pk,  # type: ignore[union-attr]
        )

    def get_next_value(self) -> str | None:
        return self.request.GET.get("next") or self.request.POST.get("next")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["comment"] = self.comment
        context["next"] = self.get_next_value()
        return context

    def perform_action(self) -> None:
        raise NotImplementedError

    @method_decorator(csrf_protect)
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)  # type: ignore[return-value]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.comment = self.get_comment()
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.comment = self.get_comment()
        self.perform_action()
        return http.HttpResponseRedirect(
            self.build_success_url(
                fallback=self.fallback_success_url_name,
                comment_pk=self.comment.pk,
            )
        )


class FlagView(LoginRequiredMixin, BaseCommentActionView):
    template_name = "tree_comments/flag.html"
    fallback_success_url_name = "tree-comments-flag-done"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)  # type: ignore[return-value]

    def perform_action(self) -> None:
        flag_model = get_comment_flag_model()
        flag, created = flag_model.objects.get_or_create(  # type: ignore[attr-defined]
            comment=self.comment,
            user=self.request.user,
            flag=flag_model.SUGGEST_REMOVAL,  # type: ignore[attr-defined]
        )
        signals.comment_was_flagged.send(
            sender=self.comment.__class__,
            comment=self.comment,
            flag=flag,
            created=created,
            request=self.request,
        )


class DeleteView(CommentModerationPermissionMixin, BaseCommentActionView):
    template_name = "tree_comments/delete.html"
    fallback_success_url_name = "tree-comments-delete-done"

    def perform_action(self) -> None:
        flag_model = get_comment_flag_model()
        flag, created = flag_model.objects.get_or_create(  # type: ignore[attr-defined]
            comment=self.comment,
            user=self.request.user,
            flag=flag_model.MODERATOR_DELETION,  # type: ignore[attr-defined]
        )
        self.comment.is_removed = True
        self.comment.save(update_fields=["is_removed"])
        signals.comment_was_flagged.send(
            sender=self.comment.__class__,
            comment=self.comment,
            flag=flag,
            created=created,
            request=self.request,
        )


class ApproveView(CommentModerationPermissionMixin, BaseCommentActionView):
    template_name = "tree_comments/approve.html"
    fallback_success_url_name = "tree-comments-approve-done"

    def perform_action(self) -> None:
        flag_model = get_comment_flag_model()
        flag, created = flag_model.objects.get_or_create(  # type: ignore[attr-defined]
            comment=self.comment,
            user=self.request.user,
            flag=flag_model.MODERATOR_APPROVAL,  # type: ignore[attr-defined]
        )
        self.comment.is_removed = False
        self.comment.is_public = True
        self.comment.save(update_fields=["is_removed", "is_public"])
        signals.comment_was_flagged.send(
            sender=self.comment.__class__,
            comment=self.comment,
            flag=flag,
            created=created,
            request=self.request,
        )


class CommentActionDoneView(TemplateView):
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        comment = None
        if "c" in self.request.GET:
            with contextlib.suppress(ObjectDoesNotExist, ValueError):
                comment = get_comment_model().objects.get(pk=self.request.GET["c"])  # type: ignore[attr-defined]
        context["comment"] = comment

        return context


class FlagDoneView(CommentActionDoneView):
    template_name = "tree_comments/flagged.html"


class DeleteDoneView(CommentActionDoneView):
    template_name = "tree_comments/deleted.html"


class ApproveDoneView(CommentActionDoneView):
    template_name = "tree_comments/approved.html"


class CommentDoneView(CommentActionDoneView):
    template_name = "tree_comments/posted.html"


class ReplyView(TemplateView):
    template_name = "tree_comments/reply.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = _("Reply to comment")
        return context

    @inject_comment_target
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        target = self.kwargs.pop("target")
        parent_id = self.kwargs["comment_id"]
        parent = get_object_or_404(get_comment_model(), pk=parent_id)

        form = get_comment_form()(target, parent=parent)  # type: ignore[call-arg]

        context = self.get_context_data(**kwargs)
        context["form"] = form
        context["parent"] = parent
        context["next"] = self.request.GET.get("next") or self.kwargs.get("next")
        return self.render_to_response(context)
