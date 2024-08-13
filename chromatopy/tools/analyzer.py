import glob
import os
import warnings
from collections import defaultdict
from typing import List, Literal, Tuple

import pandas as pd
import plotly.graph_objects as go
from calipytion.model import Standard
from calipytion.tools import Calibrator
from pydantic import BaseModel, Field

from chromatopy.model import (
    Chromatogram,
    Measurement,
    Peak,
    SignalType,
    UnitDefinition,
)
from chromatopy.tools.fit_chromatogram import ChromFit
from chromatopy.tools.molecule import Molecule
from chromatopy.units import min


class ChromAnalyzer(BaseModel):
    id: str = Field(
        description="Unique identifier of the given object",
    )

    standards: List[Standard] = Field(
        description="List of calibrators to be used for calibration",
        default_factory=list,
    )

    molecules: List[Molecule] = Field(
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
        experiment_id: str,
        path: str,
        wavelength: float,
        detector: str,
        time_unit: str = min,
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
            time_unit=time_unit,
            type=detector,
        )

        return cls(id=experiment_id, measurements=[measurement])

    @classmethod
    def read_chromeleon(cls, dir_path: str):
        from chromatopy.readers.chromeleon import read_chromeleon_file

        txt_files = glob.glob(os.path.join(dir_path, "*.txt"))
        txt_files.sort()

        measurements = [read_chromeleon_file(file) for file in txt_files]

        return cls(id=dir_path, measurements=measurements)

    def find_peaks(self, **fitting_kwargs):
        print(
            f"🔍 Processing signal and integrating peaks for {len(self.measurements)} chromatograms."
        )
        fitting_kwargs["verbose"] = False
        for measurement in self.measurements:
            fitter = ChromFit(
                measurement.chromatograms[0].signals,
                measurement.chromatograms[0].times,
            )
            fitter.fit(**fitting_kwargs)
            measurement.chromatograms[0].peaks = fitter.peaks

    def add_standard(
        self,
        molecule: Molecule,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition,
        concentrations: list[float],
        conc_unit: UnitDefinition,
        model: Literal["linear", "quadratic", "cubic"] = "linear",
        visualize: bool = False,
    ):
        from calipytion.model import UnitDefinition as CalUnitDefinition

        assert (
            len(molecule.peaks) == len(concentrations)
        ), f"Number of peaks {len(molecule.peaks)} does not match number of concentrations {len(concentrations)}."

        calibrator = Calibrator(
            molecule_id=molecule.id,
            molecule_name=molecule.name,
            concentrations=concentrations,
            conc_unit=CalUnitDefinition(**conc_unit.model_dump()),
            signals=[peak.area for peak in molecule.peaks],
        )
        calibrator.models = []
        calibrator.add_model(
            name="linear",
            signal_law=f"a*{molecule.id} + b",
        )
        calibrator.fit_models()

        model_obj = calibrator.get_model(model)

        if visualize:
            calibrator.visualize()

        standard = calibrator.create_standard(
            model=model_obj,
            ph=ph,
            temperature=temperature,
            temp_unit=CalUnitDefinition(**temperature_unit.model_dump()),
            retention_time=molecule.retention_time,
        )

        self.standards.append(standard)

        print(f"📏 Added standard {molecule.name}")

        return standard

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

    def add_molecule(
        self,
        id: str,
        name: str,
        ld_id: str = None,
        chebi: int = None,
        retention_time: float = None,
        reaction_times: List[float] = [],
        init_conc: float = None,
        conc_unit: str = None,
        time_unit: str = None,
        detector: SignalType = None,
        tolerance: float = 0.2,
        uniprot_id: str = None,
        sequence: str = None,
        molecular_weight: float = None,
    ) -> Molecule:
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

        analyte = Molecule(
            id=id,
            name=name,
            chebi=chebi,
            ld_id=ld_id,
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

        self.molecules.append(analyte)

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
        tolerance: float = 0.2,
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
            chromatogram = measurement.chromatograms[0]

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
        for species in self.molecules:
            if species.reaction_times:
                return species.reaction_times, species.time_unit
            else:
                raise AttributeError("No information on reaction time found.")

    def _get_data_conditions(self) -> Tuple[dict, dict]:
        data = {}
        conditions = {}

        for species in self.molecules:
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

        if not self.molecules:
            raise ValueError("No species provided. Define species first.")

        for calibrator in self.calibrators:
            calib_species = self.get_molecule(calibrator.name)
            if not calib_species.peaks:
                continue

            calib_species.concentrations = calibrator.calculate(species=calib_species)

    def get_molecule(self, id: str | int) -> Molecule:
        try:
            return next(molecule for molecule in self.molecules if molecule.chebi == id)
        except StopIteration:
            try:
                return next(
                    molecule for molecule in self.molecules if molecule.name == id
                )
            except StopIteration:
                try:
                    return next(
                        molecule
                        for molecule in self.molecules
                        if molecule.uniprot_id == id
                    )
                except StopIteration:
                    raise ValueError(f"Species with id {id} not found.")

    def to_csv(self, path: str):
        self._create_df().to_csv(path)

    def visualize(self) -> go.Figure:
        """
        Plot the chromatogram.

        This method creates a plot of the chromatogram using the plotly library.
        It adds a scatter trace for the retention times and signals, and if there are peaks present, it adds vertical lines for each peak.

        Returns:
            go.Figure: The plotly figure object.
        """
        fig = go.Figure()
        for meas in self.measurements:
            chrom = meas.chromatograms[0]
            fig.add_trace(
                go.Scatter(
                    x=chrom.times,
                    y=chrom.signals,
                    name=meas.id,
                )
            )

            if chrom.peaks:
                for peak in chrom.peaks:
                    fig.add_vline(
                        x=peak.retention_time,
                        line_dash="dash",
                        line_color="gray",
                        annotation_text=peak.retention_time,
                    )

            if chrom.processed_signal:
                fig.add_trace(
                    go.Scatter(
                        x=chrom.times,
                        y=chrom.processed_signal,
                        mode="lines",
                        line=dict(dash="dot", width=1),
                        name="Processed signal",
                    )
                )

        if chrom.wavelength:
            wave_string = f"({chrom.wavelength} nm)"
        else:
            wave_string = ""

        fig.update_layout(
            xaxis_title="Retention time / min",
            yaxis_title=f"Signal {wave_string}",
            height=600,
        )

        fig.show()

    def plot_concentrations(self):
        df = self._create_df()

        fig = go.Figure()

        for species in self.molecules:
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
            xaxis_title="time (min)",
            yaxis_title=f"concentration ({conc_unit})",
            margin=dict(l=0, r=0, b=0, t=30),
            plot_bgcolor="white",
        )

        fig.show()

    def apply_standards(self, tolerance: float = 1):
        data = defaultdict(list)

        for standard in self.standards:
            lower_ret = standard.retention_time - tolerance
            upper_ret = standard.retention_time + tolerance
            calibrator = Calibrator.from_standard(standard)
            model = calibrator.models[0]

            for meas in self.measurements:
                for chrom in meas.chromatograms:
                    for peak in chrom.peaks:
                        if lower_ret < peak.retention_time < upper_ret:
                            data[standard.molecule_name].append(
                                calibrator.calculate_concentrations(
                                    model=model, signals=[peak.area]
                                )[0]
                            )

        return data


