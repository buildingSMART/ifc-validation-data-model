import os
from dotenv import load_dotenv

from django.core.exceptions import ImproperlyConfigured

load_dotenv()

# to update records in Django DB, we need a Django user context
DJANGO_DB_USER_CONTEXT = os.environ.get("DJANGO_DB_USER_CONTEXT", "SYSTEM")

# timeout for each subprocess
TASK_TIMEOUT_LIMIT = float(os.environ.get("TASK_TIMEOUT_LIMIT", 9 * 60))  # 9 min

# location where files are physically stored
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/files_storage')
try:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
except Exception as err:
    msg = "Configuration for MEDIA_ROOT is invalid: '{}' does not exist and could not be created ({})."
    raise ImproperlyConfigured(msg.format(MEDIA_ROOT, err))
