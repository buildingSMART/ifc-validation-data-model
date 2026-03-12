from dataclasses import dataclass
from enum import Enum
import functools
import operator
import os
import threading

from django.db import models
from django.db.models import Q, QuerySet, TextField, Case, When, Value, IntegerField, CharField, Max
from django.db.models.functions import Cast, Coalesce
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

local = threading.local()

PRIMEMODULO = 1000000000
COPRIMESECRET = int(os.environ.get("COPRIMESECRET", "383446691"))
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


class SanitizedCharField(models.CharField):
    """
    A CharField that sanitizes input by replacing null characters.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is not None:
            value = value.replace('\x00', '')
        return value


class SoftDeletableModel(models.Model):
    """An abstract base class that provides soft-deletable Models."""

    deleted = models.BooleanField(
        null=False,
        default=False,
        db_index=True,
        help_text="Flag to indicate object is deleted",
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
        abstract = True


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
        help_text="Timestamp this instance was last updated.",
    )

    objects = TimestampedBaseQuerySet.as_manager()

    class Meta:
        abstract = True

        # ordered in reverse-chronological order by default
        ordering = ["-created", "-updated"]

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
        return self.to_public_id(
            self.id
        )  # type(self).__name__[0].lower() + str(self.id * COPRIMESECRET % PRIMEMODULO)

    @classmethod
    def to_public_id(cls, priv_id, override_cls=None):
        return id_prefix_mapping[override_cls or cls] + str(
            priv_id * COPRIMESECRET % PRIMEMODULO
        )

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
        related_name="+",
        null=False,
        db_index=True,
        help_text="Who created this instance",
    )

    updated_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="+",
        null=True,
        blank=True,
        db_index=True,
        help_text="Who updated this instance.",
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
        primary_key=True, help_text="Identifier of the Company (auto-generated)."
    )

    name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        unique=True,
        help_text="Name of the Company.",
    )

    legal_name = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        unique=False,
        help_text="Legal name of the Company (optional).",
    )

    email_address_pattern = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        unique=True,
        help_text="Email address pattern(s) of the Company (optional).",
    )

    class Meta:

        db_table = "ifc_company"
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):

        return f"{self.name}"

    def find_users_by_email_pattern(self, only_new=False):

        if self.email_address_pattern:
            matching_users = User.objects.filter(
                email__iregex=self.email_address_pattern
            )
            if only_new:
                matching_users = matching_users.exclude(
                    useradditionalinfo__company=self
                )
            return matching_users if matching_users.exists() else None

        return None


class UserAdditionalInfo(AuditedBaseModel):
    """
    A model to store and track additional User fields.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        help_text="What User this additional info belongs to",
    )

    is_vendor = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether this user belongs to an Authoring Tool vendor (optional)",
    )

    is_vendor_self_declared = models.BooleanField(
        null=True,
        blank=True,
        verbose_name=("is vendor (self declared)"),
        help_text="Whether this user has self-declared an affiliation with an Authoring Tool vendor (optional)",
    )

    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="What Company the User belongs to (optional)",
    )

    class Meta:

        db_table = "ifc_user_additional_info"
        verbose_name = "User Additional Info"
        verbose_name_plural = "User Additional Info"

    def find_company_by_email_pattern(self):

        if self.email:

            companies = Company.objects.filter(email_address_pattern__isnull=False)
            if companies.exists():
                for company in companies:
                    user = User.objects.filter(
                        id=self.id, email__iregex=company.email_address_pattern
                    ).first()
                    if user:
                        return company

        return None

    def find_user_by_username(username):

        return User.objects.filter(username__iexact=username).first()

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
        related_name="company",
        null=True,
        blank=True,
        db_index=True,
        help_text="What Company this Authoring Tool belongs to (optional).",
    )

    name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        help_text="Name of the Authoring Tool.",
    )

    version = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="Alphanumeric version of the Authoring Tool (eg. '1.0-alpha').",
    )

    class Meta:

        db_table = "ifc_authoring_tool"
        verbose_name = "Authoring Tool"
        verbose_name_plural = "Authoring Tools"

        constraints = [
            # Postgres supports NULLS DISTINCT, but not all DB's do (Sqlite does not!) - hence workaround using two constraints
            # models.UniqueConstraint(fields=['name', 'version', 'company_id'], name='unique_name_version_company', nulls_distinct=False)
            models.UniqueConstraint(
                name="unique_name_version_company_id",
                fields=["name", "version", "company_id"],
            ),
            models.UniqueConstraint(
                name="unique_name_version_company_id_null",
                fields=["name", "version"],
                condition=Q(company_id__isnull=True),
            ),
        ]

    def __str__(self):

        return f"{self.full_name}".strip()

    @property
    def full_name(self):
        """
        Returns full name of the Authoring Tool, concatenating company, name and version (where available).
        An Authoring Tool has at least a name; company and version are optional.
        """

        full_name_without_version = (
            f"{self.company.name} - {self.name}".strip()
            if self.company
            else f"{self.name}".strip()
        )
        return (
            f"{full_name_without_version} - {self.version}".strip()
            if self.version
            else full_name_without_version
        )

    def find_by_full_name(full_name):
        """
        Look for the Authoring Tool(s) within the Company/Authoring Tool hierarchy.
        Fallback to matching records without versions, dashes and/or company.
        """

        def full_name_without_version_dash(full_name):
            without_version = full_name.rpartition(" - ")  # last dash only
            return "{} {}".format(
                without_version[0].strip(), without_version[2].strip()
            )

        def matches(obj, full_name):
            return (
                full_name == obj.full_name
                or full_name == full_name_without_version_dash(obj.full_name)
            )

        found = [
            obj for obj in AuthoringTool.objects.all() if matches(obj, full_name)
        ]  # cannot use a property to filter...

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
        related_name="models",
        null=True,
        blank=True,
        db_index=True,
        help_text="What tool was used to create this Model.",
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
        help_text="Original name of the file that contained this Model.",
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
        help_text="License of the Model.",
    )

    mvd = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="MVD Classification of the Model.",
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

    @functools.cached_property
    def _latest_task_status_by_type(self) -> dict[str, str]:
        """
        Returns {task_type: aggregate_status} using only the latest task per type
        for this model's request.
        """
        if not getattr(self, "request", None):
            return {}

        rows = (
            self.request.tasks
            .with_aggregate_status()
            .order_by("-created", "-id")
            .values_list("type", "aggregate_status")
        )
        return dict(rows)

    def _status_for(self, task_type) -> str:
        return self._latest_task_status_by_type.get(task_type, Model.Status.NOT_VALIDATED)

    status_bsdd = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the bSDD Validation.",
    )

    status_ia = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the IA Validation.",
    )

    @property
    def status_ia_calculated(self):
        return self._status_for(ValidationTask.Type.NORMATIVE_IA)

    status_ip = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the IP Validation.",
    )

    @property
    def status_ip_calculated(self):
        return self._status_for(ValidationTask.Type.NORMATIVE_IP)

    status_ids = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the IDS Validation.",
    )

    status_mvd = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the MVD Validation.",
    )

    status_schema = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Schema Validation.",
    )

    @property
    def status_schema_calculated(self):
        return self._status_for(ValidationTask.Type.SCHEMA)

    status_syntax = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Syntax Validation.",
    )

    # @nb syntax is never white-listed

    status_magic_clamav = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the file magic and anti-virus checks.",
    )

    status_header_syntax = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Syntax Validation of the header section.",
    )

    status_industry_practices = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Industry Practices Validation.",
    )

    status_prereq = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Prerequisites Validation.",
    )

    status_header = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Header Validation.",
    )

    status_signatures = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.NOT_VALIDATED,
        db_index=True,
        null=False,
        blank=False,
        help_text="Status of the Digital Signatures Validation.",
    )

    uploaded_by = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="models",
        null=False,
        db_index=True,
        help_text="Who uploaded this Model.",
    )

    properties = models.JSONField(
        null=True,
        blank=True,
        help_text="Properties of the Model."
    )

    header_validation = models.JSONField(
        null=True,
        blank=True,
        help_text="Validation of the Header of the Model."
    )

    class Meta:
        db_table = "ifc_model"
        verbose_name = "Model"
        verbose_name_plural = "Models"

    def __str__(self):

        return f"#{self.id} - {self.created.date()} - {self.file_name}"

    def reset_status(self):

        self.status_bsdd = Model.Status.NOT_VALIDATED
        self.status_ia = Model.Status.NOT_VALIDATED
        self.status_ip = Model.Status.NOT_VALIDATED
        self.status_ids = Model.Status.NOT_VALIDATED
        self.status_mvd = Model.Status.NOT_VALIDATED
        self.status_schema = Model.Status.NOT_VALIDATED
        self.status_syntax = Model.Status.NOT_VALIDATED
        self.status_header_syntax = Model.Status.NOT_VALIDATED
        self.status_industry_practices = Model.Status.NOT_VALIDATED
        self.status_prereq = Model.Status.NOT_VALIDATED
        self.status_header = Model.Status.NOT_VALIDATED
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
        related_name="instances",
        blank=False,
        null=False,
        db_index=True,
        help_text="What Model this Model Instance is a part of.",
    )

    stepfile_id = models.PositiveBigIntegerField(
        null=False,
        blank=False,
        db_index=True,
        help_text="id assigned within the Step File (eg. #11)",
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

        constraints = [
            models.UniqueConstraint(
                fields=["model_id", "stepfile_id"], name="modelid_stepfileid"
            )
        ]

    def __str__(self):

        return f"#{self.id} - {self.ifc_type} - {self.model.file_name}"


class ValidationRequest(AuditedBaseModel, SoftDeletableModel, IdObfuscator):
    """
    A model to store and track Validation Requests.
    """

    class Status(models.TextChoices):
        """
        The overall status of a Validation Request.
        """
        PENDING   = 'PENDING', 'Pending'
        INITIATED = 'INITIATED', 'Initiated'
        FAILED    = 'FAILED', 'Failed'
        COMPLETED = 'COMPLETED', 'Completed'

    class Channel(models.TextChoices):
        """
        The channel used to create a Validation Request.
        """
        WEBUI   = 'WEBUI', 'WebUi'
        API     = 'API', 'Api'

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Validation Request (auto-generated).",
    )

    file_name = models.CharField(
        max_length=1024,
        null=False,
        blank=False,
        verbose_name="file name",
        help_text="Name of the file.",
    )

    file_removed = models.DateTimeField(
        null=True,
        db_index=True,
        help_text="Timestamp the file was removed.",
    )

    file = models.FileField(
        null=False,
        max_length=2048,
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
        help_text="Current status of the Validation Request.",
    )

    status_reason = SanitizedCharField(
        null=True, 
        blank=True, 
        help_text="Reason for current status."
    )

    started = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name="started",
        help_text="Timestamp the Validation Request was started.",
    )

    completed = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name="completed",
        help_text="Timestamp the Validation Request completed.",
    )

    progress = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Overall progress (%) of the Validation Request.",
    )

    model = models.OneToOneField(
        to=Model,
        on_delete=models.CASCADE,
        related_name="request",
        null=True,
        db_index=True,
        help_text="What Model is created based on this Validation Request.",
    )

    channel = models.CharField(
        max_length=10,
        choices=Channel.choices,
        default=Channel.API,
        db_index=True,
        null=False,
        blank=False,
        help_text="What channel was used to create this Validation Request.",
    )

    class Meta:

        db_table = "ifc_validation_request"
        indexes = [
            models.Index(fields=["file_name", "status"])
        ]  # only add multi-column indexes here
        verbose_name = "Validation Request"
        verbose_name_plural = "Validation Requests"
        permissions = [("change_status", "Can change status of Validation Request")]

    def __str__(self):

        return f"#{self.id} - {self.created.date()} - {self.file_name}"

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
            return self.completed - self.started
        elif self.started:
            return timezone.now() - self.started
        else:
            return None

    @property
    def model_public_id(self):
        return (
            IdObfuscator.to_public_id(self.model_id, override_cls=Model)
            if self.model_id
            else None
        )

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

    def remove_file(self):

        self.file = None
        self.file_removed = timezone.now()
        self.save(update_fields=['file', 'file_removed'])