if __name__ == "__main__":
    from devtools import pprint

    from chromatopy.units import mM

    dir_path = "/Users/max/Documents/jan-niklas/MjNK/guanosine_std"
    file_path = (
        "/Users/max/Documents/jan-niklas/MjNK/Standards/Adenosine Stadards_ 0.5 mM.txt"
    )

    data_path = "/Users/max/Documents/jan-niklas/MjNK"

    data_ana = ChromAnalyzer.read_chromeleon(data_path)

    ana = ChromAnalyzer.read_chromeleon(dir_path)
    del ana.measurements[0]

    ana.find_peaks()

    ana.add_molecule(
        ld_id="www.mol.com",
        id="s0",
        name="Guanosine",
        retention_time=6.03,
    )

    print(ana.molecules)

    # find and fit peaks

    # scatterplot as multiplot for each measurement

    # for meas in ana.measurements[1:]:
    #     for chrom in meas.chromatograms:
    #         chrom.fit()

    # from matplotlib import pyplot as plt

    # plt.plot(
    #     ana.measurements[0].chromatograms[0].times,
    #     ana.measurements[0].chromatograms[0].signals,
    # )
    # plt.plot(
    #     ana.measurements[1].chromatograms[0].times,
    #     ana.measurements[1].chromatograms[0].signals,
    # )
    # plt.plot(
    #     ana.measurements[2].chromatograms[0].times,
    #     ana.measurements[2].chromatograms[0].signals,
    # )
    # plt.show()

    from chromatopy.units import C

    stan = ana.add_standard(
        ana.molecules[0], 7.4, 37, C, [0.5, 1, 1.5, 2, 2.5], mM, visualize=True
    )
    pprint(stan)
