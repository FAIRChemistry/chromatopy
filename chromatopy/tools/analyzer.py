import warnings
from typing import List, Tuple

import pandas as pd
import plotly.graph_objects as go
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
    def read_csv(
        cls,
        path: str,
        wavelength: float,
        detector: str,
        **kwargs,
    ):
        detectors = [det.value for det in SignalType]
        assert detector in detectors, (
            f"Detector '{detector}' not found. Available detectors are" f" {detectors}."
        )

        df = pd.read_csv(path, **kwargs)
        col_names = df.columns

        if not len(col_names) == 2:
            raise ValueError(
                f"Expected two columns in the csv file, found {len(col_names)}.",
                "The first column should contain the time values and the second column"
                " should contain the signal values.",
            )

        measurement = Measurement(id=path)
        measurement.add_to_chromatograms(
            times=df[col_names[0]].values.tolist(),
            signals=df[col_names[1]].values.tolist(),
            wavelength=wavelength,
            type=detector,
        )

        return cls(measurements=[measurement])

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
        else:
            peaks = []

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
            time_unit=time_unit,
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

    def plot_measurements(self):
        # Create a 2D plot using Plotly
        fig = go.Figure()

        for meas in self.measurements:
            chromatogram = meas.chromatograms[
                0
            ]  # Assuming each measurement has at least one chromatogram
            x = chromatogram.times
            z = chromatogram.signals

            # Adding each chromatogram as a 2D line plot to the figure
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=z,
                    mode="lines",  # Line plot
                    name=f"{meas.id.split('/')[-1]}",
                )
            )

            # Update plot layout
        fig.update_layout(
            title="Chromatogram Plot",
            xaxis_title="Time (min)",
            yaxis_title=f"Absorbance {chromatogram.wavelength} nm",
            margin=dict(l=0, r=0, b=0, t=30),  # Adjust margins to fit layout
            plot_bgcolor="white",  # Set background to white for better visibility
        )

        # Show the plot
        fig.show()

    def _get_reaction_times(self) -> List[float]:
        for species in self.species:
            if species.reaction_times:
                return species.reaction_times, species.time_unit
            else:
                raise AttributeError("No information on reaction time found.")

    def _get_data_conditions(self) -> Tuple[dict, dict]:
        data = {}
        conditions = {}

        for species in self.species:
            if not species.concentrations:
                continue
            label = f"{species.name},{species.conc_unit._unit.to_string()}"
            data[label] = species.concentrations
            conditions[label] = species.init_conc

        return data, conditions

    def _create_df(self) -> pd.DataFrame:
        self._apply_calibrators()

        times, time_unit = self._get_reaction_times()

        data, _ = self._get_data_conditions()

        time_label = f"time,{time_unit._unit.to_string()}"
        data[time_label] = times

        return pd.DataFrame.from_dict(data).set_index(time_label)

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

    def _apply_calibrators(self):
        if not self.calibrators:
            raise ValueError("No calibrators provided. Define calibrators first.")

        if not self.species:
            raise ValueError("No species provided. Define species first.")

        for calibrator in self.calibrators:
            calib_species = self.get_species(calibrator.name)
            if not calib_species.peaks:
                continue

            calib_species.concentrations = calibrator.calculate(species=calib_species)

    def get_species(self, id: str | int) -> Species:
        try:
            return next(species for species in self.species if species.chebi == id)
        except StopIteration:
            try:
                return next(species for species in self.species if species.name == id)
            except StopIteration:
                try:
                    return next(
                        species for species in self.species if species.uniprot_id == id
                    )
                except StopIteration:
                    raise ValueError(f"Species with id {id} not found.")

    def to_csv(self, path: str):
        self._create_df().to_csv(path)

    def plot_concentrations(self):
        df = self._create_df()

        fig = go.Figure()

        for species in self.species:
            if not species.concentrations:
                continue

            time_unit = species.time_unit._unit.to_string()
            conc_unit = species.conc_unit._unit.to_string()
            fig.add_trace(
                go.Scatter(
                    x=species.reaction_times,
                    y=species.concentrations,
                    mode="markers",
                    name=f"{species.name} (initial concentration: {species.init_conc} {conc_unit}",
                )
            )

        fig.update_layout(
            xaxis_title=f"time ({time_unit})",
            yaxis_title=f"concentration ({conc_unit})",
            margin=dict(l=0, r=0, b=0, t=30),
            plot_bgcolor="white",
        )

        fig.show()


if __name__ == "__main__":
    path = "/Users/max/Documents/training_course/memeth/raw_result_folders_dotD_format"

    analyzer = ChromAnalyzer.read_data(path)
