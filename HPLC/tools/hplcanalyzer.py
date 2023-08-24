from typing import List, Tuple, Dict
from dotted_dict import DottedDict
from datetime import datetime
from pydantic import BaseModel, Field

from HPLC.core.hplcexperiment import HPLCExperiment
from HPLC.core.molecule import Molecule
from HPLC.core.peak import Peak
from HPLC.core.role import Role
from HPLC.core.signal import Signal
from HPLC.core.standard import Standard
from HPLC.core.signaltype import SignalType


class HPLCAnalyzer(BaseModel):

    data: HPLCExperiment
    analytes: Dict[str, Molecule] = Field(default_factory=DottedDict)
    internal_standards: Dict[str, Molecule] = Field(default_factory=DottedDict)

    def add_analyte(
            self,
            name: str,
            retention_time: float,
            molecular_weight: float = None,
            inchi: str = None,
            tolerance: float = 0.1,
            detector: SignalType = "fid"
    ) -> Molecule:

        analyte = self._set_molecule(
            name=name,
            retention_time=retention_time,
            role=Role.ANALYTE,
            molecular_weight=molecular_weight,
            inchi=inchi,
            tolerance=tolerance,
            detector=detector
        )

        self.analytes[name] = analyte

        return analyte

    def add_internal_standard(
            self,
            name: str,
            retention_time: float,
            concentrations: List[float],
            signals: List[float],
            molecular_weight: float,
            inchi: str = None,
            tolerance: float = 0.1,
            detector: SignalType = "fid"
    ) -> Molecule:

        internal_standard = self._set_molecule(
            name=name,
            retention_time=retention_time,
            concentrations=concentrations,
            signals=signals,
            role=Role.INTERNAL_STANDARD,
            molecular_weight=molecular_weight,
            inchi=inchi,
            tolerance=tolerance,
            detector=detector
        )

        self.internal_standards[name] = internal_standard

        return internal_standard

    def calculate_concentrations(
            self,
            analytes: List[Molecule] = None,
            internal_standard: Molecule = None,
    ):

        if analytes is None:
            analytes = self.analytes.values()
        if isinstance(analytes, Molecule):
            analytes = [analytes]

        # if one internal standard is defined, it is used for all analytes
        if internal_standard is None and len(self.internal_standards.keys()) == 1:
            internal_standard = next(iter(self.internal_standards.values()))

        if internal_standard.role is not Role.INTERNAL_STANDARD.value:
            raise ValueError(
                f"Internal standard {internal_standard.name} is not an internal standard"
            )

        for analyte in self.analytes.values():
            analyte.calculate_concentrations(
                internal_standard=internal_standard)

    def _analytes_to_dataframe(self, analytes: List[Molecule] = None):

        if analytes is None:
            analytes = self.analytes.values()
        if isinstance(analytes, Molecule):
            analytes = [analytes]

        for analyte in analytes:
            print(analyte.to_dict())

    def visualize(
            self,
            analytes: List[Molecule] = None,
    ):
        if analytes is None:
            analytes = self.analytes.values()
        if isinstance(analytes, Molecule):
            analytes = [analytes]

        for analyte in analytes:
            pass

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
            detector: SignalType = "fid"
    ):

        times, peaks = self._get_peaks_by_retention_time(
            retention_time=retention_time,
            tolerance=tolerance,
            detector=detector
        )

        molecule = Molecule(
            name=name,
            inchi=inchi,
            retention_time=retention_time,
            molecular_weight=molecular_weight,
            times=times,
            peaks=peaks,
            role=role
        )

        if concentrations is not None and signals is not None:
            molecule = self._add_standard_to_molecule(
                molecule=molecule,
                concentrations=concentrations,
                signals=signals,
                concentration_unit=concentration_unit
            )

        return molecule

    @staticmethod
    def _add_standard_to_molecule(
        molecule: Molecule,
        concentrations: List[float],
        signals: List[float],
        concentration_unit: str
    ):

        assert len(concentrations) == len(signals)

        molecule.standard = Standard(
            concentration=concentrations,
            signal=signals,
            concentration_unit=concentration_unit
        )

        return molecule

    def _get_peaks_by_retention_time(
        self,
        retention_time: float,
        tolerance: float = 0.1,
        detector: SignalType = "fid",
    ) -> Tuple[List[datetime], List[Peak]]:

        lower_ret = retention_time - tolerance
        upper_ret = retention_time + tolerance

        times = []
        peaks = []

        for measurement in self.data.measurements:

            time = measurement.timestamp

            detector_signals = measurement.get(
                path="signals",
                attribute="type",
                target=detector
            )[0][0]

            peaks_in_retention_interval = [
                peak for peak in detector_signals.peaks
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
    def from_directory(cls, path: str):
        pass
