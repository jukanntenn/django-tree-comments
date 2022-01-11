import importlib

from tree_comments import serializers


def test_use_default_user_serializer():
    assert serializers.UserSerializer.__name__ == "DefaultUserSerializer"


def test_use_custom_user_serializer(settings):
    settings.TREE_COMMENTS_USER_SERIALIZER = "tests.default_app.serializers.MyUserSerializer"
    importlib.reload(serializers)
    assert serializers.UserSerializer.__name__ == "MyUserSerializer"
