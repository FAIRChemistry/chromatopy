import sdRDM

from typing import Dict, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict


@forge_signature
class Peak(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    retention_time: Optional[float] = element(
        description="Retention time of the peak",
        default=None,
        tag="retention_time",
        json_schema_extra=dict(),
    )

    retention_time_unit: Optional[str] = element(
        description="Unit of retention time",
        default=None,
        tag="retention_time_unit",
        json_schema_extra=dict(),
    )

    type: Optional[str] = element(
        description="Type of peak (baseline-baseline / baseline-valey / ...)",
        default=None,
        tag="type",
        json_schema_extra=dict(),
    )

    width: Optional[float] = element(
        description="Width of the peak",
        default=None,
        tag="width",
        json_schema_extra=dict(),
    )

    width_unit: Optional[str] = element(
        description="Unit of width",
        default=None,
        tag="width_unit",
        json_schema_extra=dict(),
    )

    area: Optional[float] = element(
        description="Area of the peak",
        default=None,
        tag="area",
        json_schema_extra=dict(),
    )

    area_unit: Optional[str] = element(
        description="Unit of area",
        default=None,
        tag="area_unit",
        json_schema_extra=dict(),
    )

    height: Optional[float] = element(
        description="Height of the peak",
        default=None,
        tag="height",
        json_schema_extra=dict(),
    )

    height_unit: Optional[str] = element(
        description="Unit of height",
        default=None,
        tag="height_unit",
        json_schema_extra=dict(),
    )

    percent_area: Optional[float] = element(
        description="Percent area of the peak",
        default=None,
        tag="percent_area",
        json_schema_extra=dict(),
    )
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="117b9dcf20afc909f806d2bcf6a15a0046ba0b7b"
    )
    _raw_xml_data: Dict = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _parse_raw_xml_data(self):
        for attr, value in self:
            if isinstance(value, (ListPlus, list)) and all(
                (isinstance(i, _Element) for i in value)
            ):
                self._raw_xml_data[attr] = [elem2dict(i) for i in value]
            elif isinstance(value, _Element):
                self._raw_xml_data[attr] = elem2dict(value)
        return self
