from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView

from .models import Post


class PostListView(ListView):
    model = Post
    template_name = "blog/index.html"
    context_object_name = "posts"
    paginate_by = None

    def get_queryset(self):
        return Post.objects.all().order_by("-created_at")


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = reverse("blog-detail", kwargs={"pk": self.object.pk})
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs.get("pk"))
