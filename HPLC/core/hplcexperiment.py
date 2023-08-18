import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator

from datetime import datetime as Datetime

from .measurement import Measurement
from .method import Method
from .molecule import Molecule
from .peak import Peak
from .signal import Signal


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

    molecules: List[Molecule] = Field(
        default_factory=ListPlus,
        multiple=True,
        description="Results of",
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

    def add_to_molecules(
        self,
        name: Optional[str] = None,
        inchi: Optional[str] = None,
        molecular_weight: Optional[float] = None,
        retention_time: Optional[float] = None,
        times: List[Datetime] = ListPlus(),
        peaks: List[Peak] = ListPlus(),
        concentration: List[float] = ListPlus(),
        id: Optional[str] = None,
    ) -> None:
        """
        This method adds an object of type 'Molecule' to attribute molecules

        Args:
            id (str): Unique identifier of the 'Molecule' object. Defaults to 'None'.
            name (): Molecule name. Defaults to None
            inchi (): Inchi code of the molecule. Defaults to None
            molecular_weight (): Molar weight of the molecule in g/mol. Defaults to None
            retention_time (): Approximated retention time of the molecule. Defaults to None
            times (): Time points when the molecule concentration was measured. Defaults to ListPlus()
            peaks (): All peaks of the dataset which are within the same retention time interval. Defaults to ListPlus()
            concentration (): Concentration of the molecule. Defaults to ListPlus()
        """

        params = {
            "name": name,
            "inchi": inchi,
            "molecular_weight": molecular_weight,
            "retention_time": retention_time,
            "times": times,
            "peaks": peaks,
            "concentration": concentration,
        }

        if id is not None:
            params["id"] = id

        self.molecules.append(Molecule(**params))

        return self.molecules[-1]
