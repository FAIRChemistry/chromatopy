from ast import Tuple
import sdRDM

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.base.datatypes import Unit
from sdRDM.tools.utils import elem2dict
from datetime import datetime as Datetime

from chromatopy.readers.abstractreader import AbstractReader
from .molecule import Molecule
from .method import Method
from .measurement import Measurement
from .chromatogram import Chromatogram
from .role import Role
from .signaltype import SignalType
from .peak import Peak


@forge_signature
class ChromatigraphicExperiment(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    method: Optional[Method] = element(
        description="Description of the HPLC method",
        default_factory=Method,
        tag="method",
        json_schema_extra=dict(),
    )

    molecules: Optional[Molecule] = element(
        description="Molecule that can be assigned to a peak.",
        default_factory=Molecule,
        tag="molecules",
        json_schema_extra=dict(),
    )

    measurements: List[Measurement] = element(
        description="Measured signals",
        default_factory=ListPlus,
        tag="measurements",
        json_schema_extra=dict(multiple=True),
    )
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="5dbbb3efba145cf71128e1f754ece504f2d77f52"
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

    def add_to_measurements(
        self,
        chromatograms: List[Chromatogram] = ListPlus(),
        timestamp: Optional[Datetime] = None,
        injection_volume: Optional[float] = None,
        injection_volume_unit: Optional[Unit] = None,
        id: Optional[str] = None,
    ) -> Measurement:
        """
        This method adds an object of type 'Measurement' to attribute measurements

        Args:
            id (str): Unique identifier of the 'Measurement' object. Defaults to 'None'.
            chromatograms (): Measured signal. Defaults to ListPlus()
            timestamp (): Timestamp of sample injection into the column. Defaults to None
            injection_volume (): Injection volume. Defaults to None
            injection_volume_unit (): Unit of injection volume. Defaults to None
        """
        params = {
            "chromatograms": chromatograms,
            "timestamp": timestamp,
            "injection_volume": injection_volume,
            "injection_volume_unit": injection_volume_unit,
        }
        if id is not None:
            params["id"] = id
        self.measurements.append(Measurement(**params))
        return self.measurements[-1]

    def add_analyte(
        self,
        name: str,
        retention_time: float,
        molecular_weight: float = None,
        inchi: str = None,
        tolerance: float = 0.1,
    ) -> Molecule:

        analyte = self._set_molecule(
            name=name,
            retention_time=retention_time,
            role=Role.ANALYTE,
            molecular_weight=molecular_weight,
            inchi=inchi,
            tolerance=tolerance,
        )

        self.analytes[name] = analyte

        return analyte

    def _set_molecule(
        self,
        name: str,
        retention_time: float,
        role: Role,
        molecular_weight: float = None,
        concentrations: float = None,
        signals: float = None,
        concentration_unit: str = None,
        inchi: str = None,
        tolerance: float = 0.1,
        detector: SignalType = "fid",
    ):

        times, peaks = self._get_peaks_by_retention_time(
            retention_time=retention_time, tolerance=tolerance, detector=detector
        )

        molecule = Molecule(
            name=name,
            inchi=inchi,
            retention_time=retention_time,
            molecular_weight=molecular_weight,
            times=times,
            peaks=peaks,
            role=role,
        )

        if concentrations is not None and signals is not None:
            molecule = self._add_standard_to_molecule(
                molecule=molecule,
                concentrations=concentrations,
                signals=signals,
                concentration_unit=concentration_unit,
            )

        return molecule

    def _get_peaks_by_retention_time(
        self,
        retention_time: float,
        tolerance: float = 0.1,
        detector: SignalType = "fid",
    ) -> "Tuple[List[datetime], List[Peak]]":

        lower_ret = retention_time - tolerance
        upper_ret = retention_time + tolerance

        times = []
        peaks = []

        for measurement in self.measurements:

            print(detector)

            time = measurement.timestamp

            detector_signals = measurement.get(
                path="chromatograms", attribute="type", target=detector
            )[0]

            peaks_in_retention_interval = [
                peak
                for peak in detector_signals.peaks
                if lower_ret < peak.retention_time < upper_ret
            ]

            if len(peaks_in_retention_interval) == 1:
                times.append(time)
                peaks.append(peaks_in_retention_interval[0])

            elif len(peaks_in_retention_interval) == 0:
                continue

            else:
                raise ValueError(
                    f"Multiple {len(peaks_in_retention_interval)} peaks found within"
                    f"retention time interval [{lower_ret} : {upper_ret}]"
                )

        assert len(times) == len(peaks)
        return times, peaks

    @classmethod
    def read(cls, path: str, reader: AbstractReader):
        """Reads in data from file or direcotry"""

        measurements = reader(path).read()
        data = {"measurements": measurements}

        return cls(**data)
