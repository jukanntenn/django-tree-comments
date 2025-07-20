from django.urls import path

from .views import PostDetailView, PostListView

urlpatterns = [
    path("", PostListView.as_view(), name="blog-index"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="blog-detail"),
]