class ValidationTaskQuerySet(models.QuerySet):
    def with_aggregate_status(self, include_whitelist: bool = True):
        wl_annotations = {}
        wl_q = Q(**{"outcomes__pk__in": []})  # always false

        if include_whitelist:
            whitelist_entries = WhiteListEntry.objects.all()
            if whitelist_entries:
                query = functools.reduce(operator.or_, map(lambda wle: wle.build("outcomes__"), whitelist_entries))
                wl_annotations, wl_q = query.annotations, query.q

        # mirror your "only check whitelist for >= WARNING"
        wl_cond = (
            Q(outcomes__severity_in_db__gte=ValidationOutcome.OutcomeSeverity.WARNING)
            & wl_q
        )

        severity_rank = Case(
            # non-whitelisted ERROR/WARNING are "bad"
            When(
                Q(outcomes__severity_in_db=ValidationOutcome.OutcomeSeverity.ERROR) & ~wl_cond,
                then=Value(3),
            ),
            When(
                Q(outcomes__severity_in_db=ValidationOutcome.OutcomeSeverity.WARNING) & ~wl_cond,
                then=Value(2),
            ),

            # whitelisted WARNING/ERROR become "valid"
            When(wl_cond, then=Value(1)),

            # normal "good" severities
            When(
                outcomes__severity_in_db__in=[
                    ValidationOutcome.OutcomeSeverity.EXECUTED,
                    ValidationOutcome.OutcomeSeverity.PASSED,
                ],
                then=Value(1),
            ),
            When(outcomes__severity_in_db=ValidationOutcome.OutcomeSeverity.NOT_APPLICABLE, then=Value(0)),
            default=Value(-1),
            output_field=IntegerField(),
        )

        return (
            self.annotate(**wl_annotations)
            .annotate(_agg_rank=Coalesce(Max(severity_rank), Value(1)))  # no outcomes => VALID
            .annotate(
                aggregate_status=Case(
                    When(_agg_rank=3, then=Value(Model.Status.INVALID)),
                    When(_agg_rank=2, then=Value(Model.Status.WARNING)),
                    When(_agg_rank=1, then=Value(Model.Status.VALID)),
                    When(_agg_rank=0, then=Value(Model.Status.NOT_APPLICABLE)),
                    default=Value(Model.Status.VALID),
                    output_field=CharField(),
                )
            )
        )


