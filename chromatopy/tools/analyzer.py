import warnings
from typing import List

from pydantic import BaseModel, Field

from chromatopy.core import (
    Chromatogram,
    Measurement,
    Peak,
    SignalType,
)
from chromatopy.readers import ChromReader
from chromatopy.tools.calibration import Calibrator
from chromatopy.tools.species import Species


class ChromAnalyzer(BaseModel):
    calibrators: List[Calibrator] = Field(
        description="List of calibrators to be used for calibration",
        default_factory=list,
    )

    species: List[Species] = Field(
        description="List of species present in the measurements",
        default_factory=list,
    )

    measurements: List[Measurement] = Field(
        description="List of measurements to be analyzed",
        default_factory=list,
    )

    @classmethod
    def read_data(cls, path: str):
        return cls(
            measurements=ChromReader.read(path),
        )

    def add_reaction_time(self, reaction_times: List[float], unit: str):
        """Add reation times to the measurements.

        Args:
            reaction_times (List[float]): List of reaction times corresponding to the measurements.
        """
        assert len(reaction_times) == len(self.measurements), (
            f"Length of reaction time {len(reaction_times)} does not match"
            f" length of measurements {len(self.measurements)}."
        )

        for measurement, reaction_time in zip(self.measurements, reaction_times):
            measurement.reaction_time = reaction_time
            measurement.time_unit = unit

    def reaction_time_from_injection_time(self):
        """Calculate reaction times from the injection time between measurements."""
        timestamps = [measurement.timestamp for measurement in self.measurements]
        reaction_times = [
            (timestamp - timestamps[0]).total_seconds() for timestamp in timestamps
        ]

        self.add_reaction_time(reaction_times)

    def add_species(
        self,
        name: str,
        chebi: int = None,
        retention_time: float = None,
        reaction_times: List[float] = [],
        init_conc: float = None,
        conc_unit: str = None,
        time_unit: str = None,
        detector: SignalType = None,
        tolerance: float = 0.1,
        uniprot_id: str = None,
        sequence: str = None,
        molecular_weight: float = None,
    ) -> Species:
        detector = self._handel_detector(detector)

        if retention_time:
            peaks = self._get_peaks_by_retention_time(
                retention_time=retention_time, tolerance=tolerance, detector=detector
            )
            print(
                f"🏔️ Assigned {len(peaks)} peaks to {name} at {retention_time} ± {tolerance} min."
            )

        if reaction_times:
            assert len(reaction_times) == len(peaks), (
                f"Length of reaction time {len(reaction_times)} does not match"
                f" length of peaks {len(peaks)}."
            )

        analyte = Species(
            name=name,
            chebi=chebi,
            retention_time=retention_time,
            init_conc=init_conc,
            conc_unit=conc_unit,
            uniprot_id=uniprot_id,
            reaction_times=reaction_times,
            reacton_time_unit=time_unit,
            molecular_weight=molecular_weight,
            sequence=sequence,
            peaks=peaks,
        )

        self.species.append(analyte)

        return analyte

    def _handel_detector(self, detector: SignalType):
        """
        Handles the detector selection for the given SignalType.
        If only one detector is found in a measurement, it is selected.

        Args:
            detector (SignalType): The type of detector to handle.

        Returns:
            SignalType: The selected detector.

        Raises:
            ValueError: If data from multiple detectors is found and no specific detector is specified.

        """
        detectors = list(
            set(
                [
                    chomatogram.type
                    for measurement in self.measurements
                    for chomatogram in measurement.chromatograms
                ]
            )
        )

        if detector in detectors:
            return detector
        if all(detector == detectors[0] for detector in detectors):
            return detectors[0]

        raise ValueError(
            "Data from multiple detectors found. Please specify detector."
            f" {list(set(detectors))}"
        )

    def _get_peaks_by_retention_time(
        self,
        retention_time: float,
        detector: SignalType,
        tolerance: float = 0.1,
    ) -> List[Peak]:
        """
        Returns a list of peaks within a specified retention time interval.

        Args:
            chromatogram (Chromatogram): The chromatogram object containing the peaks.
            lower_retention_time (float): The lower bound of the retention time interval.
            upper_retention_time (float): The upper bound of the retention time interval.

        Returns:
            List[Peak]: A list of peaks within the specified retention time interval.
        """

        lower_ret = retention_time - tolerance
        upper_ret = retention_time + tolerance

        peaks = []

        for measurement in self.measurements:
            chromatogram = measurement.get_detector(detector)

            peaks_in_retention_interval = self._get_peaks_in_retention_interval(
                chromatogram=chromatogram,
                lower_retention_time=lower_ret,
                upper_retention_time=upper_ret,
            )

            if len(peaks_in_retention_interval) == 1:
                peaks.append(peaks_in_retention_interval[0])

            elif len(peaks_in_retention_interval) == 0:
                warnings.warn(
                    "No peak annotated within retention time interval"
                    f" [{lower_ret:.2f} : {upper_ret:.2f}] for masurement at"
                    f" {measurement.timestamp} from {detector} found. Skipping measurement."
                )

            else:
                raise ValueError(
                    f"Multiple {len(peaks_in_retention_interval)} peaks found within"
                    f"retention time interval [{lower_ret} : {upper_ret}]"
                )

        return peaks

    def _get_peaks_in_retention_interval(
        self,
        chromatogram: Chromatogram,
        lower_retention_time: float,
        upper_retention_time: float,
    ) -> List[Peak]:
        return [
            peak
            for peak in chromatogram.peaks
            if lower_retention_time < peak.retention_time < upper_retention_time
        ]
