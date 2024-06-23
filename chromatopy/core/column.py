from typing import Dict, Optional
from uuid import uuid4

import sdRDM
from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM.base.datatypes import Unit
from sdRDM.base.listplus import ListPlus
from sdRDM.tools.utils import elem2dict

from .detector import Detector
from .inlet import Inlet


class Column(
    sdRDM.DataModel,
    search_mode="unordered",
):
    """Describes properties of a column and its connections to the inlet and detector."""

    id: Optional[str] = attr(
        name="id",
        alias="@id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
    )

    name: Optional[str] = element(
        description="Name of the column",
        default=None,
        tag="name",
        json_schema_extra=dict(),
    )

    type: Optional[str] = element(
        description="Type of column",
        default=None,
        tag="type",
        json_schema_extra=dict(),
    )

    max_temp: Optional[float] = element(
        description="Maximum temperature of the column",
        default=None,
        tag="max_temp",
        json_schema_extra=dict(),
    )

    length: Optional[float] = element(
        description="Length of the column",
        default=None,
        tag="length",
        json_schema_extra=dict(),
    )

    diameter: Optional[float] = element(
        description="Diameter of the column",
        default=None,
        tag="diameter",
        json_schema_extra=dict(),
    )

    film_thickness: Optional[float] = element(
        description="Film thickness of the column",
        default=None,
        tag="film_thickness",
        json_schema_extra=dict(),
    )

    flow_mode: Optional[str] = element(
        description="Flow mode of the column",
        default=None,
        tag="flow_mode",
        json_schema_extra=dict(),
    )

    flow_rate: Optional[float] = element(
        description="Flow rate of the column",
        default=None,
        tag="flow_rate",
        json_schema_extra=dict(),
    )

    flow_unit: Optional[Unit] = element(
        description="Unit of flow rate",
        default=None,
        tag="flow_unit",
        json_schema_extra=dict(),
    )

    inlet: Optional[Inlet] = element(
        description="Inlet of the column",
        default_factory=Inlet,
        tag="inlet",
        json_schema_extra=dict(),
    )

    detector: Optional[Detector] = element(
        description="Outlet of the column, connected to the detector",
        default_factory=Detector,
        tag="detector",
        json_schema_extra=dict(),
    )

    outlet_pressure: Optional[float] = element(
        description="Outlet pressure of the column",
        default=None,
        tag="outlet_pressure",
        json_schema_extra=dict(),
    )

    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="bc10c2adaa50a977b0a99da28b4bf3671887f5e6"
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
