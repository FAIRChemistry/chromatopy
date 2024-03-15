
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
class FIDDetector(Detector):
    """Describes properties of a flame ionization detector."""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    reference_flow: Optional[float] = element(
        description="Reference flow",
        default=None,
        tag="reference_flow",
        json_schema_extra=dict(),
    )

    filament: Optional[bool] = element(
        description="Filament on/off",
        default=None,
        tag="filament",
        json_schema_extra=dict(),
    )

    negative_polarity: Optional[bool] = element(
        description="Negative polarity on/off",
        default=None,
        tag="negative_polarity",
        json_schema_extra=dict(),
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
