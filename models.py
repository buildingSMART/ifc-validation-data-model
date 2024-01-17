import threading

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from deprecated import deprecated

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
            self.updated = timezone.now()

        super().save(*args, **kwargs)


class IfcCompany(AuditedBaseModel):
    """
    A model to store and track Company information.
    """

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Company (auto-generated)."
    )

    name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        unique=True,
        help_text="Name of the Company."
    )

    class Meta:

        db_table = "ifc_company"
        verbose_name = "Company"
        verbose_name_plural = "Companies"


class IfcAuthoringTool(AuditedBaseModel):
    """
    A model to store and track Authoring Tool information.
    """

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Authoring Tool (auto-generated)."
    )

    company = models.ForeignKey(
        to=IfcCompany,
        on_delete=models.CASCADE,
        related_name='company',
        blank=False,
        null=False,
        db_index=True,
        help_text='What Company this Authoring Tool belongs to.'
    )

    name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        help_text="Name of the Authoring Tool."
    )

    version = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Alphanumeric version of the Authoring Tool (eg. '1.0-alpha')."
    )

    class Meta:

        db_table = "ifc_authoring_tool"
        verbose_name = "Authoring Tool"
        verbose_name_plural = "Authoring Tools"

        constraints = [
            models.UniqueConstraint(fields=['name', 'version'], name='unique_name_version')
        ]


class IfcModel(AuditedBaseModel):
    """
    A model to store and track Models.
    """

    class Status(models.TextChoices):
        """
        The overall status of a Model.
        """
        VALID         = 'v', 'Valid'
        INVALID       = 'i', 'Invalid'
        NOT_VALIDATED = 'n', 'Not Validated'

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Model (auto-generated)."
    )

    produced_by = models.ForeignKey(
        to=IfcAuthoringTool,
        on_delete=models.RESTRICT,
        related_name='models',
        null=True,
        db_index=True,
        help_text='What tool was used to create this Model.'
    )

    date = models.DateTimeField(
        null=True,
        blank=False,
        help_text="Timestamp the Model was created."
    )

    details = models.TextField(
        null=True,
        blank=False,
        help_text="Details of the Model."
    )

    file_name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        help_text="Original name of the file that contained this Model."
    )

    file = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        help_text="File name as it stored."
    )

    size = models.PositiveIntegerField(
        null=False,
        help_text="Size of the model (bytes)"
    )
    
    # TODO - not sure what this field is used for
    hours = models.PositiveIntegerField(
        null=True,
        help_text="TBC (???)"        
    )

    license = models.CharField(
        max_length=7,
        null=True,
        blank=False,
        help_text="License of the Model."
    )

    mvd = models.CharField(
        max_length=25,
        null=True,
        blank=False,
        help_text="MVD Classification of the Model."
    )

    number_of_elements = models.PositiveIntegerField(
        null=True,
        help_text="Number of elements within the Model."        
    )

    number_of_geometries = models.PositiveSmallIntegerField(
        null=True,
        help_text="Number of geometries within the Model."        
    )

    number_of_properties = models.PositiveSmallIntegerField(
        null=True,
        help_text="Number of properties within the Model."        
    )

    schema = models.CharField(
        max_length=25,
        null=True,
        blank=False,
        help_text="Schema of the Model."
    )

    status_bsdd = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the bSDD Validation."
    )

    status_ia = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the IA Validation."
    )

    status_ip = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the IP Validation."
    )

    status_ids = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the IDS Validation."
    )

    status_mvd = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the MVD Validation."
    )

    status_schema = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Schema Validation."
    )

    status_syntax = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Syntax Validation."
    )

    status_industry_practices = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Industry Practices Validation."
    )

    uploaded_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='models',
        null=False,
        db_index=True,
        help_text='Who uploaded this Model.'
    )

    properties = models.JSONField(
        null=True,
        help_text="Properties of the Model."
    )

    class Meta:
        db_table = "ifc_model"
        verbose_name = "Model"
        verbose_name_plural = "Models"

    def __str__(self):

        return f'#{self.id} - {self.created} - {self.type}'


