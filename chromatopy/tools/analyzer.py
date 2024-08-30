import glob
import os
import warnings
from collections import defaultdict

import plotly.colors as pc
import plotly.graph_objects as go
from calipytion.model import Standard
from calipytion.tools import Calibrator
from calipytion.tools.utility import pubchem_request_molecule_name
from loguru import logger
from pydantic import BaseModel, Field
from pyenzyme import EnzymeMLDocument, Protein

from chromatopy.model import (
    Chromatogram,
    Measurement,
    Peak,
    SignalType,
    UnitDefinition,
)
from chromatopy.tools.fit_chromatogram import ChromFit
from chromatopy.tools.molecule import Molecule
from chromatopy.tools.utility import _resolve_chromatogram
from chromatopy.units import C, min


class ChromAnalyzer(BaseModel):
    id: str = Field(
        description="Unique identifier of the given object.",
    )

    molecules: list[Molecule] = Field(
        description="List of species present in the measurements.",
        default_factory=list,
    )

    proteins: list[Protein] = Field(
        description="List of proteins present in the measurements.",
        default_factory=list,
    )

    measurements: list[Measurement] = Field(
        description="List of measurements to be analyzed.",
        default_factory=list,
    )

    internal_standard: Molecule | None = Field(
        description="Internal standard molecule used for concentation calculation.",
        default=None,
    )

    def add_molecule_from_standard(
        self,
        standard: Standard,
        init_conc: float,
        conc_unit: UnitDefinition,
    ):
        """Adds a molecule to the list of species based on a `Standard` object."""

        molecule = Molecule.from_standard(standard, init_conc, conc_unit)

        self.add_molecule(**molecule.model_dump())

    def add_molecule(
        self,
        id: str,
        pubchem_cid: int,
        init_conc: float,
        conc_unit: UnitDefinition,
        retention_time: float,
        retention_tolerance: float = 0.2,
        name: str | None = None,
        wavelength: float | None = None,
    ):
        """Adds a molecule to the list of species.

        Args:
            id (str): Internal identifier of the molecule such as `s0` or `asd45`.
            pubchem_cid (int): PubChem CID of the molecule.
            init_conc (float): Initial concentration of the molecule at reaction start.
            conc_unit (UnitDefinition): Unit of the concentration.
            retention_time (float): Retention time tolerance for peak annotation in minutes.
            name (str | None, optional): Name of the molecule.
                If not provided, the name is retrieved from the PubChem database. Defaults to None.
        """

        if name is None:
            name = pubchem_request_molecule_name(pubchem_cid)

        molecule = Molecule(
            id=id,
            pubchem_cid=pubchem_cid,
            name=name,
            init_conc=init_conc,
            conc_unit=conc_unit,
            retention_time=retention_time,
        )

        if not self._update_molecule(molecule):
            self.molecules.append(molecule)

        self._register_peaks(molecule, retention_tolerance, wavelength)

    def define_internal_standard(
        self,
        id: str,
        pubchem_cid: int,
        name: str,
        init_conc: float,
        conc_unit: UnitDefinition,
        retention_time: float,
        retention_tolerance: float = 0.2,
        wavelength: float | None = None,
    ):
        self.internal_standard = Molecule(
            id=id,
            pubchem_cid=pubchem_cid,
            name=name,
            init_conc=init_conc,
            conc_unit=conc_unit,
            retention_time=retention_time,
        )

        self._register_peaks(
            molecule=self.internal_standard,
            ret_tolerance=retention_tolerance,
            wavelength=wavelength,
        )

    def _register_peaks(
        self,
        molecule: Molecule,
        ret_tolerance: float,
        wavelength: float | None,
    ):
        for meas in self.measurements:
            for peak in _resolve_chromatogram(meas.chromatograms, wavelength).peaks:
                if (
                    peak.retention_time - ret_tolerance
                    < molecule.retention_time
                    < peak.retention_time + ret_tolerance
                ):
                    peak.molecule_id = molecule.id
                    logger.debug(
                        f"{molecule.id} assigned as molecule ID for peak at {peak.retention_time}."
                    )

    def add_protein(
        self,
        id: str,
        name: str,
        uniprot_id: str | None = None,
        sequence: str | None = None,
        ecnumber: str | None = None,
        organism: str | None = None,
        organism_tax_id: int | None = None,
    ):
        """Adds a protein to the list of proteins or updates an existing protein
        based on the pubchem_cid of the molecule.

        Args:
            id (str): Internal identifier of the protein such as `p0` or `asd45`.
            name (str): Name of the protein.
            uniprot_id (str | None, optional): UniProt ID of the protein. Defaults to None.
            sequence (str | None, optional): Amino acid sequence of the protein. Defaults to None.
            ecnumber (str | None, optional): EC number of the protein. Defaults to None.
            organism (str | None, optional): Name of the organism the protein belongs to. Defaults to None.
            organism_tax_id (int | None, optional): NCBI Taxonomy ID of the organism. Defaults to None.
        """
        protein = Protein(
            id=id,
            name=name,
            uniprot_id=uniprot_id,
            sequence=sequence,
            ecnumber=ecnumber,
            organism=organism,
            organism_tax_id=organism_tax_id,
        )

        if not self._update_protein(protein):
            self.proteins.append(protein)

    @classmethod
    def read_agilent_csv(
        cls,
        id: str,
        path: str,
        reaction_times: list[float],
        time_unit: UnitDefinition,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition = C,
    ):
        """Reads peak data from Agilent CSV files from a directory containing *.D directories.


        Args:
            path (str): _description_
            reaction_times (list[float]): _description_
            time_unit (UnitDefinition): _description_
            ph (float): _description_
            temperature (float): _description_
            temperature_unit (UnitDefinition, optional): _description_. Defaults to C.

        Returns:
            _type_: _description_
        """
        from chromatopy.readers.agilent_csv import (
            assamble_measurements_from_agilent_csv,
        )

        measurements = assamble_measurements_from_agilent_csv(
            path=path,
            reaction_times=reaction_times,
            time_unit=time_unit,
            ph=ph,
            temperature=temperature,
            temperature_unit=temperature_unit,
        )

        return cls(id=id, measurements=measurements)

    def create_enzymeml(
        self,
        name: str,
        calculate_concentration: bool = True,
    ) -> EnzymeMLDocument:
        """Creates an EnzymeML document from the data in the ChromAnalyzer.

        Args:
            name (str): Name of the EnzymeML document.
            calculate_concentration (bool, optional): If True, the concentrations of the species
                are calculated. Defaults to True.

        Returns:
            EnzymeMLDocument: _description_
        """
        from chromatopy.ioutils.enzymeml import create_enzymeml

        return create_enzymeml(
            name=name,
            molecules=self.molecules,
            proteins=self.proteins,
            measurements=self.measurements,
            calculate_concentration=calculate_concentration,
            internal_standard=self.internal_standard,
        )

    def add_to_enzymeml(
        self,
        enzdoc: EnzymeMLDocument,
        calculate_concentration: bool = True,
    ) -> EnzymeMLDocument:
        """Adds the data from the ChromAnalyzer to an existing EnzymeML document.

        Args:
            enzdoc (EnzymeMLDocument): The EnzymeML document to which the data should be added.
            calculate_concentration (bool, optional): If True, the concentrations of the species
                are calculated. Defaults to True.

        Returns:
            EnzymeMLDocument: The updated EnzymeML document.
        """
        from chromatopy.ioutils.enzymeml import add_measurements_to_enzymeml

        return add_measurements_to_enzymeml(
            doc=enzdoc,
            new_measurements=self.measurements,
            molecules=self.molecules,
            internal_standard=self.internal_standard,
            calculate_concentration=calculate_concentration,
        )

    # @classmethod
    # def read_csv(
    #     cls,
    #     experiment_id: str,
    #     path: str,
    #     wavelength: float,
    #     detector: str,
    #     time_unit: str = min,
    #     **kwargs,
    # ):
    #     detectors = [det.value for det in SignalType]
    #     assert detector in detectors, (
    #         f"Detector '{detector}' not found. Available detectors are" f" {detectors}."
    #     )

    #     df = pd.read_csv(path, **kwargs)
    #     col_names = df.columns

    #     if not len(col_names) == 2:
    #         raise ValueError(
    #             f"Expected two columns in the csv file, found {len(col_names)}.",
    #             "The first column should contain the time values and the second column"
    #             " should contain the signal values.",
    #         )

    #     measurement = Measurement(id=path)
    #     measurement.add_to_chromatograms(
    #         times=df[col_names[0]].values.tolist(),
    #         signals=df[col_names[1]].values.tolist(),
    #         wavelength=wavelength,
    #         time_unit=time_unit,
    #         type=detector,
    #     )

    #     return cls(id=experiment_id, measurements=[measurement])

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
    ) -> list[Peak]:
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

    def _get_peaks_in_retention_interval(
        self,
        chromatogram: Chromatogram,
        lower_retention_time: float,
        upper_retention_time: float,
    ) -> list[Peak]:
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

    def _update_molecule(self, molecule) -> bool:
        """Updates the molecule if it already exists in the list of species."""
        for idx, mol in enumerate(self.molecules):
            if mol.pubchem_cid == molecule.pubchem_cid:
                self.molecules[idx] = molecule

                return True

        return False

    def _update_protein(self, protein) -> bool:
        """Updates the protein if it already exists in the list of proteins.
        Returns True if the protein was updated, False otherwise."""
        for idx, prot in enumerate(self.proteins):
            if prot.id == protein.id:
                self.proteins[idx] = protein

                return True

        return False

    def visualize_peaks(self):
        """
        Plot the chromatogram with annotated peaks.

        This method creates a plot of the chromatogram using the plotly library.
        It adds a scatter trace for the retention times and signals, and if there are peaks present, it adds vertical lines for each peak.

        Returns:
            go.Figure: The plotly figure object.
        """
        fig = go.Figure()

        # color map for unique peak ids
        unique_species = set(
            [
                peak.molecule_id
                for meas in self.measurements
                for chrom in meas.chromatograms
                for peak in chrom.peaks
                if peak.molecule_id
            ]
        )
        colors = pc.sample_colorscale(
            "viridis", [i / len(unique_species) for i in range(len(unique_species))]
        )
        color_dict = dict(zip(unique_species, colors))

        for meas in self.measurements:
            peaks = [
                peak
                for chrom in meas.chromatograms
                for peak in chrom.peaks
                if peak.molecule_id
            ]
            for peak in peaks:
                fig.add_trace(
                    go.Scatter(
                        x=[meas.reaction_time],
                        y=[peak.area],
                        name=self.get_molecule(peak.molecule_id).name,
                        marker=dict(color=color_dict[peak.molecule_id]),
                    )
                )

            fig.update_layout(
                xaxis_title=f"Reaction time / {meas.time_unit.name}",
                yaxis_title="Peak area",
            )

        legends = set()
        fig.for_each_trace(
            lambda trace: trace.update(showlegend=False)
            if (trace.name in legends)
            else legends.add(trace.name)
        )

        fig.show()

    def get_molecule(self, molecule_id: str) -> Molecule:
        for molecule in self.molecules:
            if molecule.id == molecule_id:
                return molecule

            if self.internal_standard:
                if self.internal_standard.id == molecule_id:
                    return self.internal_standard

        raise ValueError(f"Molecule with ID {molecule_id} not found.")

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
            for chrom in meas.chromatograms:
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
        fig = go.Figure()

        for species in self.molecules:
            if not species.concentrations:
                continue

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

        for standard in self.molecules:
            lower_ret = standard.retention_time - tolerance
            upper_ret = standard.retention_time + tolerance
            calibrator = Calibrator.from_standard(standard)
            model = calibrator.models[0]

            for meas in self.measurements:
                for chrom in meas.chromatograms:
                    for peak in chrom.peaks:
                        if lower_ret < peak.retention_time < upper_ret:
                            data[standard.name].append(
                                calibrator.calculate_concentrations(
                                    model=model, signals=[peak.area]
                                )[0]
                            )

        return data


