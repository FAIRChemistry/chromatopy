import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator

from datetime import datetime as Datetime

from .molecule import Molecule
from .signal import Signal
from .measurement import Measurement
from .method import Method


@forge_signature
class HPLCExperiment(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("hplcexperimentINDEX"),
        xml="@id",
    )

    method: Optional[Method] = Field(
        default=Method(),
        description="Description of the HPLC method",
    )

    molecules: Optional[Molecule] = Field(
        default=Molecule(),
        description="Molecule which can be assigned to a peak.",
    )

    measurements: List[Measurement] = Field(
        description="Measured signals",
        default_factory=ListPlus,
        multiple=True,
    )

    def add_to_measurements(
        self,
        signals: List[Signal] = ListPlus(),
        timestamp: Optional[Datetime] = None,
        injection_volume: Optional[float] = None,
        injection_volume_unit: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        """
        This method adds an object of type 'Measurement' to attribute measurements

        Args:
            id (str): Unique identifier of the 'Measurement' object. Defaults to 'None'.
            signals (): Measured signal. Defaults to ListPlus()
            timestamp (): Timestamp of sample injection into the column. Defaults to None
            injection_volume (): Injection volume. Defaults to None
            injection_volume_unit (): Unit of injection volume. Defaults to None
        """

        params = {
            "signals": signals,
            "timestamp": timestamp,
            "injection_volume": injection_volume,
            "injection_volume_unit": injection_volume_unit,
        }

        if id is not None:
            params["id"] = id

        self.measurements.append(Measurement(**params))

        return self.measurements[-1]
