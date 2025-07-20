import functools
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
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from . import get_comment_flag_model, get_comment_form, get_comment_model, signals


class CommentPostBadRequest(http.HttpResponseBadRequest):
    """
    Response returned when a comment post is invalid. If ``DEBUG`` is on a
    nice-ish error message will be displayed (for debugging purposes), but in
    production mode a simple opaque 400 page will be displayed.
    """

    def __init__(self, why):
        super().__init__()
        if settings.DEBUG:
            self.content = render_to_string(
                "tree_comments/400-debug.html", {"why": why}
            )


class BadRequest(Exception):
    """
    Exception raised for a bad post request holding the CommentPostBadRequest
    object.
    """

    def __init__(self, why):
        self.response = CommentPostBadRequest(why)


def inject_comment_target(func):
    @functools.wraps(func)
    def wrapper(view, *args, **kwargs):
        request = view.request
        if request.method.upper() == "POST":
            ctype = request.POST.get("content_type")
            object_pk = request.POST.get("object_pk")
        else:
            ctype = request.GET.get("content_type")
            object_pk = request.GET.get("object_pk")

        if ctype is None or object_pk is None:
            return CommentPostBadRequest("Missing content_type or object_pk field.")

        try:
            model = apps.get_model(*ctype.split(".", 1))
            target = model.objects.get(pk=object_pk)
            view.kwargs["target"] = target
        except (LookupError, TypeError):
            return CommentPostBadRequest(
                "Invalid content_type value: %r" % escape(ctype)
            )
        except AttributeError:
            return CommentPostBadRequest(
                "The given content-type %r does not resolve to a valid model."
                % escape(ctype)
            )
        except ObjectDoesNotExist:
            return CommentPostBadRequest(
                "No object matching content-type %r and object PK %r exists."
                % (escape(ctype), escape(object_pk))
            )
        except (ValueError, ValidationError) as e:
            return CommentPostBadRequest(
                "Attempting to get content-type %r and object PK %r raised %s"
                % (escape(ctype), escape(object_pk), e.__class__.__name__)
            )
        return func(view, *args, **kwargs)

    wrapper.__wrapped__ = func
    return wrapper


class CommentFormTemplateView(TemplateView):
    template_name = "tree_comments/form.html"

    @inject_comment_target
    def get(self, request, *args, **kwargs):
        target = self.kwargs.pop("target")

        # Optional parent for reply
        parent_obj = None
        parent_pk = request.GET.get("parent")
        if parent_pk:
            try:
                parent_obj = get_comment_model().objects.get(pk=parent_pk)
            except (ObjectDoesNotExist, ValueError):
                parent_obj = None

        form = get_comment_form()(target, parent=parent_obj)
        accept_header = request.META.get("HTTP_ACCEPT", "")
        if "application/json" in accept_header:
            return JsonResponse(form.as_json(), status=200)
        else:
            context = self.get_context_data(**kwargs)
            context["form"] = form
            context["parent"] = parent_obj
            return self.render_to_response(context)