class ValidationTask(TimestampedBaseModel, IdObfuscator):
    objects = ValidationTaskQuerySet.as_manager()

    """
    A model to store and track Validation Tasks.
    """

    class Type(models.TextChoices):
        """
        The type of an Validation Task.
        """
        MAGIC_AND_CLAMAV    = 'MAGIC_AND_CLAMAV', 'File magic and anti-virus checks',
        SYNTAX              = 'SYNTAX', 'STEP Physical File Syntax'
        HEADER_SYNTAX       = 'HEADER_SYNTAX', 'STEP Physical File Syntax (HEADER section)'
        SCHEMA              = 'SCHEMA', 'Schema (EXPRESS language)'
        MVD                 = 'MVD', 'Model View Definitions'
        BSDD                = 'BSDD', 'bSDD Compliance'
        PARSE_INFO          = 'INFO', 'Parse Info'
        PREREQUISITES       = 'PREREQ', 'Prerequisites'
        HEADER              = 'HEADER', 'Header Validation'
        NORMATIVE_IA        = 'NORMATIVE_IA', 'Implementer Agreements (IA)'
        NORMATIVE_IP        = 'NORMATIVE_IP', 'Informal Propositions (IP)'
        INDUSTRY_PRACTICES  = 'INDUSTRY', 'Industry Practices'
        INSTANCE_COMPLETION = 'INST_COMPLETION', 'Instance Completion'
        DIGITAL_SIGNATURES  = 'DIGITAL_SIGNATURES', 'Digital Signatures'

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
        primary_key=True, help_text="Identifier of the task (auto-generated)."
    )

    request = models.ForeignKey(
        to=ValidationRequest,
        on_delete=models.CASCADE,
        related_name="tasks",
        blank=False,
        null=False,
        db_index=True,
        help_text="What Validation Request this Validation Task belongs to.",
    )

    type = models.CharField(
        max_length=25,
        choices=Type.choices,
        db_index=True,
        null=False,
        blank=False,
        help_text="Type of the Validation Task.",
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        null=False,
        blank=False,
        help_text="Current status of the Validation Task.",
    )

    status_reason = SanitizedCharField(
        null=True,
        blank=True,
        help_text="Reason for current status."
    )

    started = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name="started",
        help_text="Timestamp the Validation Task was started.",
    )

    ended = models.DateTimeField(
        null=True,
        db_index=True,
        verbose_name="ended",
        help_text="Timestamp the Validation Task ended.",
    )

    progress = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Overall progress (%) of the Validation Task.",
    )

    process_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Process id of subprocess executing the Validation Task.",
    )

    process_cmd = models.TextField(
        null=True,
        blank=True,
        help_text="Command and arguments used to launch the subprocess executing the Validation Task.",
    )

    class Meta:

        db_table = "ifc_validation_task"
        verbose_name = "Validation Task"
        verbose_name_plural = "Validation Tasks"

    def __str__(self):

        return f"#{self.id} - {self.request.file_name} - {self.type} - {self.created.date()} - {self.status}"

    @property
    def has_final_status(self):

        FINAL_STATUS_LIST = [
            self.Status.SKIPPED,
            self.Status.FAILED,
            self.Status.NOT_APPLICABLE,
            self.Status.COMPLETED,
        ]
        return self.status in FINAL_STATUS_LIST

    @property
    def duration(self):

        if self.started and self.ended:
            return self.ended - self.started
        elif self.started:
            return timezone.now() - self.started
        else:
            return None

    @property
    def request_public_id(self):
        return (
            IdObfuscator.to_public_id(self.request_id, override_cls=ValidationRequest)
            if self.request_id
            else None
        )

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
            if (
                outcome.severity == ValidationOutcome.OutcomeSeverity.NOT_APPLICABLE
                and agg_status is None
            ):
                agg_status = Model.Status.NOT_APPLICABLE
            elif (
                outcome.severity == ValidationOutcome.OutcomeSeverity.EXECUTED
                and agg_status in [None, Model.Status.NOT_APPLICABLE]
            ):
                agg_status = Model.Status.VALID
            elif (
                outcome.severity == ValidationOutcome.OutcomeSeverity.PASSED
                and agg_status in [None, Model.Status.NOT_APPLICABLE]
            ):
                agg_status = Model.Status.VALID
            elif outcome.severity == ValidationOutcome.OutcomeSeverity.WARNING:
                agg_status = Model.Status.WARNING
            elif outcome.severity == ValidationOutcome.OutcomeSeverity.ERROR:
                agg_status = Model.Status.INVALID
                break  # can't get any worse...

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

    @functools.cached_property
    def is_whitelisted(self):
        if self.severity_in_db < ValidationOutcome.OutcomeSeverity.WARNING:
            # never check for lower than warning, because potentially expensive query
            return False
        whitelist_entries = WhiteListEntry.objects.all()
        if not whitelist_entries:
            return False
        query = functools.reduce(operator.or_, map(lambda wle: wle.build(), whitelist_entries))
        return query.apply(ValidationOutcome.objects.filter(pk=self.id)).exists()

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

    _inst = None  # temp internal-use attribute to store the instance of the model being validated for further use in behave statements

    id = models.AutoField(
        primary_key=True,
        help_text="Identifier of the Validation Outcome (auto-generated).",
    )

    instance = models.ForeignKey(
        to=ModelInstance,
        on_delete=models.CASCADE,
        related_name="outcomes",
        null=True,
        db_index=True,
        help_text="What Model Instance this Outcome is applicable to (optional).",
    )

    validation_task = models.ForeignKey(
        to=ValidationTask,
        on_delete=models.CASCADE,
        related_name="outcomes",
        blank=False,
        null=False,
        db_index=True,
        help_text="What Validation Task this Outcome belongs to.",
    )

    feature = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        help_text="Name of the Gherkin Feature (optional).",
    )

    feature_version = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Version number of the Gherkin Feature (optional).",
    )

    severity_in_db = models.PositiveSmallIntegerField(
        choices=OutcomeSeverity.choices,
        default=OutcomeSeverity.NOT_APPLICABLE,
        db_index=True,
        null=False,
        blank=False,
        help_text="Severity of the Validation Outcome.",
        db_column="severity"
    )

    @property
    def severity(self):
        return ValidationOutcome.OutcomeSeverity.PASSED if self.is_whitelisted else self.severity_in_db

    @severity.setter
    def severity(self, value):
        self.severity_in_db = value
        return self.severity_in_db

    outcome_code = models.CharField(
        max_length=10,
        choices=ValidationOutcomeCode.choices,
        default=ValidationOutcomeCode.NOT_APPLICABLE,
        help_text="Code representing the Validation Outcome.",
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
            models.Index(fields=["feature", "feature_version", "severity_in_db"]),
        ]

    def __str__(self):
        members = {
            "Feature": (self.feature or "").split("-")[0].strip(),
            "Outcome": self.outcome_code,
            "Severity": repr(self.severity).split(".")[-1],
            "ifc_instance_id": self.instance_id,
            "Expected": self.expected,
            "Observed": self.observed,
        }
        return f' '.join(f'{k}={repr(v)}' for k, v in members.items() if v is not None)

    def to_dict(self):
        return {
            "id": self.id,
            "instance_id": self.instance_public_id,
            "validation_task_id": self.validation_task_public_id,
            "feature": self.feature,
            "feature_version": self.feature_version,
            "severity": self.get_severity_display(),  # Convert the integer to a human-readable string
            "outcome_code": self.outcome_code,
            "expected": self.expected,
            "observed": self.observed,
        }

    @property
    def instance_public_id(self):
        return (
            IdObfuscator.to_public_id(self.instance_id, override_cls=ModelInstance)
            if self.instance_id
            else None
        )

    @property
    def validation_task_public_id(self):
        return (
            IdObfuscator.to_public_id(
                self.validation_task_id, override_cls=ValidationTask
            )
            if self.validation_task_id
            else None
        )

    @property
    def inst(self):
        return self._inst

    @inst.setter
    def inst(self, value):
        self._inst = value

    def determine_severity(self):

        match self.name[0]:
            case "X":
                return self.OutcomeSeverity.EXECUTED
            case "P":
                return self.OutcomeSeverity.PASSED
            case "N":
                return self.OutcomeSeverity.NOT_APPLICABLE
            case "W":
                return self.OutcomeSeverity.WARNING
            case "E":
                return self.OutcomeSeverity.ERROR
            case _:
                raise ValueError(f"Outcome code '{self.name}' not recognized")


