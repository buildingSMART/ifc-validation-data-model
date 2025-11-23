from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, Enum
import sys
from typing import Any, Optional, Union, Mapping, Sequence

JSONLike = Union[None, bool, int, float, str, Mapping[str, Any], Sequence[Any]]


# @todo decide whether the django string choices are in fact light weight enough. Maybe it's only the action models that need a dataclass equivalent.
class OutcomeSeverity(IntEnum):
    EXECUTED = 1
    PASSED = 2
    WARNING = 3
    ERROR = 4
    NOT_APPLICABLE = 0


class ValidationOutcomeCode(str, Enum):
    # passed / N/A
    PASSED = "P00010"
    NOT_APPLICABLE = "N00010"

    # errors
    SYNTAX_ERROR = "E00001"
    SCHEMA_ERROR = "E00002"
    TYPE_ERROR = "E00010"
    VALUE_ERROR = "E00020"
    GEOMETRY_ERROR = "E00030"
    CARDINALITY_ERROR = "E00040"
    DUPLICATE_ERROR = "E00050"
    PLACEMENT_ERROR = "E00060"
    UNITS_ERROR = "E00070"
    QUANTITY_ERROR = "E00080"
    ENUMERATED_VALUE_ERROR = "E00090"
    RELATIONSHIP_ERROR = "E00100"
    NAMING_ERROR = "E00110"
    REFERENCE_ERROR = "E00120"
    RESOURCE_ERROR = "E00130"
    DEPRECATION_ERROR = "E00140"
    SHAPE_REPRESENTATION_ERROR = "E00150"
    INSTANCE_STRUCTURE_ERROR = "E00160"

    # warnings / executed
    ALIGNMENT_CONTAINS_BUSINESS_LOGIC_ONLY = "W00010"
    ALIGNMENT_CONTAINS_GEOMETRY_ONLY = "W00020"
    WARNING = "W00030"
    EXECUTED = "X00040"


class FrozenDict(frozenset):
    def __repr__(self):
        return repr(dict(self))


def freeze(obj):
    """
    Recursively convert dict-like structures into FrozenDict (immutable).
    Lists and tuples are converted to tuples.
    Strings are interned (todo benchmark)
    """
    if isinstance(obj, Mapping):
        return FrozenDict((k, freeze(v)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        return tuple(freeze(v) for v in obj)
    elif isinstance(obj, (set, frozenset)):
        return frozenset(freeze(v) for v in obj)
    elif isinstance(obj, str):
        return sys.intern(obj)
    else:
        return obj


def unfreeze(obj):
    """
    Recursively convert MappingProxyType (or mapping-like) objects back to dicts.
    Don't care about frozenset/tuples, just dicts for json serializability,
    we don't actually want to mutate
    """
    if isinstance(obj, FrozenDict):
        return {k: unfreeze(v) for k, v in obj}
    elif isinstance(obj, (set, frozenset)):
        return list(map(unfreeze, obj))
    elif isinstance(obj, (list, tuple)):
        return tuple(unfreeze(v) for v in obj)
    else:
        return obj



@dataclass(slots=True, kw_only=True, frozen=True, eq=True)
class ValidationOutcome:
    """A memory-lean DTO equivalent of ValidationOutcome."""

    inst: Optional[int] = None
    feature: Optional[str] = None
    feature_version: Optional[int] = None
    severity: OutcomeSeverity
    outcome_code: ValidationOutcomeCode = None
    expected: Optional[JSONLike] = None
    observed: Optional[JSONLike] = None

    def to_dict(
        self, validation_task_public_id: Optional[str] = None
    ) -> dict[str, Any]:
        return {
            "inst": self.inst,
            "validation_task_id": validation_task_public_id,
            "feature": self.feature,
            "feature_version": self.feature_version,
            "severity": self.severity.name if validation_task_public_id else int(self.severity),
            "outcome_code": str(self.outcome_code),
            "expected": unfreeze(self.expected),
            "observed": unfreeze(self.observed),
        }
    
    def __post_init__(self):
        # convert all dicts to MappingProxyType for immutability
        object.__setattr__(self, 'expected', freeze(self.expected))
        object.__setattr__(self, 'observed', freeze(self.observed))
        # intern strings for mem reduction (todo benchmark)
        if self.feature:
            object.__setattr__(self, 'feature', sys.intern(self.feature))
