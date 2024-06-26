from typing import Dict, Optional
from uuid import uuid4

import sdRDM
from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict


@forge_signature
class Valve(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    name: Optional[str] = element(
        description="Name of the valve",
        default=None,
        tag="name",
        json_schema_extra=dict(),
    )

    loop_volume: Optional[float] = element(
        description="Loop volume of the valve",
        default=None,
        tag="loop_volume",
        json_schema_extra=dict(),
    )

    load_time: Optional[float] = element(
        description="Load time",
        default=None,
        tag="load_time",
        json_schema_extra=dict(),
    )

    inject_time: Optional[float] = element(
        description="Inject time",
        default=None,
        tag="inject_time",
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
