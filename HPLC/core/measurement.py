import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator

from datetime import datetime as Datetime

from .peak import Peak
from .signaltype import SignalType
from .signal import Signal


@forge_signature
class Measurement(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("measurementINDEX"),
        xml="@id",
    )

    signals: List[Signal] = Field(
        description="Measured signal",
        default_factory=ListPlus,
        multiple=True,
    )

    timestamp: Optional[Datetime] = Field(
        default=None,
        description="Timestamp of sample injection into the column",
    )

    injection_volume: Optional[float] = Field(
        default=None,
        description="Injection volume",
    )

    injection_volume_unit: Optional[str] = Field(
        default=None,
        description="Unit of injection volume",
    )

    def add_to_signals(
        self,
        peaks: List[Peak] = ListPlus(),
        type: Optional[SignalType] = None,
        id: Optional[str] = None,
    ) -> None:
        """
        This method adds an object of type 'Signal' to attribute signals

        Args:
            id (str): Unique identifier of the 'Signal' object. Defaults to 'None'.
            peaks (): Peaks in the signal. Defaults to ListPlus()
            type (): Type of signal. Defaults to None
        """

        params = {
            "peaks": peaks,
            "type": type,
        }

        if id is not None:
            params["id"] = id

        self.signals.append(Signal(**params))

        return self.signals[-1]
