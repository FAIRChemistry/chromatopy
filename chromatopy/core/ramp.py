from typing import Dict, Optional
from uuid import uuid4

import sdRDM
from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM.base.datatypes import Unit
from sdRDM.base.listplus import ListPlus
from sdRDM.tools.utils import elem2dict


class Ramp(
    sdRDM.DataModel,
    search_mode="unordered",
):
    """Describes properties of a temperature ramp."""

    id: Optional[str] = attr(
        name="id",
        alias="@id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
    )

    temp_rate: Optional[float] = element(
        description="Rate of temperature change during the ramp",
        default=None,
        tag="temp_rate",
        json_schema_extra=dict(),
    )

    final_temp: Optional[float] = element(
        description="Final temperature of the ramp",
        default=None,
        tag="final_temp",
        json_schema_extra=dict(),
    )

    hold_time: Optional[float] = element(
        description=(
            "Duration to hold the final temperature before starting the next ramp"
        ),
        default=None,
        tag="hold_time",
        json_schema_extra=dict(),
    )

    time_unit: Optional[Unit] = element(
        description="Unit of time",
        default=None,
        tag="time_unit",
        json_schema_extra=dict(),
    )

    _raw_xml_data: Dict = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _parse_raw_xml_data(self):
        for attr, value in self:
            if isinstance(value, (ListPlus, list)) and all(
                isinstance(i, _Element) for i in value
            ):
                self._raw_xml_data[attr] = [elem2dict(i) for i in value]
            elif isinstance(value, _Element):
                self._raw_xml_data[attr] = elem2dict(value)

        return self