if __name__ == "__main__":
    from devtools import pprint

    pprint(1)

    from chromatopy.tools.molecule import Molecule
    from chromatopy.units import M, min

    path = "example_data/liam/"
    reaction_times = [
        0,
        3,
        6.0,
        9,
        12,
        15,
        18,
        21,
        24,
        27,
        30,
        45,
        60,
        90,
        120,
        150,
        180,
    ]

    ana = ChromAnalyzer.read_agilent_csv(
        id="lr_205",
        path=path,
        reaction_times=reaction_times,
        time_unit=min,
        ph=7.0,
        temperature=25.0,
    )

    ana.add_molecule(
        id="mal",
        name="maleimide",
        pubchem_cid=10935,
        init_conc=0.656,
        conc_unit=M,
        retention_time=6.05,
    )

    ana.define_internal_standard(
        id="std",
        name="internal standard",
        pubchem_cid=123,
        init_conc=1.0,
        conc_unit=M,
        retention_time=6.3,
        retention_tolerance=0.05,
    )

    enzdoc = ana.create_enzymeml(name="test")

    # pprint(enzdoc)

    # pprint(ana)

    ana.visualize_peaks()

    # Molecule(
    #     id="s0",
    #     pubchem_cid=123,
    #     name="Molecule 1",
    #     init_conc=1.0,
    #     conc_unit=mM,
    # )
    import matplotlib.pyplot as plt

    plt.scatter(
        enzdoc.measurements[0].species_data[0].time,
        enzdoc.measurements[0].species_data[0].data,
    )
    plt.show()
    # ana.plot_measurements()