class CommentPostView(FormView):
    http_method_names = ["post"]

    def wants_html_fragments(self):
        fmt = self.request.GET.get("format", "")
        return isinstance(fmt, str) and fmt.lower() == "html"

    def get_form_fragment_template_names(self):
        model = type(self.target_object)
        return [
            "tree_comments/%s/%s/form.html"
            % (model._meta.app_label, model._meta.model_name),
            "tree_comments/%s/form.html" % model._meta.app_label,
            "tree_comments/form.html",
        ]

    def get_form_fragment_context(self, form):
        return {
            "form": form,
            "next": self.data.get("next", self.kwargs.get("next")),
        }

    def get_comment_fragment_template_names(self):
        model = type(self.target_object)
        return [
            "tree_comments/%s/%s/comment.html"
            % (model._meta.app_label, model._meta.model_name),
            "tree_comments/%s/comment.html" % model._meta.app_label,
            "tree_comments/comment.html",
        ]

    def get_comment_fragment_context(self):
        return {
            "comment": self.object,
            "next": self.data.get("next", self.kwargs.get("next")),
        }

    def get_target_object(self, data):
        # Look up the object we're trying to comment about
        ctype = data.get("content_type")
        object_pk = data.get("object_pk")
        if ctype is None or object_pk is None:
            raise BadRequest("Missing content_type or object_pk field.")
        try:
            model = apps.get_model(*ctype.split(".", 1))
            return model._default_manager.using(self.kwargs.get("using")).get(
                pk=object_pk
            )
        except (LookupError, TypeError):
            raise BadRequest("Invalid content_type value: %r" % escape(ctype))
        except AttributeError:
            raise BadRequest(
                "The given content-type %r does not resolve to a valid model."
                % escape(ctype)
            )
        except ObjectDoesNotExist:
            raise BadRequest(
                "No object matching content-type %r and object PK %r exists."
                % (escape(ctype), escape(object_pk))
            )
        except (ValueError, ValidationError) as e:
            raise BadRequest(
                "Attempting to get content-type %r and object PK %r raised %s"
                % (escape(ctype), escape(object_pk), e.__class__.__name__)
            )

    def get_form_kwargs(self):
        data = self.request.POST.copy()
        if self.request.user.is_authenticated:
            if not data.get("name", ""):
                data["name"] = (
                    self.request.user.get_full_name()
                    or self.request.user.get_username()
                )
            if not data.get("email", ""):
                data["email"] = self.request.user.email
        return data

    def get_form_class(self):
        """Return the form class to use."""
        return get_comment_form()

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.target_object, data=self.data)

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        next = self.data.get("next")
        fallback = (
            self.request.GET.get("next")
            or self.kwargs.get("next")
            or "tree-comments-comment-done"
        )
        get_kwargs = dict(c=self.object._get_pk_val())

        if not url_has_allowed_host_and_scheme(
            url=next, allowed_hosts={self.request.get_host()}
        ):
            next = resolve_url(fallback)

        if "#" in next:
            tmp = next.rsplit("#", 1)
            next = tmp[0]
            anchor = "#" + tmp[1]
        else:
            anchor = ""

        joiner = ("?" in next) and "&" or "?"
        next += joiner + urlencode(get_kwargs) + anchor

        return next

    def create_comment(self, form):
        comment = form.get_comment_object(site_id=get_current_site(self.request).id)
        comment.ip_address = self.request.META.get("REMOTE_ADDR", None) or None
        if self.request.user.is_authenticated:
            comment.user = self.request.user

        # Signal that the comment is about to be saved
        responses = signals.comment_will_be_posted.send(
            sender=comment.__class__, comment=comment, request=self.request
        )

        for receiver, response in responses:
            if response is False:
                raise BadRequest(
                    "comment_will_be_posted receiver %r killed the comment"
                    % receiver.__name__
                )

        # Save the comment and signal that it was saved
        comment.save()
        signals.comment_was_posted.send(
            sender=comment.__class__, comment=comment, request=self.request
        )
        return comment

    def get_template_names(self):
        if self.template_name is None:
            model = type(self.target_object)
            return [
                # These first two exist for purely historical reasons.
                # Django v1.0 and v1.1 allowed the underscore format for
                # preview templates, so we have to preserve that format.
                "tree_comments/%s_%s_preview.html"
                % (model._meta.app_label, model._meta.model_name),
                "tree_comments/%s_preview.html" % model._meta.app_label,
                # Now the usual directory based template hierarchy.
                "tree_comments/%s/%s/preview.html"
                % (model._meta.app_label, model._meta.model_name),
                "tree_comments/%s/preview.html" % model._meta.app_label,
                "tree_comments/preview.html",
            ]
        else:
            return [self.template_name]

    def get_context_data(self, form):
        return dict(
            form=form,
            comment=form.data.get("comment", ""),
            next=self.data.get("next", self.kwargs.get("next")),
        )

    def form_invalid(self, form):
        if self.wants_html_fragments():
            html = render_to_string(
                self.get_form_fragment_template_names(),
                self.get_form_fragment_context(form),
                request=self.request,
            )
            return http.HttpResponse(html, content_type="text/html; charset=utf-8")
        return super().form_invalid(form)

    def form_valid(self, form):
        if self.wants_html_fragments():
            html = render_to_string(
                self.get_comment_fragment_template_names(),
                self.get_comment_fragment_context(),
                request=self.request,
            )
            return http.HttpResponse(html, content_type="text/html; charset=utf-8")
        return super().form_valid(form)

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, **kwargs):
        self.object = None
        self.target_object = None
        self.data = self.get_form_kwargs()
        try:
            self.target_object = self.get_target_object(self.data)
        except BadRequest as exc:
            return exc.response

        form = self.get_form()

        # Check security information
        if form.security_errors():
            return CommentPostBadRequest(
                "The comment form failed security verification: %s"
                % escape(str(form.security_errors()))
            )

        if not form.is_valid() or "preview" in self.data:
            return self.form_invalid(form)
        else:
            try:
                self.object = self.create_comment(form)
            except BadRequest as exc:
                return exc.response
            else:
                return self.form_valid(form)


