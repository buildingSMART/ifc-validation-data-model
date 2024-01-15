import functools
import logging

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

from apps.ifc_validation_models.models import set_user_context  # TODO: for now needs to be absolute!
from .settings import DJANGO_DB_USER_CONTEXT

logger = logging.getLogger()


# to make updates to Django DB, we need a Django user context
def set_django_system_user_context():

    """
    Retrieves and sets the Django user context.
    Configured via settings.DJANGO_DB_USER_CONTEXT, default is 'SYSTEM'.
    """

    try:
        user = User.objects.get(username=DJANGO_DB_USER_CONTEXT)
        logger.debug(f'User {DJANGO_DB_USER_CONTEXT} has id={user.pk} and is_active={user.is_active}.')

        if not user.is_active:
            msg = f"Configuration for DJANGO_DB_USER_CONTEXT is invalid: Django user '{DJANGO_DB_USER_CONTEXT}' is not active."
            raise ImproperlyConfigured(msg)

        set_user_context(user)

    except User.DoesNotExist:
        msg = f"Configuration for DJANGO_DB_USER_CONTEXT is invalid: Django user '{DJANGO_DB_USER_CONTEXT}' does not exist."
        raise ImproperlyConfigured(msg)

    except Exception as err:
        msg = f"Failed to set Django user context: {err}"
        logger.error(msg, exc_info=err)
        raise


# instructs a function to require a valid Django user context
def requires_django_user_context(func):

    """
    Decorator to instruct a function to require a valid Django user context.
    Configured via core.settings.DJANGO_DB_USER_CONTEXT, default is 'SYSTEM'.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        set_django_system_user_context()

        result = func(*args, **kwargs)
        return result

    return wrapper
