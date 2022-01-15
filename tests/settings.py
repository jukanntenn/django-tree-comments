# suppress RemovedInDjango50Warning
USE_TZ = True

SECRET_KEY = "test-secret-key"
ROOT_URLCONF = "tests.urls"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tree_comments",
    "tests.app",
]
TREE_COMMENT_MODEL = "app.Comment"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
# DRF-extensions
# ------------------------------------------------------------------------------
# http://chibisov.github.io/drf-extensions/docs/#settings
REST_FRAMEWORK_EXTENSIONS = {
    "DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX": "",
}

# Django REST framework
# ------------------------------------------------------------------------------
# https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        # For browserable API when develop. Must behind TokenAuthentication,
        # otherwise unauthorized request will response 403 instead of 401.
        "rest_framework.authentication.SessionAuthentication",
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
