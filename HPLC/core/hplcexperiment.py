import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator


from .signal import Signal
from .method import Method
from .oven import Oven
from .valve import Valve
from .peak import Peak
from .signaltype import SignalType
from .column import Column


@forge_signature
class HPLCExperiment(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("hplcexperimentINDEX"),
        xml="@id",
    )

    methods: List[Method] = Field(
        description="Description of the HPLC method",
        default_factory=ListPlus,
        multiple=True,
    )

    signals: List[Signal] = Field(
        description="Measured signals",
        default_factory=ListPlus,
        multiple=True,
    )

    def add_to_methods(
        self,
        injection_time: Optional[float] = None,
        injection_date: Optional[str] = None,
        injection_volume: Optional[float] = None,
        injection_volume_unit: Optional[str] = None,
        location: Optional[str] = None,
        oven: Optional[Oven] = None,
        columns: List[Column] = ListPlus(),
        valves: List[Valve] = ListPlus(),
        id: Optional[str] = None,
    ) -> None:
        """
        This method adds an object of type 'Method' to attribute methods

        Args:
            id (str): Unique identifier of the 'Method' object. Defaults to 'None'.
            injection_time (): Injection time. Defaults to None
            injection_date (): Injection date. Defaults to None
            injection_volume (): Injection volume. Defaults to None
            injection_volume_unit (): Unit of injection volume. Defaults to None
            location (): Location of sample vial. Defaults to None
            oven (): Settings of the oven. Defaults to None
            columns (): Parameters of the columns. Defaults to ListPlus()
            valves (): Settings of the valves. Defaults to ListPlus()
        """

        params = {
            "injection_time": injection_time,
            "injection_date": injection_date,
            "injection_volume": injection_volume,
            "injection_volume_unit": injection_volume_unit,
            "location": location,
            "oven": oven,
            "columns": columns,
            "valves": valves,
        }

        if id is not None:
            params["id"] = id

        self.methods.append(Method(**params))

        return self.methods[-1]

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
