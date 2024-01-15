import threading
import datetime

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

local = threading.local()


def set_user_context(user):
    """
    Stores a Django user context to use when updating (eg. in worker process or unit test)
    """

    local.user = user


def get_user_context():
    """
    Retrieves a previously stored Django user context.
    """

    try:
        user = local.user
        return user

    except AttributeError:
        thread_id = threading.get_ident()
        msg = f"A valid Django user context is required to save this instance. Try setting the user context via set_user_context() (thread_id='{thread_id}')."
        raise ImproperlyConfigured(msg)


class AuditBaseQuerySet(models.query.QuerySet):
    """
    An abstract QuerySet that provides self-updating created & modified fields.
    """

    class Meta:
        abstract = True

    def update(self, *args, **kwargs):

        # see: https://docs.djangoproject.com/en/dev/topics/db/queries/#updating-multiple-objects-at-once
        for item in self:
            item.save()

        super().update(*args, **kwargs)


class AuditedBaseModel(models.Model):
    """
    An abstract Model that provides self-updating created and modified fields.
    Note: these fields are by default not shown in eg. Django Admin.
    """

    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        help_text='Timestamp this instance was created.'
    )
    updated = models.DateTimeField(
        # don't use auto_add; as this will also be set on creation of this instance - see save()
        null=True,
        help_text='Timestamp this instance was last updated.'
    )
    created_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='+',
        null=False,
        db_index=True,
        help_text='Who created this instance'
    )
    updated_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='+',
        null=True,
        db_index=True,
        help_text='Who updated this instance.'
    )

    objects = AuditBaseQuerySet.as_manager()

    # TODO - add soft delete flag and method + manager?
    # see https://sunscrapers.com/blog/building-better-django-models-6-expert-tips

    class Meta:
        abstract = True

        # ordered in reverse-chronological order by default
        ordering = ['-created', '-updated']

    def save(self, *args, **kwargs):

        user = get_user_context()

        # create vs update
        if not self.id:
            self.created_by = user
        else:
            self.updated_by = user
            self.updated = datetime.datetime.now()

        super().save(*args, **kwargs)


class IfcValidationRequest(AuditedBaseModel):
    """
    A model to store and track IFC Validation Requests.
    """

    class Status(models.TextChoices):
        """
        The overall status of an IFC Validation Request.
        """
        PENDING   = 'PENDING', 'Pending'
        INITIATED = 'INITIATED', 'Initiated'
        FAILED    = 'FAILED', 'Failed'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the request (auto-generated)."
    )

    file_name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        verbose_name='file name',
        help_text="Name of the file."
    )

    file = models.FileField(
        null=False,
        help_text="Path of the file."
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        null=False,
        blank=False,
        help_text="Current status of the request."
    )

    status_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for current status."
    )

    class Meta:

        db_table = "ifc_validation_request"
        indexes = [models.Index(fields=["file_name", "status"])]  # only add multi-column indexes here
        verbose_name = "IFC Validation Request"
        verbose_name_plural = "IFC Validation Requests"
        permissions = [
            ("change_status", "Can change status of IFC Validation Request")
        ]

    def __str__(self):

        return f'#{self.id} - {self.file_name}'

    # do not add get_absolute url here, rather add it in a subclass as it's view specific (eg. API vs UI)
    # def get_absolute_url(self):
    #     return reverse("detail", args=[str(self.id)]) # /request/{{id}}

    @property
    def has_final_status(self):

        FINAL_STATUS_LIST = [
            self.Status.FAILED,
            self.Status.COMPLETED
        ]
        return self.status in FINAL_STATUS_LIST

    def mark_as_initiated(self):

        self.status = self.Status.INITIATED
        self.started = datetime.datetime.now()
        self.save()

    def mark_as_completed(self, reason):

        self.status = self.Status.COMPLETED
        self.status_reason = reason
        self.completed = datetime.datetime.now()
        self.save()

    def mark_as_failed(self, reason):

        self.status = self.Status.FAILED
        self.status_reason = reason
        self.completed = datetime.datetime.now()
        self.save()


