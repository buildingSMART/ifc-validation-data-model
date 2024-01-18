import os
from dotenv import load_dotenv

load_dotenv()

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",

    "ifc_validation_models"
]

DB_SQLITE = "sqlite"

DATABASES_ALL = {
    DB_SQLITE: {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "worker_db.sqlite3",
    }
}

DATABASES = {"default": DATABASES_ALL[os.environ.get("TEST_DJANGO_DB", DB_SQLITE)]}
