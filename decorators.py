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


# instructs a function to require a full table lockß
def requires_django_exclusive_table_lock(model, lock = 'ACCESS EXCLUSIVE'):
    """
    Decorator for PostgreSQL's table-level lock functionality 
    
    example:
        @transaction.commit_on_success
        @requires_django_exclusive_table_lock(MyModel)
        def myview(request)
            ...
        
    see:
        Original source code:
            https://www.caktusgroup.com/blog/2009/05/26/explicit-table-locking-with-postgresql-and-django/
        PostgreSQL's LOCK Documentation:
            https://www.postgresql.org/docs/9.4/static/explicit-locking.html
    """
    def require_lock_decorator(view_func):
        def wrapper(*args, **kwargs):
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute(
                'LOCK TABLE %s IN %s MODE' % (model._meta.db_table, lock)
            )
            return view_func(*args, **kwargs)
        return wrapper
    
    return require_lock_decorator