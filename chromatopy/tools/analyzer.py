import warnings
from typing import List

from pydantic import BaseModel, Field

from chromatopy.core import (
    Analyte,
    Chromatogram,
    Measurement,
    Peak,
    Role,
    SignalType,
    Standard,
)
from chromatopy.readers import ChromReader


class ChromAnalyzer(BaseModel):
    analytes: List[Analyte] = Field(
        description="List of analytes to be analyzed",
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

    def add_analyte(
        self,
        name: str,
        retention_time: float,
        detector: SignalType = None,
        molecular_weight: float = None,
        inchi: str = None,
        tolerance: float = 0.1,
        calibration_factor: float = None,
    ) -> Analyte:
        """
        This method adds an object of type 'Analyte' to the 'analytes' attribute.

        Args:
            name (str): Name of the analyte.
            retention_time (float): Approximated retention time of the molecule.
            detector (SignalType, optional): The type of detector used.
                Defaults to None.
            molecular_weight (float, optional): Molar weight of the molecule in g/mol.
                Defaults to None.
            inchi (str, optional): InCHI code of the molecule.
                Defaults to None.
            tolerance (float, optional): Tolerance for the retention time. Defaults to 0.1.
            calibration_factor (float, optional): Calibration factor in with respect to internal standard.

        Returns:
            Analyte: The added Analyte object.
        """
        detector = self._handel_detector(detector)

        analyte = self._set_analyte(
            name=name,
            retention_time=retention_time,
            role=Role.ANALYTE,
            molecular_weight=molecular_weight,
            inchi=inchi,
            tolerance=tolerance,
            detector=detector,
            calibration_factor=calibration_factor,
        )

        self.analytes.append(analyte)

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

    def _set_analyte(
        self,
        name: str,
        retention_time: float,
        role: Role,
        detector: SignalType,
        tolerance: float,
        molecular_weight: float = None,
        inchi: str = None,
        calibration_factor: float = None,
    ):
        peaks = self._get_peaks_by_retention_time(
            retention_time=retention_time, tolerance=tolerance, detector=detector
        )

        analyte = Analyte(
            name=name,
            inchi=inchi,
            retention_time=retention_time,
            molecular_weight=molecular_weight,
            peaks=peaks,
            timestamp=[measurement.timestamp for measurement in self.measurements],
            role=role,
        )

        if calibration_factor is not None:
            analyte.standard = Standard(factor=calibration_factor)

        return analyte

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
