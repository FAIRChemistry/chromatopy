from typing import List, Tuple
from datetime import datetime

from HPLC.core.hplcexperiment import HPLCExperiment
from HPLC.core.molecule import Molecule
from HPLC.core.peak import Peak
from HPLC.core.signal import Signal
from HPLC.core.signaltype import SignalType


class HPLCAnalyzer:

    def __init__(self, data: HPLCExperiment):
        self.data: HPLCExperiment = data
        self.molecules: List[Molecule] = []

    def addMolecule(
            self,
            name: str,
            retention_time: float,
            molecular_weight: float = None,
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
            peaks=peaks
        )

        molecule.print_name = self.print_name

        self.molecules.append(molecule)

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

    def print_name(self) -> None:
        print(self.name)