class IfcModelInstance(AuditedBaseModel):
    """
    A model to store and track Model Instances.
    """

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Model Instance (auto-generated)."
    )

    model = models.ForeignKey(
        to=IfcModel,
        on_delete=models.CASCADE,
        related_name='instances',
        blank=False,
        null=False,
        db_index=True,
        help_text='What Model this Model Instance is a part of.'
    )

    stepfile_id = models.PositiveSmallIntegerField(
        null=False,
        blank=False,
        db_index=True,
        help_text='TBC (???)'
    )

    ifc_type = models.CharField(
        max_length=25,
        null=False,
        blank=False,
        db_index=True,
        help_text="IFC Type."
    )

    fields = models.JSONField(
        null=True,
        help_text="Fields of the Instance."
    )

    class Meta:
        db_table = "ifc_model_instance"
        verbose_name = "Model Instance"
        verbose_name_plural = "Model Instances"

    def __str__(self):

        return f'#{self.id} - {self.ifc_type} - {self.model.file_name}'


class IfcValidationRequest(AuditedBaseModel):
    """
    A model to store and track Validation Requests.
    """

    class Status(models.TextChoices):
        """
        The overall status of an Validation Request.
        """
        PENDING   = 'PENDING', 'Pending'
        INITIATED = 'INITIATED', 'Initiated'
        FAILED    = 'FAILED', 'Failed'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Validation Request (auto-generated)."
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
        help_text="Current status of the Validation Request."
    )

    status_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for current status."
    )

    progress = models.PositiveSmallIntegerField(
        null=True,
        blank=False,
        db_index=True,
        help_text="Overall progress (%) of the Validation Request."
    )

    class Meta:

        db_table = "ifc_validation_request"
        indexes = [models.Index(fields=["file_name", "status"])]  # only add multi-column indexes here
        verbose_name = "Validation Request"
        verbose_name_plural = "Validation Requests"
        permissions = [
            ("change_status", "Can change status of Validation Request")
        ]

    def __str__(self):

        return f'#{self.id} - {self.file_name} - {self.created.date()} - {self.status}'

    @property
    def has_final_status(self):

        FINAL_STATUS_LIST = [
            self.Status.FAILED,
            self.Status.COMPLETED
        ]
        return self.status in FINAL_STATUS_LIST

    def mark_as_initiated(self):

        self.status = self.Status.INITIATED
        self.started = timezone.now()
        self.progress = 0
        self.save()

    def mark_as_completed(self, reason):

        self.status = self.Status.COMPLETED
        self.status_reason = reason
        self.completed = timezone.now()
        self.progress = 100
        self.save()

    def mark_as_failed(self, reason):

        self.status = self.Status.FAILED
        self.status_reason = reason
        self.completed = timezone.now()
        self.save()