class Version(TimestampedBaseModel):
    """
    A model to store and track Validation Service software versions.
    """

    id = models.AutoField(
        primary_key=True, help_text="Identifier of the Version (auto-generated)."
    )

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
        help_text="Name of the Version, eg. 0.6.8",
    )

    released = models.DateTimeField(
        null=False, blank=False, help_text="Timestamp the Version was released."
    )

    release_notes = models.TextField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Description or URL of the Release Notes (optional).",
    )

    class Meta:

        db_table = "ifc_version"
        verbose_name = "Version"
        verbose_name_plural = "Versions"

    def __str__(self):

        return f"{self.name}"

@dataclass
class WhiteListEntryQueryBlock:
    q : Q
    annotations : dict

    def __or__(self, other : 'WhiteListEntryQueryBlock'):
        return WhiteListEntryQueryBlock(self.q | other.q, self.annotations | other.annotations)

    def apply(self, outcomes_query_set : QuerySet):
        if self.annotations:
            outcomes_query_set = outcomes_query_set.annotate(**self.annotations)

        return outcomes_query_set.filter(self.q)


@dataclass(frozen=True)
class FragSnap:
    id: int
    column: str
    operation: str
    right_hand_side: str


@dataclass(frozen=True)
class EntrySnap:
    id: int
    description: str
    fragments: list[FragSnap]


