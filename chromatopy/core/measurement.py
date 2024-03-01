import sdRDM

from typing import Dict, List, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict
from datetime import datetime as Datetime
from .signal import Signal
from .peak import Peak
from .signaltype import SignalType


@forge_signature
class Measurement(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    signals: List[Signal] = element(
        description="Measured signal",
        default_factory=ListPlus,
        tag="signals",
        json_schema_extra=dict(multiple=True),
    )

    timestamp: Optional[Datetime] = element(
        description="Timestamp of sample injection into the column",
        default=None,
        tag="timestamp",
        json_schema_extra=dict(),
    )

    injection_volume: Optional[float] = element(
        description="Injection volume",
        default=None,
        tag="injection_volume",
        json_schema_extra=dict(),
    )

    injection_volume_unit: Optional[str] = element(
        description="Unit of injection volume",
        default=None,
        tag="injection_volume_unit",
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

    def add_to_signals(
        self,
        peaks: List[Peak] = ListPlus(),
        type: Optional[SignalType] = None,
        id: Optional[str] = None,
    ) -> Signal:
        """
        This method adds an object of type 'Signal' to attribute signals

        Args:
            id (str): Unique identifier of the 'Signal' object. Defaults to 'None'.
            peaks (): Peaks in the signal. Defaults to ListPlus()
            type (): Type of signal. Defaults to None
        """
        params = {"peaks": peaks, "type": type}
        if id is not None:
            params["id"] = id
        self.signals.append(Signal(**params))
        return self.signals[-1]
