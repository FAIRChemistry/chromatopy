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
class Standard(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    analyte_id: Optional[str] = element(
        description="ID of the analyte",
        default=None,
        tag="analyte_id",
        json_schema_extra=dict(),
    )

    factor: Optional[float] = element(
        description="Factor to convert the signal to concentration",
        default=None,
        tag="factor",
        json_schema_extra=dict(),
    )

    intercept: Optional[float] = element(
        description="Intercept of the standard curve",
        default=None,
        tag="intercept",
        json_schema_extra=dict(),
    )

    r_squared: Optional[float] = element(
        description="R squared value of the standard curve",
        default=None,
        tag="r_squared",
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