class WhiteListEntry(AuditedBaseModel):
    id = models.AutoField(
        primary_key=True, help_text="Identifier of the Whitelist Entry (auto-generated)."
    )

    description = models.CharField(
        max_length=255,
        blank=True,
    )

    @staticmethod
    def get_all():
        snaps: list[EntrySnap] = []
        suffix = ""
        for e in WhiteListEntry.objects.prefetch_related("fragments").order_by("id").iterator(chunk_size=16):
            frags = [
                FragSnap(
                    id=f.id,
                    column=f.column,
                    operation=f.operation,
                    right_hand_side=f.right_hand_side,
                )
                for f in e.fragments.all().order_by("id")
            ]
            if suffix:
                suffix += "_"
            suffix += e.description.lower().replace(' ', '_')
            snaps.append(EntrySnap(id=e.id, description=e.description, fragments=frags))
        return snaps

    def __str__(self):
        return f"#{self.id}: {self.description}: {' | '.join(map(str, self.fragments.all()))}"

    def build(self, prefix=""):
        q = Q()

        annotations = {}
        def ensure_text_cast(path: str) -> str:
            key = f"_wl_text__{path.replace('__', '_')}"
            if key not in annotations:
                annotations[key] = Cast(path, TextField())
            return key

        for f in self.fragments.all():
            col = prefix + f.column
            op = f.operation
            rhs = (f.right_hand_side or "").strip()
            kind = f.column_kind

            if kind == WhiteListQueryFragment.ColumnKind.INT:
                rhs_int = int(rhs)
                q &= Q(**{col: rhs_int})
            elif kind == WhiteListQueryFragment.ColumnKind.JSON:
                ann = ensure_text_cast(col)
                q &= Q(**{f"{ann}__icontains": rhs})
            elif op == WhiteListQueryFragment.Operation.EQUALS:
                q &= Q(**{f"{col}__iexact": rhs})
            elif op == WhiteListQueryFragment.Operation.CONTAINS:
                q &= Q(**{f"{col}__icontains": rhs})

        return WhiteListEntryQueryBlock(q, annotations)
        

