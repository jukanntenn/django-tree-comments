import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-change-me-in-production-please"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "tree_comments",
    "blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "default.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "default.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql"
        if os.environ.get("TREE_COMMENTS_DB_BACKEND", "").lower() == "postgres"
        else "django.db.backends.sqlite3",
        "NAME": os.environ.get("TREE_COMMENTS_DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("TREE_COMMENTS_DB_USER", "treecomments"),
        "PASSWORD": os.environ.get("TREE_COMMENTS_DB_PASSWORD", "treecomments"),
        "HOST": os.environ.get("TREE_COMMENTS_DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("TREE_COMMENTS_DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "blog" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = 1

COMMENTS_APP = "tree_comments"
TREE_COMMENTS_COMMENT_MODEL = "tree_comments.Comment"
