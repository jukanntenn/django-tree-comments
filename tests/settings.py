import os

# suppress RemovedInDjango50Warning
USE_TZ = True

SITE_ID = 1

SECRET_KEY = "test-secret-key"
ROOT_URLCONF = "tests.urls"


def _build_databases():
    """Select the database backend based on the TREE_COMMENTS_DB_BACKEND env var.

    - sqlite (default): **on-disk file** SQLite (matches production deployments;
      an in-memory database does not reflect production reality — OS page cache
      behavior, cold-start latency, and tracemalloc memory measurements all differ
      from :memory:). Set TREE_COMMENTS_SQLITE_IN_MEMORY=1 for zero-dependency,
      fast smoke tests.
    - postgres: connect to PostgreSQL at TREE_COMMENTS_DB_HOST (default localhost).
    - mysql:    connect to MySQL.
    Username / password / database name / port can all be overridden via env vars;
    defaults are shown below.
    """
    backend = os.environ.get("TREE_COMMENTS_DB_BACKEND", "sqlite").lower()

    if backend == "postgres":
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.environ.get("TREE_COMMENTS_DB_NAME", "tree_comments_perf"),
                "USER": os.environ.get("TREE_COMMENTS_DB_USER", "treecomments"),
                "PASSWORD": os.environ.get("TREE_COMMENTS_DB_PASSWORD", "treecomments"),
                # Use 127.0.0.1 to force TCP (localhost is sometimes parsed specially by certain clients).
                "HOST": os.environ.get("TREE_COMMENTS_DB_HOST", "127.0.0.1"),
                "PORT": os.environ.get("TREE_COMMENTS_DB_PORT", "5432"),
            }
        }
    if backend == "mysql":
        return {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": os.environ.get("TREE_COMMENTS_DB_NAME", "tree_comments_perf"),
                "USER": os.environ.get("TREE_COMMENTS_DB_USER", "treecomments"),
                "PASSWORD": os.environ.get("TREE_COMMENTS_DB_PASSWORD", "treecomments"),
                # Must use 127.0.0.1: MySQLdb treats host="localhost" as a Unix socket
                # (/tmp/mysql.sock) instead of TCP. Use 127.0.0.1 to force a TCP connection to the container.
                "HOST": os.environ.get("TREE_COMMENTS_DB_HOST", "127.0.0.1"),
                "PORT": os.environ.get("TREE_COMMENTS_DB_PORT", "3306"),
            }
        }
    # Default to an on-disk sqlite database. The file path can be overridden via TREE_COMMENTS_DB_NAME;
    # the default includes the current PID to avoid file collisions when multiple harness instances run concurrently.
    # Set TREE_COMMENTS_SQLITE_IN_MEMORY=1 to fall back to :memory: (only for zero-dependency fast smoke tests).
    if os.environ.get("TREE_COMMENTS_SQLITE_IN_MEMORY", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        # In-memory database: leave TEST.NAME empty so Django uses shared-cache
        # in-memory (creation.py:_get_test_db_name)
        return {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

    # On-disk database: both NAME and TEST.NAME must be set, otherwise pytest-django
    # treats an empty TEST.NAME as :memory: (see django/db/backends/sqlite3/creation.py:_get_test_db_name).
    db_path = os.environ.get(
        "TREE_COMMENTS_DB_NAME",
        os.path.join("/tmp", f"tree_comments_perf_{os.getpid()}.sqlite3"),
    )
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": db_path,
            "TEST": {"NAME": db_path},
        }
    }


DATABASES = _build_databases()
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "tree_comments",
    "tests.app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

TREE_COMMENTS_COMMENT_MODEL = "tree_comments.Comment"
