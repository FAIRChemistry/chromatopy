import sdRDM

from typing import Dict, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.base.datatypes import Unit
from sdRDM.tools.utils import elem2dict


@forge_signature
class Detector(sdRDM.DataModel):
    """Base class for detectors."""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
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
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="371223791b951fed8b47aa4129c84c4e7d5f82aa"
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
