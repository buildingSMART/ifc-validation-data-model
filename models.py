import os
import threading

from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.contrib.auth.models import User

local = threading.local()

PRIMEMODULO = 1000000000
COPRIMESECRET = int(os.environ.get('COPRIMESECRET', '383446691'))
INVERSE_COPRIME = pow(COPRIMESECRET, -1, mod=PRIMEMODULO)

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


class SoftDeletableModel(models.Model):
    """An abstract base class that provides soft-deletable Models."""
    
    deleted = models.BooleanField(
        null=False,
        default=False,
        db_index=True,
        help_text='Flag to indicate object is deleted'
    )

    def delete(self):        
        """Softly delete the object."""

        self.deleted = True
        self.save()

    def soft_delete(self):

        return self.delete()

    def undo_delete(self):
        """Restore previouly deleted object."""

        self.deleted = False
        self.save()
            
    def hard_delete(self):
        """Remove the object from the database."""

        super().delete()

    class Meta:
        abstract=True


class TimestampedBaseQuerySet(models.query.QuerySet):
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


class TimestampedBaseModel(models.Model):
    """
    An abstract Model that provides self-updating created and updated fields.
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
        blank=True,
        help_text='Timestamp this instance was last updated.'
    )

    objects = TimestampedBaseQuerySet.as_manager()

    class Meta:
        abstract = True

        # ordered in reverse-chronological order by default
        ordering = ['-created', '-updated']

    def save(self, *args, **kwargs):

        # create vs update
        if not self.id:
            pass
        else:
            self.updated = timezone.now()

        super().save(*args, **kwargs)


class IdObfuscator:
    @property
    def public_id(self):
        return self.to_public_id(self.id) # type(self).__name__[0].lower() + str(self.id * COPRIMESECRET % PRIMEMODULO)
    
    @classmethod
    def to_public_id(cls, priv_id, override_cls=None):
        return id_prefix_mapping[override_cls or cls] + str(priv_id * COPRIMESECRET % PRIMEMODULO)
    
    @staticmethod
    def to_private_id(pub_id):
        return int(pub_id[1:]) * INVERSE_COPRIME % PRIMEMODULO


class AuditBaseQuerySet(TimestampedBaseQuerySet):
    """
    An abstract QuerySet that provides self-updating created by & updated by fields.
    """

    class Meta:
        abstract = True

    def update(self, *args, **kwargs):

        # see: https://docs.djangoproject.com/en/dev/topics/db/queries/#updating-multiple-objects-at-once
        for item in self:
            item.save()

        super().update(*args, **kwargs)


class AuditedBaseModel(TimestampedBaseModel):
    """
    An abstract Model that provides self-updating created/created by and updated/updated by fields.
    Note: these fields are by default not shown in eg. Django Admin.
    """

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
        blank=True,
        db_index=True,
        help_text='Who updated this instance.'
    )

    objects = AuditBaseQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):

        user = get_user_context()

        # create vs update
        if not self.id:
            self.created_by = user
        else:
            self.updated_by = user
            self.updated = timezone.now()

        super().save(*args, **kwargs)


class Company(TimestampedBaseModel):
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

    def __str__(self):

        return f'{self.name}'


class AuthoringTool(TimestampedBaseModel):
    """
    A model to store and track Authoring Tool information.
    """

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Authoring Tool (auto-generated)."
    )

    company = models.ForeignKey(
        to=Company,
        on_delete=models.SET_NULL,
        related_name='company',
        null=True,
        blank=True,
        db_index=True,
        help_text='What Company this Authoring Tool belongs to (optional).'
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

    def __str__(self):

        return f'{self.full_name}'.strip()

    @property
    def full_name(self):
        """
        Returns full name of the Authoring Tool, concatenating company, name and version (where available).
        An Authoring Tool has at least a name; company and version are optional.
        """

        company_name = self.company.name if self.company else ''
        full_name_without_version = f'{company_name} {self.name}'.strip()

        if self.version is None:
            return full_name_without_version
        else:
            return f'{full_name_without_version} - {self.version}'.strip()

    def find_by_full_name(full_name):
        """
        Look for the Authoring Tool(s) within the Company/Authoring Tool hierarchy.
        Fallback to matching records without versions, dashes and/or company.
        """

        def full_name_without_version_dash(full_name):
            without_version = full_name.rpartition(' - ')  # last dash only
            return '{} {}'.format(without_version[0].strip(), without_version[2].strip())

        def matches(obj, full_name):
            return (full_name == obj.full_name or full_name == full_name_without_version_dash(obj.full_name))

        found = [obj for obj in AuthoringTool.objects.all() if matches(obj, full_name)] # cannot use a property to filter...

        if found is None or len(found) == 0:
            return None
        elif len(found) == 1:
            return found[0]
        else:
            return found


class Model(TimestampedBaseModel, IdObfuscator):
    """
    A model to store and track Models.
    """

    class Status(models.TextChoices):
        """
        The overall status of an individual Model component.
        """
        VALID          = 'v', 'Valid'
        INVALID        = 'i', 'Invalid'
        NOT_VALIDATED  = 'n', 'Not Validated'
        WARNING        = 'w', 'Warning'
        NOT_APPLICABLE = '-', 'Not Applicable'

    class License(models.TextChoices):
        """
        The license of a Model.
        """
        UNKNOWN       = 'UNKNOWN', 'Unknown'
        PRIVATE       = 'PRIVATE', 'Private'
        CC            = 'CC',      'CC'
        MIT           = 'MIT',     'MIT'
        GPL           = 'GPL',     'GPL'
        LGPL          = 'LGPL',    'LGPL'

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Model (auto-generated)."
    )

    produced_by = models.ForeignKey(
        to=AuthoringTool,
        on_delete=models.SET_NULL,
        related_name='models',
        null=True,
        blank=True,
        db_index=True,
        help_text='What tool was used to create this Model.'
    )

    date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp the Model was created."
    )

    details = models.TextField(
        null=True,
        blank=True,
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

    license = models.CharField(
        max_length=7,
        choices=License.choices,
        default=License.UNKNOWN,
        db_index=True,
        null=False,
        blank=False,
        help_text="License of the Model."
    )

    mvd = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="MVD Classification of the Model."
    )

    number_of_elements = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of elements within the Model."        
    )

    number_of_geometries = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of geometries within the Model."        
    )

    number_of_properties = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of properties within the Model."        
    )

    schema = models.CharField(
        max_length=25,
        null=True,
        blank=True,
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

    status_prereq = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Prerequisites Validation."
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
        blank=True,
        help_text="Properties of the Model."
    )

    class Meta:
        db_table = "ifc_model"
        verbose_name = "Model"
        verbose_name_plural = "Models"

    def __str__(self):

        return f'#{self.id} - {self.created.date()} - {self.file_name}'

    def reset_status(self):

        self.status_bsdd = Model.Status.NOT_VALIDATED
        self.status_ia = Model.Status.NOT_VALIDATED
        self.status_ip = Model.Status.NOT_VALIDATED
        self.status_ids = Model.Status.NOT_VALIDATED
        self.status_mvd = Model.Status.NOT_VALIDATED
        self.status_schema = Model.Status.NOT_VALIDATED
        self.status_syntax = Model.Status.NOT_VALIDATED
        self.status_industry_practices = Model.Status.NOT_VALIDATED
        self.status_prereq = Model.Status.NOT_VALIDATED
        self.save()


class ModelInstance(TimestampedBaseModel, IdObfuscator):
    """
    A model to store and track Model Instances.
    """

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Model Instance (auto-generated)."
    )

    model = models.ForeignKey(
        to=Model,
        on_delete=models.CASCADE,
        related_name='instances',
        blank=False,
        null=False,
        db_index=True,
        help_text='What Model this Model Instance is a part of.'
    )

    stepfile_id = models.PositiveBigIntegerField(
        null=False,
        blank=False,
        db_index=True,
        help_text='id assigned within the Step File (eg. #11)'
    )

    ifc_type = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        db_index=True,
        help_text="IFC Type."
    )

    fields = models.JSONField(
        null=True,
        blank=True,
        help_text="Fields of the Instance."
    )

    class Meta:
        db_table = "ifc_model_instance"
        verbose_name = "Model Instance"
        verbose_name_plural = "Model Instances"

    def __str__(self):

        return f'#{self.id} - {self.ifc_type} - {self.model.file_name}'


class ValidationRequest(AuditedBaseModel, SoftDeletableModel, IdObfuscator):
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

    size = models.PositiveIntegerField(
        null=False,
        help_text="Size of the file (bytes)"
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

    started = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name='started',
        help_text="Timestamp the Validation Request was started."
    )

    completed = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name='completed',
        help_text="Timestamp the Validation Request completed."
    )

    progress = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Overall progress (%) of the Validation Request."
    )

    model = models.OneToOneField(
        to=Model,
        on_delete=models.CASCADE,
        related_name='request',
        null=True,
        db_index=True,
        help_text='What Model is created based on this Validation Request.'
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

        return f'#{self.id} - {self.created.date()} - {self.file_name}'

    @property
    def has_final_status(self):

        FINAL_STATUS_LIST = [
            self.Status.FAILED,
            self.Status.COMPLETED
        ]
        return self.status in FINAL_STATUS_LIST

    @property
    def duration(self):

        if self.started and self.completed:
            return (self.completed - self.started)
        elif self.started:
            return (timezone.now() - self.started)
        else:
            return None
        
    @property
    def model_public_id(self):
        return IdObfuscator.to_public_id(self.model_id, override_cls=Model) if self.model_id else None

    def mark_as_initiated(self, reason=None):

        self.status = self.Status.INITIATED
        self.status_reason = reason
        self.started = timezone.now()
        self.completed = None
        self.progress = 0
        self.save()

    def mark_as_completed(self, reason=None):

        self.status = self.Status.COMPLETED
        self.status_reason = reason
        self.completed = timezone.now()
        self.progress = 100
        self.save()

    def mark_as_failed(self, reason=None):

        self.status = self.Status.FAILED
        self.status_reason = reason
        self.completed = timezone.now()
        self.save()

    def mark_as_warning(self, reason=None):

        self.status = self.Status.FAILED
        self.status_reason = reason
        self.completed = timezone.now()
        self.progress = 100
        self.save()

    def mark_as_pending(self, reason=None):

        self.status = self.Status.PENDING
        self.status_reason = reason
        self.progress = 0
        self.started = None
        self.ended = None
        self.save()


class ValidationTask(TimestampedBaseModel, IdObfuscator):
    """
    A model to store and track Validation Tasks.
    """

    class Type(models.TextChoices):
        """
        The type of an Validation Task.
        """
        SYNTAX              = 'SYNTAX', 'STEP Physical File Syntax'
        SCHEMA              = 'SCHEMA', 'Schema (EXPRESS language)'
        MVD                 = 'MVD', 'Model View Definitions'
        BSDD                = 'BSDD', 'bSDD Compliance'
        PARSE_INFO          = 'INFO', 'Parse Info'
        PREREQUISITES       = 'PREREQ', 'Prerequisites'
        NORMATIVE_IA        = 'NORMATIVE_IA', 'Implementer Agreements (IA)'
        NORMATIVE_IP        = 'NORMATIVE_IP', 'Informal Propositions (IP)'
        INDUSTRY_PRACTICES  = 'INDUSTRY', 'Industry Practices'
        INSTANCE_COMPLETION = 'INST_COMPLETION', 'Instance Completion'

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
        to=ValidationRequest,
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
        blank=True,
        db_index=True,
        help_text="Overall progress (%) of the Validation Task."
    )

    process_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Process id of subprocess executing the Validation Task."
    )

    process_cmd = models.TextField(
        null=True,
        blank=True,
        help_text="Command and arguments used to launch the subprocess executing the Validation Task."
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
        elif self.started:
            return (timezone.now() - self.started)
        else:
            return None
        
    @property
    def request_public_id(self):
        return IdObfuscator.to_public_id(self.request_id, override_cls=ValidationRequest) if self.request_id else None

    def mark_as_initiated(self):

        self.status = self.Status.INITIATED
        self.started = timezone.now()
        self.ended = None
        self.progress = 0
        self.save()

    def mark_as_completed(self, reason=None):

        self.status = self.Status.COMPLETED
        self.status_reason = reason
        self.ended = timezone.now()
        self.progress = 100
        self.save()

    def mark_as_failed(self, reason=None):

        self.status = self.Status.FAILED
        self.status_reason = reason
        self.ended = timezone.now()
        self.save()

    def mark_as_skipped(self, reason=None):

        self.status = self.Status.SKIPPED
        self.status_reason = reason
        self.save()

    def set_process_details(self, id, cmd):

        self.process_id = id
        self.process_cmd = cmd
        self.save()

    def determine_aggregate_status(self):
        """
        Aggregates Severity of all Outcomes into one final Status value.
        """
        
        agg_status = None
        for outcome in self.outcomes.iterator():
            if outcome.severity == ValidationOutcome.OutcomeSeverity.NOT_APPLICABLE and agg_status is None:
                agg_status = Model.Status.NOT_APPLICABLE
            elif outcome.severity == ValidationOutcome.OutcomeSeverity.EXECUTED and agg_status in [None, Model.Status.NOT_APPLICABLE]:
                agg_status = Model.Status.VALID
            elif outcome.severity == ValidationOutcome.OutcomeSeverity.PASSED and agg_status in [None, Model.Status.NOT_APPLICABLE]:
                agg_status = Model.Status.VALID
            elif outcome.severity == ValidationOutcome.OutcomeSeverity.WARNING:
                agg_status = Model.Status.WARNING
            elif outcome.severity == ValidationOutcome.OutcomeSeverity.ERROR:
                agg_status = Model.Status.INVALID
                break # can't get any worse...

        # assume valid if no outcomes - TODO: is this correct?
        if agg_status is None:
            agg_status = Model.Status.VALID

        return agg_status


class ValidationOutcome(TimestampedBaseModel, IdObfuscator):
    """
    A model to store and track Validation Outcome instances.
    """

    class OutcomeSeverity(models.IntegerChoices):
        """
        The severity of an Validation Outcome.
        """
        EXECUTED               = 1, 'Executed'
        PASSED                 = 2, 'Passed'
        WARNING                = 3, 'Warning'
        ERROR                  = 4, 'Error'
        NOT_APPLICABLE         = 0, 'N/A'

    class ValidationOutcomeCode(models.TextChoices):
        """
        A code representing a Validation Outcome.
        """
        PASSED                                 = "P00010", "Passed"
        NOT_APPLICABLE                         = "N00010", "Not Applicable"

        # errors
        SYNTAX_ERROR                           = "E00001", "Syntax Error"
        SCHEMA_ERROR                           = "E00002", "Schema Error"
        TYPE_ERROR                             = "E00010", "Type Error"
        VALUE_ERROR                            = "E00020", "Value Error"
        GEOMETRY_ERROR                         = "E00030", "Geometry Error"
        CARDINALITY_ERROR                      = "E00040", "Cardinality Error"
        DUPLICATE_ERROR                        = "E00050", "Duplicate Error"
        PLACEMENT_ERROR                        = "E00060", "Placement Error"
        UNITS_ERROR                            = "E00070", "Units Error"
        QUANTITY_ERROR                         = "E00080", "Quantity Error"
        ENUMERATED_VALUE_ERROR                 = "E00090", "Enumerated Value Error"
        RELATIONSHIP_ERROR                     = "E00100", "Relationship Error"
        NAMING_ERROR                           = "E00110", "Naming Error"
        REFERENCE_ERROR                        = "E00120", "Reference Error"
        RESOURCE_ERROR                         = "E00130", "Resource Error"
        DEPRECATION_ERROR                      = "E00140", "Deprecation Error"
        SHAPE_REPRESENTATION_ERROR             = "E00150", "Shape Representation Error"
        INSTANCE_STRUCTURE_ERROR               = "E00160", "Instance Structure Error"

        # warnings
        ALIGNMENT_CONTAINS_BUSINESS_LOGIC_ONLY = "W00010", "Alignment Contains Business Logic Only"
        ALIGNMENT_CONTAINS_GEOMETRY_ONLY       = "W00020", "Alignment Contains Geometry Only"
        WARNING                                = "W00030", "Warning"
        
        EXECUTED                               = "X00040", "Executed"

    _inst = None # temp internal-use attribute to store the instance of the model being validated for further use in behave statements

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Validation Outcome (auto-generated)."
    )

    instance = models.ForeignKey(
        to=ModelInstance,
        on_delete=models.CASCADE,
        related_name='outcomes',
        null=True,
        db_index=True,
        help_text='What Model Instance this Outcome is applicable to (optional).'
    )

    validation_task = models.ForeignKey(
        to=ValidationTask,
        on_delete=models.CASCADE,
        related_name='outcomes',
        blank=False,
        null=False,
        db_index=True,
        help_text='What Validation Task this Outcome belongs to.'
    )

    feature = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="Name of the Gherkin Feature (optional)."
    )

    feature_version = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Version number of the Gherkin Feature (optional)."
    )

    severity = models.PositiveSmallIntegerField(
        choices=OutcomeSeverity.choices,
        default=OutcomeSeverity.NOT_APPLICABLE,
        db_index=True,
        null=False,
        blank=False,
        help_text="Severity of the Validation Outcome."
    )

    outcome_code = models.CharField(
        max_length=10,
        choices=ValidationOutcomeCode.choices,
        default=ValidationOutcomeCode.NOT_APPLICABLE,
        help_text="Code representing the Validation Outcome."
    )

    expected = models.JSONField(
        null=True,
        blank=True,
        help_text="Expected value(s) for the Validation Outcome."
    )

    observed = models.JSONField(
        null=True,
        blank=True,
        help_text="Observed value(s) for the Validation Outcome."
    )

    class Meta:
        db_table = "ifc_validation_outcome"
        verbose_name = "Validation Outcome"
        verbose_name_plural = "Validation Outcomes"
        indexes = [
            models.Index(fields=["feature", "feature_version"]),
            models.Index(fields=["feature", "feature_version", "severity"])
        ]

    def __str__(self):
        members = {
            'Feature': (self.feature or '').split('-')[0].strip(),
            'Outcome': self.outcome_code,
            'Severity': repr(self.severity).split('.')[-1],
            'ifc_instance_id': self.instance_id,
            'Expected': self.expected,
            'Observed': self.observed
        }
        return f' '.join(f'{k}={v}' for k, v in members.items() if v)
    
    @property
    def instance_public_id(self):
        return IdObfuscator.to_public_id(self.instance_id, override_cls=ModelInstance) if self.instance_id else None

    @property
    def validation_task_public_id(self):
        return IdObfuscator.to_public_id(self.validation_task_id, override_cls=ValidationTask) if self.validation_task_id else None

    @property
    def inst(self):
        return self._inst

    @inst.setter
    def inst(self, value):
        self._inst = value

    def determine_severity(self):
        
        match self.name[0]:
            case 'X':
                return self.OutcomeSeverity.EXECUTED
            case 'P':
                return self.OutcomeSeverity.PASSED
            case 'N':
                return self.OutcomeSeverity.NOT_APPLICABLE
            case 'W':
                return self.OutcomeSeverity.WARNING
            case 'E':
                return self.OutcomeSeverity.ERROR
            case _:
                raise ValueError(f"Outcome code '{self.name}' not recognized")


id_prefix_mapping = {
    Model: 'm',
    ModelInstance: 'i',
    ValidationRequest: 'r',
    ValidationTask: 't',
    ValidationOutcome: 'o',
    User: 'u',
}