class WhiteListQueryFragment(models.Model):
    class ColumnKind(Enum):
        TEXT = "text"
        INT  = "int"
        JSON = "json"

    class OutcomeColumn(models.TextChoices):
        """
        Outcome column to query
        """
        INSTANCE_TYPE = 'instance__ifc_type', 'Instance type'
        TASK_TYPE = 'validation_task__type', 'Task type'
        FEATURE = 'feature', 'Feature'
        FEATURE_VERSION = 'feature_version', 'Feature version'
        EXPECTED = 'expected', 'Expected'
        OBSERVED = 'observed', 'Observed'
        MODEL_SCHEMA = 'validation_task__request__model__schema', 'Model schema'
        INSTANCE_FIELDS = 'instance__fields', 'Instance fields'

    class Operation(models.TextChoices):
        EQUALS = 'EQUALS', 'Equals'
        CONTAINS = 'CONTAINS', 'Contains'

    id = models.AutoField(
        primary_key=True, help_text="Identifier of the Query Fragment (auto-generated)."
    )

    column = models.CharField(
        max_length=39,
        choices=OutcomeColumn.choices,
        help_text="Outcome column this query fragment is bound to",
    )

    operation = models.CharField(
        max_length=8,
        choices=Operation.choices,
        help_text="Predicate this query fragment is based on to",
    )

    right_hand_side = models.TextField(
        max_length=255,
        help_text="Right hand side of the query fragment",
    )

    whitelist_entry = models.ForeignKey(
        WhiteListEntry,
        related_name="fragments",
        on_delete=models.CASCADE,
        help_text="What Whitelist Entry this fragment is part of",
    )

    _KIND_BY_COLUMN = {
        OutcomeColumn.EXPECTED: ColumnKind.JSON,
        OutcomeColumn.OBSERVED: ColumnKind.JSON,
        OutcomeColumn.FEATURE_VERSION: ColumnKind.INT,
        OutcomeColumn.INSTANCE_TYPE: ColumnKind.TEXT,
        OutcomeColumn.INSTANCE_FIELDS: ColumnKind.JSON,
        OutcomeColumn.TASK_TYPE: ColumnKind.TEXT,
        OutcomeColumn.FEATURE: ColumnKind.TEXT,
        OutcomeColumn.MODEL_SCHEMA: ColumnKind.TEXT,
    }

    def __str__(self):
        return f"({self.column} {self.operation} {self.right_hand_side})"

    @property
    def column_kind(self) -> ColumnKind:
        try:
            return self._KIND_BY_COLUMN[self.column]
        except KeyError:
            return WhiteListQueryFragment.ColumnKind.TEXT

    def clean(self):
        rhs = (self.right_hand_side or "").strip()
        if rhs == "":
            raise ValidationError({"right_hand_side": "Right-hand side cannot be empty."})

        if self.column_kind == WhiteListQueryFragment.ColumnKind.INT:
            try:
                int(rhs)
            except (TypeError, ValueError):
                raise ValidationError({"right_hand_side": f"RHS must be an integer for column '{self.column}'."})
        
        if self.operation == WhiteListQueryFragment.Operation.EQUALS:
            if self.column_kind == WhiteListQueryFragment.ColumnKind.JSON:
                raise ValidationError({"operation": f"Equals is not supported for JSON column type on column '{self.column}'."})
        else:
            if self.column_kind == WhiteListQueryFragment.ColumnKind.INT:
                raise ValidationError({"operation": f"Contains is not supported for INT column type on column '{self.column}'."})

id_prefix_mapping = {
    Model: "m",
    ModelInstance: "i",
    ValidationRequest: "r",
    ValidationTask: "t",
    ValidationOutcome: "o",
    User: "u",
}