class IfcValidationTask(AuditedBaseModel):
    """
    A model to store and track Validation Tasks.
    """

    class Type(models.TextChoices):
        """
        The type of an Validation Task.
        """
        SYNTAX              = 'SYNTAX', 'STEP Physical File Syntax'
        SCHEMA              = 'SCHEMA', 'Schema (Express language)'
        MVD                 = 'MVD', 'Model View Definitions'
        BSDD                = 'BSDD', 'Requirements per bSDD Classification'
        PARSE_INFO          = 'INFO', 'Parse Info'
        PREREQUISITES       = 'PREREQ', 'Prerequisites'
        NORMATIVE_IA        = 'NORMATIVE_IA', 'Normative Rules - Implementer Agreements (IA)'
        NORMATIVE_IP        = 'NORMATIVE_IP', 'Normative Rules - Informal Propositions (IP)'
        INDUSTRY_PRACTICES  = 'INDUSTRY', 'Industry Practices (TBC)'

    class Status(models.TextChoices):
        """
        The overall status of a Validation Task.
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
        help_text='What Validation Request this Validation Task belongs to.'
    )

    type = models.CharField(
        max_length=25,
        choices=Type.choices,
        db_index=True,
        null=False,
        blank=False,
        help_text="Type of the Validation Task."
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        null=False,
        blank=False,
        help_text="Current status of the Validation Task."
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
        help_text="Timestamp the Validation Task was started."
    )

    ended = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name='ended',
        help_text="Timestamp the Validation Task ended."
    )

    progress = models.PositiveSmallIntegerField(
        null=True,
        blank=False,
        db_index=True,
        help_text="Overall progress (%) of the Validation Task."
    )

    class Meta:

        db_table = "ifc_validation_task"
        verbose_name = "Validation Task"
        verbose_name_plural = "Validation Tasks"

    def __str__(self):

        return f'#{self.id} - {self.request.file_name} - {self.type} - {self.created.date()} - {self.status}'


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
        self.started = timezone.now()
        self.progress = 0
        self.save()

    def mark_as_completed(self, reason):

        self.status = self.Status.COMPLETED
        self.status_reason = reason
        self.ended = timezone.now()
        self.progress = 100
        self.save()

    def mark_as_failed(self, reason):

        self.status = self.Status.FAILED
        self.status_reason = reason
        self.ended = timezone.now()
        self.save()

    def mark_as_skipped(self, reason):

        self.status = self.Status.SKIPPED
        self.status_reason = reason
        self.save()


class IfcValidationOutcome(AuditedBaseModel):
    """
    A model to store and track Validation Outcome instances.
    """

    class OutcomeSeverity(models.TextChoices):
        """
        The severity of an Validation Outcome.
        """
        EXECUTED               = 1, 'Executed'
        PASSED                 = 2, 'Passed'
        WARNING                = 3, 'Warning'
        ERROR                  = 4, 'Error'
        NOT_APPLICABLE         = 0, 'N/A'

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the validation outcome (auto-generated)."
    )

    instance = models.ForeignKey(
        to=IfcModel,
        on_delete=models.CASCADE,
        related_name='outcomes',
        blank=False,
        null=False,
        db_index=True,
        help_text='What Model Instance this Outcome is applicable to.'
    )

    validation_task = models.ForeignKey(
        to=IfcValidationTask,
        on_delete=models.CASCADE,
        related_name='outcomes',
        blank=False,
        null=False,
        db_index=True,
        help_text='What Validation Task this Outcome belongs to.'
    )

    feature = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        help_text="Name of the Gherkin Feature."
    )

    feature_version = models.PositiveSmallIntegerField(
        null=False,
        blank=False,
        db_index=True,
        help_text="Version number of the Gherkin Feature."
    )

    code = models.CharField(
        max_length=6,
        null=False,
        blank=False,
        db_index=True,
        help_text="Name of the Gherkin Feature."
    )

    severity = models.PositiveSmallIntegerField(
        choices=OutcomeSeverity.choices,
        default=OutcomeSeverity.NOT_APPLICABLE,
        db_index=True,
        null=False,
        blank=False,
        help_text="Severity of the Validation Outcome."
    )

    expected = models.JSONField(
        null=True,
        blank=False,
        help_text="Expected value(s) for the Validation Outcome."
    )

    observed = models.JSONField(
        null=True,
        blank=False,
        help_text="Observed value(s) for the Validation Outcome."
    )

    class Meta:
        db_table = "ifc_validation_outcome"
        verbose_name = "Validation Outcome"
        verbose_name_plural = "Validation Outcomes"
        indexes = [
            models.Index(fields=["code", "feature_version"]),
            models.Index(fields=["code", "feature_version", "severity"])
        ]

    def __str__(self):

        return f'#{self.id} - {self.feature} - v{self.feature_version} - {self.severity}'


@deprecated("Use IfcValidationOutcome instead.")
class IfcValidationTaskResult(AuditedBaseModel):
    """
    An abstract class for Task Results.
    """

    # TODO
    pass

    class Meta:
        abstract = True


@deprecated("Use IfcValidationOutcome instead.")
class IfcGherkinTaskResult(IfcValidationTaskResult):
    """
    A model to store and track Gherkin Task Results.
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
        help_text='What Validation Request this Task belongs to.'
    )

    task = models.ForeignKey(
        to=IfcValidationTask,
        on_delete=models.CASCADE,
        related_name='results',
        blank=False,
        null=False,
        db_index=True,
        help_text='What Validation Task this Result belongs to.'
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
        verbose_name = "Validation Gherkin Task Result"
        verbose_name_plural = "Validation Gherkin Task Results"

    def __str__(self):

        return f'#{self.id} - {self.request.file_name} - {self.feature}'
