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
class Inlet(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    mode: Optional[str] = element(
        description="Mode of the inlet (Split / Splitless)",
        default=None,
        tag="mode",
        json_schema_extra=dict(),
    )

    init_temp: Optional[float] = element(
        description="Initial temperature",
        default=None,
        tag="init_temp",
        json_schema_extra=dict(),
    )

    pressure: Optional[float] = element(
        description="Inlet pressure",
        default=None,
        tag="pressure",
        json_schema_extra=dict(),
    )

    pressure_unit: Optional[Unit] = element(
        description="Unit of pressure",
        default=None,
        tag="pressure_unit",
        json_schema_extra=dict(),
    )

    split_ratio: Optional[str] = element(
        description="Split ratio",
        default=None,
        tag="split_ratio",
        json_schema_extra=dict(regex="(d+)(:)(d+)"),
    )

    split_flow: Optional[float] = element(
        description="Split flow",
        default=None,
        tag="split_flow",
        json_schema_extra=dict(),
    )

    total_flow: Optional[float] = element(
        description="Total flow",
        default=None,
        tag="total_flow",
        json_schema_extra=dict(),
    )

    flow_unit: Optional[Unit] = element(
        description="Unit of flow",
        default=None,
        tag="flow_unit",
        json_schema_extra=dict(),
    )

    gas_saver: Optional[bool] = element(
        description="Gas saver mode",
        default=None,
        tag="gas_saver",
        json_schema_extra=dict(),
    )

    gas_type: Optional[str] = element(
        description="Type of gas",
        default=None,
        tag="gas_type",
        json_schema_extra=dict(),
    )
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="10cacc0f6eea0feefa9a3bc7a4b4e90ee75bd03f"
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
