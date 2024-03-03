
from typing import Dict, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict
from .detector import Detector


@forge_signature
class TCDDetector(Detector):
    """Describes properties of a thermal conductivity detector."""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    hydrogen_flow: Optional[float] = element(
        description="Hydrogen flow",
        default=None,
        tag="hydrogen_flow",
        json_schema_extra=dict(),
    )

    air_flow: Optional[float] = element(
        description="Airflow",
        default=None,
        tag="air_flow",
        json_schema_extra=dict(),
    )

    flame: Optional[bool] = element(
        description="Flame on/off",
        default=None,
        tag="flame",
        json_schema_extra=dict(),
    )

    electrometer: Optional[bool] = element(
        description="Electrometer on/off",
        default=None,
        tag="electrometer",
        json_schema_extra=dict(),
    )

    lit_offset: Optional[float] = element(
        description="Lit offset",
        default=None,
        tag="lit_offset",
        json_schema_extra=dict(),
    )
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="e644bb97567b9f707760537f4d4df61a48a9a29a"
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
