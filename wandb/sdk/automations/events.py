from __future__ import annotations

from enum import StrEnum
from typing import Literal, Union

from pydantic import Field, Json
from typing_extensions import Annotated

from wandb.sdk.automations.base import Base
from wandb.sdk.automations.expressions import AnyExpr, MetricPredicate


# Triggers on mutation
class FilterEventType(StrEnum):
    ADD_ARTIFACT_ALIAS = "ADD_ARTIFACT_ALIAS"
    CREATE_ARTIFACT = "CREATE_ARTIFACT"
    LINK_ARTIFACT = "LINK_MODEL"
    UPDATE_ARTIFACT_ALIAS = "UPDATE_ARTIFACT_ALIAS"


class Filter(Base):
    filter: Json[AnyExpr]


class FilterEvent(Base):
    typename__: Literal["FilterEventTriggeringCondition"] = Field(
        repr=False, alias="__typename"
    )
    event_type: FilterEventType
    filter: Json[Filter]


# Triggers on run metrics
class RunMetricEvent(Base):
    typename__: Literal["RunMetricTriggeringCondition"] = Field(
        repr=False, alias="__typename"
    )
    event_type: str  # TODO: TBD

    run_filter: Json[Filter]
    metric_filter: Json[MetricPredicate]


AnyEvent = Annotated[
    Union[
        FilterEvent,
        RunMetricEvent,
    ],
    Field(alias="triggeringCondition"),
]
