from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from tree_comments.models import Comment

from .models import Post


class PostListView(ListView):
    model = Post
    template_name = "blog/index.html"
    context_object_name = "posts"

    def get_queryset(self):
        return Post.objects.all()


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = reverse("blog-detail", kwargs={"pk": self.object.pk})
        return context


@login_required
@require_POST
def htmx_delete_comment(request, comment_id):
    """Soft-delete a comment and return the re-rendered fragment for HTMX swap."""
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        return HttpResponse(status=404)
    if not (request.user.is_staff or comment.user_id == request.user.id):
        return HttpResponse(status=403)
    comment.is_removed = True
    comment.save(update_fields=["is_removed"])
    node = {"comment": comment, "children": []}
    html = render_to_string(
        "tree_comments/comment.html",
        {"node": node, "request": request},
        request=request,
    )
    return HttpResponse(html)
