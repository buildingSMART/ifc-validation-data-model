from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, Enum
from typing import Any, Optional, Union, Mapping, Sequence

JSONLike = Union[None, bool, int, float, str, Mapping[str, Any], Sequence[Any]]


# @todo decide whether the django string choices are in fact light weight enough. Maybe it's only the action models that need a dataclass equivalent.
class OutcomeSeverity(IntEnum):
    EXECUTED       = 1
    PASSED         = 2
    WARNING        = 3
    ERROR          = 4
    NOT_APPLICABLE = 0

class ValidationOutcomeCode(str, Enum):
    # passed / N/A
    PASSED                                 = "P00010"
    NOT_APPLICABLE                         = "N00010"

    # errors
    SYNTAX_ERROR                           = "E00001"
    SCHEMA_ERROR                           = "E00002"
    TYPE_ERROR                             = "E00010"
    VALUE_ERROR                            = "E00020"
    GEOMETRY_ERROR                         = "E00030"
    CARDINALITY_ERROR                      = "E00040"
    DUPLICATE_ERROR                        = "E00050"
    PLACEMENT_ERROR                        = "E00060"
    UNITS_ERROR                            = "E00070"
    QUANTITY_ERROR                         = "E00080"
    ENUMERATED_VALUE_ERROR                 = "E00090"
    RELATIONSHIP_ERROR                     = "E00100"
    NAMING_ERROR                           = "E00110"
    REFERENCE_ERROR                        = "E00120"
    RESOURCE_ERROR                         = "E00130"
    DEPRECATION_ERROR                      = "E00140"
    SHAPE_REPRESENTATION_ERROR             = "E00150"
    INSTANCE_STRUCTURE_ERROR               = "E00160"

    # warnings / executed
    ALIGNMENT_CONTAINS_BUSINESS_LOGIC_ONLY = "W00010"
    ALIGNMENT_CONTAINS_GEOMETRY_ONLY       = "W00020"
    WARNING                                = "W00030"
    EXECUTED                               = "X00040"

SeverityLike = Union[int, OutcomeSeverity]

@dataclass(slots=True, kw_only=True, frozen=True, eq=True)
class ValidationOutcome:
    """A memory-lean DTO equivalent of ValidationOutcome."""
    # id: Optional[int]
    instance_id: Optional[int] = -1
    # validation_task_id: int
    feature: Optional[str] = None
    feature_version: Optional[int] = None
    severity: SeverityLike
    outcome_code: ValidationOutcomeCode | str = None
    expected: Optional[JSONLike] = None
    observed: Optional[JSONLike] = None
    # created: Optional[datetime] = None
    # updated: Optional[datetime] = None

    # ---------- parity helpers ----------
    def severity_label(self) -> str:
        # @todo probably don't need this.
        """Human-readable label like Django's get_severity_display()."""
        mapping = {
            OutcomeSeverity.EXECUTED: "Executed",
            OutcomeSeverity.PASSED: "Passed",
            OutcomeSeverity.WARNING: "Warning",
            OutcomeSeverity.ERROR: "Error",
            OutcomeSeverity.NOT_APPLICABLE: "N/A",
        }
        sev = OutcomeSeverity(int(self.severity))
        return mapping.get(sev, str(int(self.severity)))

    def to_dict(self,
                instance_public_id: Optional[str] = None,
                validation_task_public_id: Optional[str] = None) -> dict[str, Any]:
        # @todo can use dataclass.asdict()?
        return {
            # "id": self.id,
            "instance_id": instance_public_id,
            "validation_task_id": validation_task_public_id,
            "feature": self.feature,
            "feature_version": self.feature_version,
            "severity": self.severity_label(),
            "outcome_code": str(self.outcome_code),
            # "expected": self.expected,
            # "observed": self.observed,
        }

    def determine_severity(self) -> OutcomeSeverity:
        # @todo probably don't need this
        """Mirror of the model method, using the outcome_code's first letter."""
        code = str(self.outcome_code)
        if not code:
            raise ValueError("Outcome code not set")
        match code[0]:
            case "X": return OutcomeSeverity.EXECUTED
            case "P": return OutcomeSeverity.PASSED
            case "N": return OutcomeSeverity.NOT_APPLICABLE
            case "W": return OutcomeSeverity.WARNING
            case "E": return OutcomeSeverity.ERROR
            case _:   raise ValueError(f"Outcome code '{code}' not recognized")

    # ---------- Django conversion ----------
    @classmethod
    def from_model(cls, obj: "ValidationOutcome") -> "ValidationOutcomeDTO":
        # @todo never needed because we only need to convert the other way around
        """
        Create a DTO from a Django ValidationOutcome instance.
        NOTE: import this at call-site to avoid circular imports.
        """
        return cls(
            id=obj.id,
            instance_id=obj.instance_id,
            validation_task_id=obj.validation_task_id,
            feature=obj.feature,
            feature_version=obj.feature_version,
            severity=int(obj.severity),
            outcome_code=str(obj.outcome_code),
            expected=obj.expected,
            observed=obj.observed,
            created=getattr(obj, "created", None),
            updated=getattr(obj, "updated", None),
        )

    def to_model_fields(self) -> dict[str, Any]:
        # @todo single to_dict call
        """Field dict you can pass into the Django model ctor/update."""
        return {
            "id": self.id,  # Django ignores id on create unless explicitly set
            "instance_id": self.instance_id,
            "validation_task_id": self.validation_task_id,
            "feature": self.feature,
            "feature_version": self.feature_version,
            "severity": int(self.severity),
            "outcome_code": str(self.outcome_code),
            "expected": self.expected,
            "observed": self.observed,
            # created/updated are managed by the model
        }

    def into_model(self,
                   *,
                   existing: Optional["ValidationOutcome"] = None,
                   save: bool = False) -> "ValidationOutcome":
        # @todo not necessary, use to_dict() and then kwarg that into a django model
        """
        Create or update a Django ValidationOutcome instance from this DTO.
        If `existing` is provided, it's updated in-place. If `save=True`, it is saved.
        """
        from yourapp.models import ValidationOutcome  # adjust import to your app

        if existing is None:
            obj = ValidationOutcome(**{k: v for k, v in self.to_model_fields().items() if k != "id"})
            # optionally set explicit id if you really need to (usually you don't):
            if self.id is not None:
                obj.id = self.id
        else:
            obj = existing
            for k, v in self.to_model_fields().items():
                if k == "id":
                    continue
                setattr(obj, k, v)

        if save:
            obj.save()
        return obj
