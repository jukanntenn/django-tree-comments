import pytest
from django.contrib.auth.models import User
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from tests.app.models import Comment, Post
from tree_comments.serializers import TreeCommentListWithParentUserSerializer


@pytest.mark.django_db
class TestTreeCommentListViewSet:
    def setup_method(self, method):
        self.api_client = APIClient()
        self.user = User.objects.create_user(username="user", password="password", email="user@example.com")
        self.post1 = Post.objects.create(title="test post1", author=self.user)

        self.comment_1a = Comment.objects.create(content="test comment 1a", post=self.post1, user=self.user)
        self.comment_1aa = Comment.objects.create(content="test comment 1aa", post=self.post1, user=self.user)
        self.comment_1aaa = Comment.objects.create(content="test comment 1aaa", post=self.post1, user=self.user)
        self.comment_1b = Comment.objects.create(content="test comment 1b", post=self.post1, user=self.user)
        self.comment_1c = Comment.objects.create(content="test comment 1c", post=self.post1, user=self.user)
        self.comment_1cc = Comment.objects.create(content="test comment 1cc", post=self.post1, user=self.user)

        self.post2 = Post.objects.create(title="test post2", author=self.user)
        self.comment_2a = Comment.objects.create(content="test comment 2a", post=self.post2, user=self.user)
        self.comment_2b = Comment.objects.create(content="test comment 2b", post=self.post2, user=self.user)
        self.comment_2bb = Comment.objects.create(content="test comment 2bb", post=self.post2, user=self.user)

        self.list_url1 = reverse("posts-comment-list", kwargs={"post_id": self.post1.id})
        self.list_url2 = reverse("posts-comment-list", kwargs={"post_id": self.post2.id})

    def teardown_method(self, method):
        self.api_client.force_authenticate(user=None)

    def test_permission(self):
        response = self.api_client.get(self.list_url1)
        assert response.status_code == 200

    def test_list(self):
        response = self.api_client.get(self.list_url1)
        assert response.status_code == 200
        serializer = TreeCommentListWithParentUserSerializer(
            instance=[
                self.comment_1a,
                self.comment_1aa,
                self.comment_1aaa,
                self.comment_1b,
                self.comment_1c,
                self.comment_1cc,
            ],
            many=True,
        )
        assert serializer.data == response.data["results"]

        response = self.api_client.get(self.list_url2)
        assert response.status_code == 200
        serializer = TreeCommentListWithParentUserSerializer(
            instance=[
                self.comment_2a,
                self.comment_2b,
                self.comment_2bb,
            ],
            many=True,
        )
        assert serializer.data == response.data["results"]


@pytest.mark.django_db
class TestTreeCommentCreateUpdateViewSet:
    def setup_method(self, method):
        self.api_client = APIClient()
        self.user = User.objects.create_user(username="user", password="password", email="user@example.com")
        self.post = Post.objects.create(title="test post1", author=self.user)
        self.comment = Comment.objects.create(content="test comment", post=self.post, user=self.user)

        self.list_url = reverse("comment-list")
        self.detail_url = reverse("comment-detail", kwargs={"pk": self.comment.pk})

    def teardown_method(self, method):
        self.api_client.force_authenticate(user=None)

    def test_permission(self):
        response = self.api_client.post(self.list_url, data={})
        assert response.status_code == 401

        response = self.api_client.patch(self.detail_url, data={})
        assert response.status_code == 401

    def test_create(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            self.list_url, data={"post": self.post.id, "content": "comment content from test create"}
        )
        assert response.status_code == 201

    def test_create_with_invalid_data(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(self.list_url, data={"post": self.post.id})
        assert response.status_code == 400
        assert "content" in response.data

    def test_update(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.patch(self.detail_url, data={"content": "updated comment content"})
        assert response.status_code == 200

    def test_update_with_invalid_data(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.patch(self.detail_url, data={"content": ""})
        assert response.status_code == 400
        assert "content" in response.data

    def test_update_nonexistent_comment(self):
        self.api_client.force_authenticate(user=self.user)
        url = reverse("comment-detail", kwargs={"pk": 99999})
        response = self.api_client.patch(url, data={"content": "updated comment content"})
        assert response.status_code == 404