class IfcValidationTask(AuditedBaseModel):
    """
    A model to store and track IFC Validation Tasks.
    """

    class Type(models.TextChoices):
        """
        The type of an IFC Validation Task.
        """
        SYNTAX                 = 'SYNTAX', 'STEP Physical File Syntax'
        SCHEMA                 = 'SCHEMA', 'IFC Schema (Express language)'
        BSDD                   = 'BSDD', 'Requirements per bSDD Classification'
        PARSE_INFO             = 'INFO', 'Parse Info'
        GHERKIN_RULES_BLOCKERS = 'GHERKIN_BLOCKERS', 'Gherkin Rules - Blockers (TBC)'
        GHERKIN_RULES_IA       = 'GHERKIN_IA', 'Gherkin Rules - Implementer Agreements (IA)'
        GHERKIN_RULES_IP       = 'GHERKIN_IP', 'Gherkin Rules - Informal Propositions (IP)'
        INDUSTRY_PRACTICES     = 'INDUSTRY', 'Industry Practices (TBC)'

    class Status(models.TextChoices):
        """
        The overall status of an IFC Validation Task.
        """
        PENDING        = 'PENDING', 'Pending'
        SKIPPED        = 'SKIPPED', 'Skipped'
        NOT_APPLICABLE = 'N/A', 'Not Applicable'
        INITIATED      = 'INITIATED', 'Initiated'
        FAILED         = 'FAILED', 'Failed'
        COMPLETED      = 'COMPLETED', 'Completed'

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the task (auto-generated)."
    )

    request = models.ForeignKey(
        to=IfcValidationRequest,
        on_delete=models.CASCADE,
        related_name='tasks',
        blank=False,
        null=False,
        db_index=True,
        help_text='What IFC Validation Request this Task belongs to.'
    )

    type = models.CharField(
        max_length=25,
        choices=Type.choices,
        db_index=True,
        null=False,
        blank=False,
        help_text="Type of the task."
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        null=False,
        blank=False,
        help_text="Current status of the task."
    )

    status_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for current status."
    )

    started = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name='started',
        help_text="Timestamp the task was started."
    )

    ended = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name='ended',
        help_text="Timestamp the task was ended."
    )

    class Meta:

        db_table = "ifc_validation_task"
        verbose_name = "IFC Validation Task"
        verbose_name_plural = "IFC Validation Tasks"

    def __str__(self):

        return f'#{self.id} - {self.request.file_name} - {self.type} - {self.created.date()} - {self.status}'

    # do not add get_absolute url here, rather add it in a subclass as it's view specific (eg. API vs UI)
    # def get_absolute_url(self):
    #     return reverse("detail", args=[str(self.id)]) # /request/{{id}}

    @property
    def has_final_status(self):

        FINAL_STATUS_LIST = [
            self.Status.SKIPPED,
            self.Status.FAILED,
            self.Status.NOT_APPLICABLE,
            self.Status.COMPLETED
        ]
        return self.status in FINAL_STATUS_LIST

    @property
    def duration(self):

        if self.started and self.ended:
            return (self.ended - self.started)
        else:
            return None

    def mark_as_initiated(self):

        self.status = self.Status.INITIATED
        self.started = datetime.datetime.now()
        self.save()

    def mark_as_completed(self, reason):

        self.status = self.Status.COMPLETED
        self.status_reason = reason
        self.ended = datetime.datetime.now()
        self.save()

    def mark_as_failed(self, reason):

        self.status = self.Status.FAILED
        self.status_reason = reason
        self.ended = datetime.datetime.now()
        self.save()

    def mark_as_skipped(self, reason):

        self.status = self.Status.SKIPPED
        self.status_reason = reason
        self.save()


class IfcValidationTaskResult(AuditedBaseModel):
    """
    An abstract class for IFC Task Results.
    """

    # TODO
    pass

    class Meta:
        abstract = True


class IfcGherkinTaskResult(IfcValidationTaskResult):
    """
    A model to store and track IFC Gherkin Task Results.
    """

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the task result (auto-generated)."
    )

    request = models.ForeignKey(
        to=IfcValidationRequest,
        on_delete=models.CASCADE,
        related_name='results',
        blank=False,
        null=False,
        db_index=True,
        help_text='What IFC Validation Request this Task belongs to.'
    )

    task = models.ForeignKey(
        to=IfcValidationTask,
        on_delete=models.CASCADE,
        related_name='results',
        blank=False,
        null=False,
        db_index=True,
        help_text='What IFC Validation Task this Result belongs to.'
    )

    feature = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        db_index=True,
        help_text="Name of the Gherkin Feature."
    )

    feature_url = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        db_index=True,
        help_text="Url with definition of the Gherkin Feature."
    )

    step = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        help_text="Step within the Gherkin Feature."
    )

    message = models.TextField(
        null=True,
        blank=True,
        help_text="Output message."
    )

    class Meta:
        db_table = "ifc_gherkin_task_result"
        verbose_name = "IFC Validation Gherkin Task Result"
        verbose_name_plural = "IFC Validation Gherkin Task Results"

    def __str__(self):

        return f'#{self.id} - {self.request.file_name} - {self.feature}'
