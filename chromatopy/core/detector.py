from typing import Dict, Optional
from uuid import uuid4

import sdRDM
from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM.base.datatypes import Unit
from sdRDM.base.listplus import ListPlus
from sdRDM.tools.utils import elem2dict


class Detector(
    sdRDM.DataModel,
    search_mode="unordered",
):
    """Base class for detectors."""

    id: Optional[str] = attr(
        name="id",
        alias="@id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
    )

    type: Optional[str] = element(
        description="Type of detector",
        default=None,
        tag="type",
        json_schema_extra=dict(),
    )

    flow_mode: Optional[str] = element(
        description="Airflow mode",
        default=None,
        tag="flow_mode",
        json_schema_extra=dict(),
    )

    makeup_flow: Optional[float] = element(
        description="Makeup flow",
        default=None,
        tag="makeup_flow",
        json_schema_extra=dict(),
    )

    makeup_gas: Optional[str] = element(
        description="Makeup gas",
        default=None,
        tag="makeup_gas",
        json_schema_extra=dict(),
    )

    flow_unit: Optional[Unit] = element(
        description="Unit of flow",
        default=None,
        tag="flow_unit",
        json_schema_extra=dict(),
    )

    reference_flow: Optional[float] = element(
        description="Reference flow",
        default=None,
        tag="reference_flow",
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