class CommentActionRedirectMixin:
    def build_success_url(self, *, fallback, comment_pk):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")

        if not url_has_allowed_host_and_scheme(
            url=next_url, allowed_hosts={self.request.get_host()}
        ):
            next_url = resolve_url(fallback)

        get_kwargs = dict(c=comment_pk)

        if "#" in next_url:
            tmp = next_url.rsplit("#", 1)
            next_url = tmp[0]
            anchor = "#" + tmp[1]
        else:
            anchor = ""

        joiner = ("?" in next_url) and "&" or "?"
        next_url += joiner + urlencode(get_kwargs) + anchor

        return next_url


class CommentModerationPermissionMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        perm = f"{get_comment_model()._meta.app_label}.can_moderate"
        if request.user.is_authenticated and not request.user.has_perm(perm):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class BaseCommentActionView(CommentActionRedirectMixin, TemplateView):
    http_method_names = ["get", "post"]
    fallback_success_url_name = None

    def get_comment(self):
        return get_object_or_404(
            get_comment_model(),
            pk=self.kwargs["comment_id"],
            site__pk=get_current_site(self.request).pk,
        )

    def get_next_value(self):
        return self.request.GET.get("next") or self.request.POST.get("next")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment"] = self.comment
        context["next"] = self.get_next_value()
        return context

    def perform_action(self):
        raise NotImplementedError

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.comment = self.get_comment()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
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

    def perform_action(self):
        flag_model = get_comment_flag_model()
        flag, created = flag_model.objects.get_or_create(
            comment=self.comment,
            user=self.request.user,
            flag=flag_model.SUGGEST_REMOVAL,
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

    def perform_action(self):
        flag_model = get_comment_flag_model()
        flag, created = flag_model.objects.get_or_create(
            comment=self.comment,
            user=self.request.user,
            flag=flag_model.MODERATOR_DELETION,
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

    def perform_action(self):
        flag_model = get_comment_flag_model()
        flag, created = flag_model.objects.get_or_create(
            comment=self.comment,
            user=self.request.user,
            flag=flag_model.MODERATOR_APPROVAL,
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
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        comment = None
        if "c" in self.request.GET:
            try:
                comment = get_comment_model().objects.get(pk=self.request.GET["c"])
            except (ObjectDoesNotExist, ValueError):
                pass
        context["comment"] = comment

        return context


class FlagDoneView(CommentActionDoneView):
    template_name = "tree_comments/flagged.html"


class DeleteDoneView(CommentActionDoneView):
    template_name = "tree_comments/deleted.html"


class ApproveDoneView(CommentActionDoneView):
    template_name = "tree_comments/approved.html"


class CommentDoneView(TemplateView):
    template_name = "tree_comments/posted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        comment = None
        if "c" in self.request.GET:
            try:
                comment = get_comment_model().objects.get(pk=self.request.GET["c"])
            except (ObjectDoesNotExist, ValueError):
                pass
        context["comment"] = comment

        return context


class ReplyView(TemplateView):
    template_name = "tree_comments/reply.html"

    @inject_comment_target
    def get(self, request, *args, **kwargs):
        target = self.kwargs.pop("target")
        parent_id = self.kwargs["comment_id"]
        parent = get_object_or_404(get_comment_model(), pk=parent_id)

        form = get_comment_form()(target, parent=parent)

        context = self.get_context_data(**kwargs)
        context["form"] = form
        context["next"] = self.request.GET.get("next") or self.kwargs.get("next")
        return self.render_to_response(context)
