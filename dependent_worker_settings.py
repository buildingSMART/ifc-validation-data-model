import os
from dotenv import load_dotenv

load_dotenv()

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",

    "ifc_validation_models"
]

from core.settings import DATABASES
