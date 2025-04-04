from __future__ import annotations

import copy
import json
import multiprocessing as mp
import time
from pathlib import Path
from typing import Any, Literal, Optional

import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go
import scipy
import scipy.stats
from calipytion.model import Standard
from calipytion.tools.utility import pubchem_request_molecule_name
from loguru import logger
from pydantic import BaseModel, Field, field_validator
from pyenzyme import EnzymeMLDocument
from rich.progress import Progress

from chromatopy.model import (
    Chromatogram,
    DataType,
    Measurement,
    Peak,
    UnitDefinition,
)
from chromatopy.tools.molecule import Molecule
from chromatopy.tools.peak_utils import SpectrumProcessor
from chromatopy.tools.protein import Protein
from chromatopy.tools.utility import _resolve_chromatogram
from chromatopy.units import C


class ChromAnalyzer(BaseModel):
    id: str = Field(
        description="Unique identifier of the given object.",
    )

    name: str = Field(
        description="Name of the ChromAnalyzer object.",
    )

    mode: str = Field(..., description="Mode of data processing: 'calibration' or 'timecourse'.")

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
        description="Internal standard molecule used for concentration calculation.",
        default=None,
    )

    @field_validator("mode", mode="before")
    def validate_mode(cls, value: str) -> str:
        value = value.lower()
        if value not in {DataType.CALIBRATION.value, DataType.TIMECOURSE.value}:
            raise ValueError("Invalid mode. Must be 'calibration' or 'timecourse'.")
        return value

    def __repr__(self) -> str:
        return (
            f"ChromAnalyzer(id={self.id!r}, "
            f"molecules={len(self.molecules)}, "
            f"proteins={len(self.proteins)}, "
            f"measurements={len(self.measurements)}"
        )

    def add_molecule_from_standard(
        self,
        standard: Standard,
        init_conc: float,
        conc_unit: UnitDefinition,
    ) -> None:
        """Adds a molecule to the list of species based on a `Standard` object."""

        molecule = Molecule.from_standard(standard, init_conc, conc_unit)

        self.define_molecule(**molecule.model_dump())

    def add_molecule(
        self,
        molecule: Molecule,
        init_conc: Optional[float] = None,
        conc_unit: Optional[UnitDefinition] = None,
        retention_tolerance: Optional[float] = None,
    ) -> None:
        """
        Adds a molecule to the list of species, allowing to update the initial concentration,
        concentration unit, and retention time tolerance.

        Args:
            molecule (Molecule): The molecule object to be added.
            init_conc (float | None, optional): The initial concentration of the molecule. Defaults to None.
            conc_unit (UnitDefinition | None, optional): The unit of the concentration. Defaults to None.
            retention_tolerance (float | None, optional): Retention time tolerance for peak annotation
                in minutes. Defaults to None.
        """

        new_mol = copy.deepcopy(molecule)

        if init_conc is not None:
            new_mol.init_conc = init_conc

        if conc_unit is not None:
            new_mol.conc_unit = conc_unit

        if retention_tolerance is not None:
            new_mol.retention_tolerance = retention_tolerance

        self._update_molecule(new_mol)

        if new_mol.has_retention_time:
            self._register_peaks(new_mol, new_mol.retention_tolerance, new_mol.wavelength)

    def define_molecule(
        self,
        id: str,
        pubchem_cid: int,
        retention_time: Optional[float],
        retention_tolerance: float = 0.1,
        init_conc: Optional[float] = None,
        conc_unit: Optional[UnitDefinition] = None,
        name: Optional[str] = None,
        wavelength: Optional[float] = None,
    ) -> Molecule:
        """
        Defines and adds a molecule to the list of molecules.

        Args:
            id (str): Internal identifier of the molecule, such as `s0` or `asd45`.
            pubchem_cid (int): PubChem CID of the molecule, which uniquely identifies the compound.
            retention_time (Optional[float]): Retention time for peak annotation in minutes. If the molecule is not
                detected in the chromatograms, this can be set to None.
            retention_tolerance (float, optional): Tolerance in minutes for retention time used in peak annotation.
                Defaults to 0.1.
            init_conc (Optional[float], optional): Initial concentration of the molecule. If not provided, it defaults to None.
            conc_unit (Optional[UnitDefinition], optional): Unit of the initial concentration. If not provided, it defaults to None.
            name (Optional[str], optional): Name of the molecule. If not provided, the name is fetched from the PubChem
                database. Defaults to None.
            wavelength (Optional[float], optional): Wavelength of the detector where the molecule was detected. If not provided,
                it defaults to None.

        Returns:
            Molecule: The molecule object that was added to the list of species.
        """

        if conc_unit:
            assert init_conc is not None, "Initial concentration must be provided if concentration unit is given."
        if init_conc:
            assert conc_unit, "Concentration unit must be provided if initial concentration is given."

        if name is None:
            name = pubchem_request_molecule_name(pubchem_cid)

        molecule = Molecule(
            id=id,
            pubchem_cid=pubchem_cid,
            name=name,
            init_conc=init_conc,
            conc_unit=conc_unit,
            retention_time=retention_time,
            retention_tolerance=retention_tolerance,
            wavelength=wavelength,
        )

        self._update_molecule(molecule)

        if molecule.has_retention_time:
            self._register_peaks(molecule, retention_tolerance, wavelength)

        return molecule

    def define_internal_standard(
        self,
        id: str,
        pubchem_cid: int,
        name: str,
        init_conc: float,
        conc_unit: UnitDefinition,
        retention_time: float,
        retention_tolerance: float = 0.1,
        wavelength: float | None = None,
    ) -> None:
        """Defines an molecule as the internal standard for concentration calculation.

        Args:
            id (str): Internal identifier of the molecule such as `s0` or `asd45`.
            pubchem_cid (int): PubChem CID of the molecule.
            name (str): Name of the internal standard molecule.
            init_conc (float): Initial concentration of the internal standard.
            conc_unit (UnitDefinition): Unit of the concentration.
            retention_time (float): Retention time of the internal standard in minutes.
            retention_tolerance (float, optional): Retention time tolerance for
                peak annotation in minutes. Defaults to 0.1.
            wavelength (float | None, optional): Wavelength of the detector on
                which the molecule was detected. Defaults to None.
        """
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

    def get_peaks(self, molecule_id: str) -> list[Peak]:
        peaks: list[Peak] = []
        for meas in self.measurements:
            for chrom in meas.chromatograms:
                for peak in chrom.peaks:
                    if peak.molecule_id == molecule_id:
                        peaks.append(peak)

        if not peaks:
            raise ValueError(f"No peaks found for molecule {molecule_id}.")
        return peaks

    def _register_peaks(
        self,
        molecule: Molecule,
        ret_tolerance: float,
        wavelength: float | None,
    ) -> None:
        """Registers the peaks of a molecule based on the retention time tolerance and wavelength.

        Args:
            molecule (Molecule): The molecule for which the peaks should be registered.
            ret_tolerance (float): Retention time tolerance for peak annotation in minutes.
            wavelength (float | None): Wavelength of the detector on which the molecule was detected.
        """
        assigned_peak_count = 0
        if not molecule.has_retention_time:
            raise ValueError(f"Molecule {molecule.id} has no retention time.")

        for meas in self.measurements:
            for peak in _resolve_chromatogram(meas.chromatograms, wavelength).peaks:
                if (
                    peak.retention_time is not None
                    and molecule.retention_time is not None
                    and peak.retention_time - ret_tolerance
                    < molecule.retention_time
                    < peak.retention_time + ret_tolerance
                ):
                    peak.molecule_id = molecule.id
                    assigned_peak_count += 1
                    logger.debug(f"{molecule.id} assigned as molecule ID for peak at {peak.retention_time}.")

        print(f"🎯 Assigned {molecule.name} to {assigned_peak_count} peaks")

    def define_protein(
        self,
        id: str,
        name: str,
        init_conc: float,
        conc_unit: UnitDefinition,
        sequence: str | None = None,
        organism: str | None = None,
        organism_tax_id: str | None = None,
        constant: bool = True,
    ) -> None:
        """Adds a protein to the list of proteins or updates an existing protein
        based on the pubchem_cid of the molecule.

        Args:
            id (str): Internal identifier of the protein such as `p0` or `asd45`.
            name (str): Name of the protein.
            init_conc (float): Initial concentration of the protein.
            conc_unit (UnitDefinition): Unit of the concentration.
            sequence (str, optional): Amino acid sequence of the protein. Defaults to None.
            organism (str, optional): Name of the organism. Defaults to None.
            organism_tax_id (int, optional): NCBI taxonomy ID of the organism. Defaults to None.
            constant (bool, optional): Boolean indicating whether the protein concentration is constant. Defaults to True.
        """
        protein = Protein(
            id=id,
            name=name,
            init_conc=init_conc,
            conc_unit=conc_unit,
            sequence=sequence,
            organism=organism,
            organism_tax_id=organism_tax_id,
            constant=constant,
        )

        self._update_protein(protein)

    def add_protein(
        self,
        protein: Protein,
        init_conc: float | None = None,
        conc_unit: UnitDefinition | None = None,
    ) -> None:
        """Adds a protein to the list of proteins or updates an existing protein
        based on the pubchem_cid of the molecule.

        Args:
            protein (Protein): The protein object to be added.
        """

        nu_prot = copy.deepcopy(protein)

        if init_conc:
            nu_prot.init_conc = init_conc

        if conc_unit:
            nu_prot.conc_unit = conc_unit

        self._update_protein(nu_prot)

    def process_chromatograms(
        self,
        prominence: float = 0.03,
        min_retention_time: float | None = None,
        max_retention_time: float | None = None,
        **hplc_py_kwargs: dict[str, Any],
    ) -> None:
        """
        Processes the chromatograms using the [`hplc-py`](https://cremerlab.github.io/hplc-py/index.html) library.
        !!! info
            Please consider using OpenChrom or other chromatography software to calculate peak areas.
            Especially for complex chromatograms, the results may be more accurate.

        Args:
            prominence: The prominence of the peaks to be detected. Defaults to 0.03.
            min_retention_time: The minimum retention time to be considered in the peak detection.
                Defaults to None.
            max_retention_time: The maximum retention time to be considered in the peak detection.
                Defaults to None.
            hplc_py_kwargs: Keyword arguments to be passed to the `fit_peaks` method of the
                `hplc-py` library. For more information, visit the [HPLC-Py Documentation](https://cremerlab.github.io/hplc-py/quant.html#hplc.quant.Chromatogram.fit_peaks).
        """

        hplc_py_kwargs["prominence"] = prominence  # type: ignore
        hplc_py_kwargs["approx_peak_width"] = 0.6  # type: ignore
        processors = []

        for meas in self.measurements:
            for chrom in meas.chromatograms:
                if min_retention_time is not None:
                    # get index of first retention time greater than min_retention_time
                    idx_min = int(np.argmax(np.array(chrom.times) > min_retention_time))
                    times = chrom.times[idx_min:]
                    signals = chrom.signals[idx_min:]
                else:
                    times = chrom.times
                    signals = chrom.signals
                    idx_min = 0

                if max_retention_time is not None:
                    # filter out retention times greater than max_retention_time
                    idx_max = int(np.argmax(np.array(times) > max_retention_time))
                    times = times[:idx_max]
                    signals = signals[:idx_max]
                else:
                    idx_max = len(chrom.times)

                processors.append(
                    SpectrumProcessor(
                        time=times,
                        raw_data=signals,
                        silent=True,
                    )
                )

        with Progress() as progress:
            task = progress.add_task("Processing chromatograms...", total=len(self.measurements))

            with mp.Pool(processes=mp.cpu_count()) as pool:
                result_objects = [
                    pool.apply_async(self.process_task, args=(processor,), kwds=hplc_py_kwargs)
                    for processor in processors
                ]

                results = []
                for result in result_objects:
                    processor_result = result.get()  # Retrieve the actual result
                    results.append(processor_result)
                    progress.update(task, advance=1)
            time.sleep(0.1)
            progress.update(task, refresh=True)

        processor_idx = 0
        no_peaks = False
        for meas in self.measurements:
            for chrom in meas.chromatograms:
                chrom.peaks = []
                if not hasattr(results[processor_idx], "peaks"):
                    no_peaks = True
                    logger.warning(f"No peaks found in chromatogram {meas.id} at {chrom.wavelength} nm.")
                    processor_idx += 1
                    continue
                # pad the processed signal with zeros to match the length of the raw signal accounting for the cropping of the retention time
                nans_laft = idx_min
                nans_right = len(chrom.signals) - len(times)

                chrom.processed_signal = np.concatenate(
                    [
                        np.full(nans_laft, float(0)),
                        results[processor_idx].processed_signal,
                        np.full(nans_right, float(0)),
                    ]
                ).tolist()

                # replace nan values and nones with 0
                # self.processed_signal = [
                #     0 if np.isnan(d) or d is None else d for d in self.processed_signal
                # ]

                chrom.peaks = results[processor_idx].peaks
                processor_idx += 1

        for molecule in self.molecules:
            self._register_peaks(molecule, molecule.retention_tolerance, molecule.wavelength)

        if no_peaks:
            print(
                "No peaks found in one of the chromatograms, try to reduce the `prominence` in the `hplc_py_kwargs` of the `process_chromatograms` method."
            )

    @staticmethod
    def process_task(processor: SpectrumProcessor, **kwargs: Any) -> Chromatogram:
        try:
            return processor.silent_fit(**kwargs)
        except KeyError as e:
            if "retention_time" in str(e):
                # check if retention time is in kwargs and halve it
                if "retention_time" in kwargs:
                    kwargs["retention_time"] /= 2
                    return processor.silent_fit(**kwargs)
            raise  # re-raise the exception if we can't handle it

    @classmethod
    def read_asm(
        cls,
        path: str,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition = C,
        mode: Optional[Literal["timecourse", "calibration"]] = None,
        values: Optional[list[float]] = None,
        unit: Optional[UnitDefinition] = None,
        id: str | None = None,
        name: str = "Chromatographic measurement",
        silent: bool = False,
    ) -> ChromAnalyzer:
        """Reads chromatographic data from a directory containing Allotrope Simple Model (ASM) json files.
        Measurements are assumed to be named alphabetically, allowing sorting by file name.

        Args:
            path (str): Path to the directory containing the ASM files.
            ph (float): pH value of the measurement.
            temperature (float): Temperature of the measurement.
            temperature_unit (UnitDefinition, optional): Unit of the temperature. Defaults to Celsius (C).
            mode (Optional[Literal["timecourse", "calibration"]], optional): Mode of the data. If "timecourse",
                `values` should be a list of reaction times. If "calibration", `values` should be a list of concentrations.
                Defaults to None.
            values (list[float], optional): A list of reaction times (for "timecourse" mode) or concentrations
                (for "calibration" mode), corresponding to each measurement in the directory.
            unit (UnitDefinition, optional): Unit of the `values` provided. It can be the time unit for reaction times or
                the concentration unit for calibration mode, depending on the mode.
            id (str, optional): Unique identifier of the ChromAnalyzer object. If not provided, the `path` is used as ID.
            name (str, optional): Name of the measurement. Defaults to "Chromatographic measurement".
            silent (bool, optional): If True, no success message is printed. Defaults to False.

        Returns:
            ChromAnalyzer: ChromAnalyzer object containing the measurements.
        """
        from chromatopy.readers.asm import ASMReader

        data = {
            "dirpath": path,
            "values": values,
            "unit": unit,
            "ph": ph,
            "temperature": temperature,
            "temperature_unit": temperature_unit,
            "silent": silent,
            "mode": mode,
        }

        reader = ASMReader(**data)
        measurements = reader.read()

        if id is None:
            id = path

        return cls(id=id, name=name, measurements=measurements, mode=reader.mode)

    @classmethod
    def read_shimadzu(
        cls,
        path: str,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition = C,
        mode: Optional[Literal["timecourse", "calibration"]] = None,
        values: Optional[list[float]] = None,
        unit: Optional[UnitDefinition] = None,
        id: str | None = None,
        name: str = "Chromatographic measurement",
        silent: bool = False,
    ) -> ChromAnalyzer:
        """Reads chromatographic data from a directory containing Shimadzu files.
        Measurements are assumed to be named alphabetically, allowing sorting by file name.

        Args:
            path (str): Path to the directory containing the Shimadzu files.
            ph (float): pH value of the measurement.
            temperature (float): Temperature of the measurement.
            temperature_unit (UnitDefinition, optional): Unit of the temperature. Defaults to Celsius (C).
            mode (Optional[Literal["timecourse", "calibration"]], optional): Mode of the data. If "timecourse",
                `values` should be a list of reaction times. If "calibration", `values` should be a list of concentrations.
                Defaults to None.
            values (list[float], optional): A list of reaction times (for "timecourse" mode) or concentrations
                (for "calibration" mode), corresponding to each measurement in the directory.
            unit (UnitDefinition, optional): Unit of the `values` provided. It can be the time unit for reaction times or
                the concentration unit for calibration mode, depending on the mode.
            id (str, optional): Unique identifier of the ChromAnalyzer object. If not provided, the `path` is used as ID.
            name (str, optional): Name of the measurement. Defaults to "Chromatographic measurement".
            silent (bool, optional): If True, no success message is printed. Defaults to False.

        Returns:
            ChromAnalyzer: ChromAnalyzer object containing the measurements.
        """
        from chromatopy.readers.shimadzu import ShimadzuReader

        data = {
            "dirpath": path,
            "values": values,
            "unit": unit,
            "ph": ph,
            "temperature": temperature,
            "temperature_unit": temperature_unit,
            "silent": silent,
            "mode": mode,
        }

        reader = ShimadzuReader(**data)
        measurements = reader.read()

        if id is None:
            id = path

        return cls(
            id=id,
            name=name,
            measurements=measurements,
            mode=reader.mode,
        )

    @classmethod
    def read_agilent(
        cls,
        path: str,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition = C,
        mode: Optional[Literal["timecourse", "calibration"]] = None,
        values: Optional[list[float]] = None,
        unit: Optional[UnitDefinition] = None,
        id: str | None = None,
        name: str = "Chromatographic measurement",
        silent: bool = False,
    ) -> ChromAnalyzer:
        """Reads Agilent `Report.txt` or `RESULTS.csv` files within a `*.D` directories within the specified path.

        Args:
            path (str): Path to the directory containing the Shimadzu files.
            ph (float): pH value of the measurement.
            temperature (float): Temperature of the measurement.
            temperature_unit (UnitDefinition, optional): Unit of the temperature. Defaults to Celsius (C).
            mode (Optional[Literal["timecourse", "calibration"]], optional): Mode of the data. If "timecourse",
                `values` should be a list of reaction times. If "calibration", `values` should be a list of concentrations.
                Defaults to None.
            values (list[float], optional): A list of reaction times (for "timecourse" mode) or concentrations
                (for "calibration" mode), corresponding to each measurement in the directory.
            unit (UnitDefinition, optional): Unit of the `values` provided. It can be the time unit for reaction times or
                the concentration unit for calibration mode, depending on the mode.
            id (str, optional): Unique identifier of the ChromAnalyzer object. If not provided, the `path` is used as ID.
            name (str, optional): Name of the measurement. Defaults to "Chromatographic measurement".
            silent (bool, optional): If True, no success message is printed. Defaults to False.

        Returns:
            ChromAnalyzer: ChromAnalyzer object containing the measurements.
        """
        from chromatopy.readers.agilent_csv import AgilentCSVReader
        from chromatopy.readers.agilent_rdl import AgilentRDLReader
        from chromatopy.readers.agilent_txt import AgilentTXTReader

        directory = Path(path)

        txt_paths = []
        csv_paths = []
        rdl_paths: list[str] = []

        txt_paths = [str(f.absolute()) for f in directory.rglob("Report.TXT") if f.parent.parent == directory]
        csv_paths = [str(f.absolute()) for f in directory.rglob("RESULTS.CSV") if f.parent.parent == directory]
        rdl_paths = []

        try:
            txt_path = next(directory.rglob("*.txt"))
            try:
                lines = AgilentRDLReader.read_file(str(txt_path))
                if lines[0].startswith("┌─────"):
                    rdl_paths = [str(f.absolute()) for f in directory.rglob("*.txt")]
                else:
                    txt_paths = txt_paths
            except UnicodeDecodeError:
                txt_paths = txt_paths

        except StopIteration:
            txt_paths = txt_paths

        data = {
            "dirpath": path,
            "values": values,
            "unit": unit,
            "ph": ph,
            "temperature": temperature,
            "temperature_unit": temperature_unit,
            "silent": silent,
            "mode": mode,
        }

        if rdl_paths:
            data["file_paths"] = rdl_paths  # type: ignore
            reader = AgilentRDLReader(**data)
            measurements = reader.read()  # type: ignore
        elif not csv_paths and txt_paths:
            data["file_paths"] = txt_paths  # type: ignore
            reader = AgilentTXTReader(**data)  # type: ignore
            measurements = reader.read()  # type: ignore
        elif csv_paths and not txt_paths:
            data["file_paths"] = csv_paths  # type: ignore
            reader = AgilentCSVReader(**data)  # type: ignore
            measurements = AgilentCSVReader(**data).read()
        else:
            raise IOError(f"No 'REPORT.TXT' or 'RESULTS.CSV' files found in '{path}'.")

        if id is None:
            id = path

        return cls(id=id, name=name, measurements=measurements, mode=reader.mode)

    @classmethod
    def read_chromeleon(
        cls,
        path: str,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition = C,
        mode: Optional[Literal["timecourse", "calibration"]] = None,
        values: Optional[list[float]] = None,
        unit: Optional[UnitDefinition] = None,
        id: str | None = None,
        name: str = "Chromatographic measurement",
        silent: bool = False,
    ) -> ChromAnalyzer:
        """Reads Chromeleon txt files from a directory. The files in the directory are assumed to be of
        one calibration or timecourse measurement series.

        Args:
            path (str): Path to the directory containing the Shimadzu files.
            ph (float): pH value of the measurement.
            temperature (float): Temperature of the measurement.
            temperature_unit (UnitDefinition, optional): Unit of the temperature. Defaults to Celsius (C).
            mode (Optional[Literal["timecourse", "calibration"]], optional): Mode of the data. If "timecourse",
                `values` should be a list of reaction times. If "calibration", `values` should be a list of concentrations.
                Defaults to None.
            values (list[float], optional): A list of reaction times (for "timecourse" mode) or concentrations
                (for "calibration" mode), corresponding to each measurement in the directory.
            unit (UnitDefinition, optional): Unit of the `values` provided. It can be the time unit for reaction times or
                the concentration unit for calibration mode, depending on the mode.
            id (str, optional): Unique identifier of the ChromAnalyzer object. If not provided, the `path` is used as ID.
            name (str, optional): Name of the measurement. Defaults to "Chromatographic measurement".
            silent (bool, optional): If True, no success message is printed. Defaults to False.

        Returns:
            ChromAnalyzer: ChromAnalyzer object containing the measurements.
        """
        from chromatopy.readers.chromeleon import ChromeleonReader

        data = {
            "dirpath": path,
            "values": values,
            "unit": unit,
            "ph": ph,
            "temperature": temperature,
            "temperature_unit": temperature_unit,
            "silent": silent,
            "mode": mode,
        }

        if id is None:
            id = path

        reader = ChromeleonReader(**data)
        measurements = reader.read()

        return cls(id=path, name=name, measurements=measurements, mode=reader.mode)

    @classmethod
    def read_thermo(
        cls,
        path: str,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition = C,
        mode: Optional[Literal["timecourse", "calibration"]] = None,
        values: Optional[list[float]] = None,
        unit: Optional[UnitDefinition] = None,
        id: str | None = None,
        name: str = "Chromatographic measurement",
        silent: bool = False,
    ) -> ChromAnalyzer:
        """Reads chromatographic data from a directory containing Thermo Scientific TX0 files.
        Measurements are assumed to be named alphabetically, allowing sorting by file name.

        Args:
            path (str): Path to the directory containing the TX0 files.
            ph (float): pH value of the measurement.
            temperature (float): Temperature of the measurement.
            temperature_unit (UnitDefinition, optional): Unit of the temperature. Defaults to Celsius (C).
            mode (Optional[Literal["timecourse", "calibration"]], optional): Mode of the data. If "timecourse",
                `values` should be a list of reaction times. If "calibration", `values` should be a list of concentrations.
                Defaults to None.
            values (list[float], optional): A list of reaction times (for "timecourse" mode) or concentrations
                (for "calibration" mode), corresponding to each measurement in the directory.
            unit (UnitDefinition, optional): Unit of the `values` provided. It can be the time unit for reaction times or
                the concentration unit for calibration mode, depending on the mode.
            id (str, optional): Unique identifier of the ChromAnalyzer object. If not provided, the `path` is used as ID.
            name (str, optional): Name of the measurement. Defaults to "Chromatographic measurement".
            silent (bool, optional): If True, no success message is printed. Defaults to False.

        Returns:
            ChromAnalyzer: ChromAnalyzer object containing the measurements.
        """
        from chromatopy.readers.thermo_txt import ThermoTX0Reader

        data = {
            "dirpath": path,
            "values": values,
            "unit": unit,
            "ph": ph,
            "temperature": temperature,
            "temperature_unit": temperature_unit,
            "silent": silent,
            "mode": mode,
        }

        if id is None:
            id = path

        reader = ThermoTX0Reader(**data)  # type: ignore
        measurements = reader.read()

        return cls(id=id, name=name, measurements=measurements, mode=reader.mode)

    def to_json(self, path: str | Path) -> None:
        """
        Serialize the instance to a JSON file.
        Parameters:
            path (str | Path): The file path where the JSON data will be saved.
                                If the parent directory does not exist, it will be created.
        Returns:
            None: This method does not return a value. It writes the instance's
            attributes to a JSON file at the specified path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize the instance to JSON, allowing overwriting
        with open(path, "w") as file:
            file.write(self.model_dump_json(indent=2))

    @classmethod
    def read_csv(
        cls,
        path: str,
        mode: Literal["timecourse", "calibration"],
        values: list[float],
        unit: UnitDefinition,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition,
        retention_time_col_name: str,
        peak_area_col_name: str,
        silent: bool = False,
    ) -> ChromAnalyzer:
        """Reads chromatographic data from a CSV file.

        Args:
            path (str): Path to the CSV file.
            mode (Literal["timecourse", "calibration"]): Mode of the data.
            values (list[float]): List of values.
            unit (UnitDefinition): Unit of the values.
            ph (float): pH value of the measurement.
            temperature (float): Temperature of the measurement.
            temperature_unit (UnitDefinition): Unit of the temperature.
            retention_time_col_name (str): Name of the retention time column.
            peak_area_col_name (str): Name of the peak area column.
            silent (bool, optional): If True, no success message is printed. Defaults to False.

        Returns:
            ChromAnalyzer: ChromAnalyzer object containing the measurements.
        """
        from chromatopy.readers.generic_csv import GenericCSVReader

        reader = GenericCSVReader(
            dirpath=path,
            mode=mode,
            values=values,
            unit=unit,
            ph=ph,
            temperature=temperature,
            temperature_unit=temperature_unit,
            silent=silent,
        )
        measurements = reader.read_generic_csv(
            retention_time_col_name=retention_time_col_name, peak_area_col_name=peak_area_col_name
        )
        return cls(id=path, name=path, measurements=measurements, mode=reader.mode)

    @classmethod
    def from_json(cls, path: str) -> ChromAnalyzer:
        """
        Load an instance of the class from a JSON file.

        Args:
            path (str): The file path to the JSON file.

        Returns:
            An instance of the class populated with data from the JSON file.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        # Load from a JSON file
        with open(path, "r") as file:
            data = json.load(file)

        # Return an instance of the class
        return cls(**data)

    def to_enzymeml(
        self,
        name: str,
        calculate_concentration: bool = True,
        extrapolate: bool = False,
    ) -> EnzymeMLDocument:
        """Creates an EnzymeML document from the data in the ChromAnalyzer.

        Args:
            name (str): Name of the EnzymeML document.
            calculate_concentration (bool, optional): If True, the concentrations of the species
                are calculated. Defaults to True.
            extrapolate (bool, optional): If True, the concentrations are extrapolated to if the
                measured peak areas are outside the calibration range. Defaults to False.

        Returns:
            EnzymeMLDocument: _description_
        """
        from chromatopy.ioutils.enzymeml import create_enzymeml

        return create_enzymeml(
            doc_name=name,
            molecules=self.molecules,
            proteins=self.proteins,
            measurements=self.measurements,
            calculate_concentration=calculate_concentration,
            internal_standard=self.internal_standard,
            extrapolate=extrapolate,
        )

    def add_to_enzymeml(
        self,
        enzdoc: EnzymeMLDocument,
        calculate_concentration: bool = True,
        extrapolate: bool = False,
    ) -> EnzymeMLDocument:
        """Adds the data from the ChromAnalyzer to an existing EnzymeML document.

        Args:
            enzdoc (EnzymeMLDocument): The EnzymeML document to which the data should be added.
            calculate_concentration (bool, optional): If True, the concentrations of the species
                are calculated. Defaults to True.
            extrapolate (bool, optional): If True, the concentrations are extrapolated to if the
                measured peak areas are outside the calibration range. Defaults to False.

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
            extrapolate=extrapolate,
        )

    def get_molecule(self, molecule_id: str) -> Molecule:
        for molecule in self.molecules:
            if molecule.id == molecule_id:
                return molecule

            if self.internal_standard:
                if self.internal_standard.id == molecule_id:
                    return self.internal_standard

        raise ValueError(f"Molecule with ID {molecule_id} not found.")

    def visualize_all(self, assigned_only: bool = False, dark_mode: bool = False, show: bool = False) -> go.Figure:
        """Plots the fitted peaks of the chromatograms in an interactive figure.

        Args:
            assigned_only (bool, optional): If True, only the peaks that are assigned to a molecule are plotted. Defaults to False.
            dark_mode (bool, optional): If True, the figure is displayed in dark mode. Defaults to False.

        Returns:
            go.Figure: _description_
        """
        # make plotly figure for each chromatogram whereas ech chromatogram contains multiple traces and each comatogram is mapped to one slider
        from plotly.express.colors import sample_colorscale

        from chromatopy.tools.utility import generate_gaussian_data, generate_visibility

        if dark_mode:
            theme = "plotly_dark"
            signal_color = "white"
        else:
            theme = "plotly_white"
            signal_color = "black"

        peak_vis_mode = None

        fig = go.Figure()

        for meas in self.measurements:
            for chrom in meas.chromatograms[:1]:
                # model peaks as gaussians
                if chrom.peaks:
                    peaks_exist = True
                    if len(chrom.peaks) == 1:
                        color_map = ["teal"]
                    else:
                        color_map = sample_colorscale("viridis", len(chrom.peaks))

                    for color, peak in zip(color_map, chrom.peaks):
                        if assigned_only and not peak.molecule_id:
                            continue

                        if peak.molecule_id:
                            peak_name = self.get_molecule(peak.molecule_id).name
                        else:
                            if peak.retention_time is None:
                                raise ValueError("Peak retention time cannot be None")
                            peak_name = f"Peak {peak.retention_time:.2f}"

                        if peak.peak_start and peak.peak_end and peak.width:
                            if peak.amplitude is None or peak.retention_time is None:
                                raise ValueError(
                                    "Peak amplitude and retention time must not be None for Gaussian visualization"
                                )
                            x_arr, data = generate_gaussian_data(
                                amplitude=peak.amplitude,
                                center=peak.retention_time,
                                half_height_diameter=peak.width,
                                start=peak.peak_start,
                                end=peak.peak_end,
                            )
                            peak_vis_mode = "gaussian"

                        elif peak.skew and peak.width:
                            if peak.retention_time is None or peak.amplitude is None:
                                raise ValueError(
                                    "Peak retention time and amplitude must not be None for skewed visualization"
                                )
                            x_start = peak.retention_time - 3 * peak.width
                            x_end = peak.retention_time + 3 * peak.width
                            x_arr = np.linspace(x_start, x_end, 100).tolist()
                            data = (
                                scipy.stats.skewnorm.pdf(
                                    x_arr,
                                    peak.skew if peak.skew else 0,
                                    loc=peak.retention_time,
                                    scale=peak.width,
                                )
                                * peak.amplitude
                            )
                            peak_vis_mode = "skewnorm"

                        else:
                            if peak.retention_time is None or peak.amplitude is None:
                                raise ValueError(
                                    "Peak retention time and amplitude must not be None for line visualization"
                                )
                            # make only h-line at retention time
                            interval = 0.03
                            left_shifted = peak.retention_time - interval
                            right_shifted = peak.retention_time + interval
                            x_arr = [
                                left_shifted,
                                right_shifted,
                                right_shifted,
                                left_shifted,
                                left_shifted,
                            ]
                            data = [0, 0, peak.amplitude, peak.amplitude, 0]

                        custom1 = [round(peak.area)] * len(x_arr)
                        custom2 = [round(peak.retention_time, 2)] * len(x_arr)
                        customdata = np.stack((custom1, custom2), axis=-1)
                        fig.add_trace(
                            go.Scatter(
                                visible=False,
                                x=x_arr,
                                y=data,
                                mode="lines",
                                name=peak_name,
                                customdata=customdata,
                                hovertemplate="<b>Area:</b> %{customdata[0]}<br>"
                                + "<b>Center:</b> %{customdata[1]}<br>"
                                + "<extra></extra>",
                                hovertext=f"{meas.id}",
                                line=dict(
                                    color=color,
                                    width=1,
                                ),
                                fill="tozeroy",
                                fillcolor=color,
                            )
                        )

                else:
                    peaks_exist = False

                if chrom.times and chrom.signals:
                    signal_exist = True
                    fig.add_trace(
                        go.Scatter(
                            visible=False,
                            x=chrom.times,
                            y=chrom.signals,
                            mode="lines",
                            name="Signal",
                            hovertext=f"{meas.id}",
                            line=dict(
                                color=signal_color,
                                dash="solid",
                                width=1,
                            ),
                        )
                    )
                else:
                    signal_exist = False

                if chrom.processed_signal and chrom.times:
                    processed_signal_exist = True
                    fig.add_trace(
                        go.Scatter(
                            visible=False,
                            x=chrom.times,
                            y=chrom.processed_signal,
                            mode="lines",
                            name="Processed Signal",
                            hovertext=f"{meas.id}",
                            line=dict(
                                color="red",
                                dash="dot",
                                width=2,
                            ),
                        )
                    )
                else:
                    processed_signal_exist = False

        if assigned_only:
            n_peaks_in_first_chrom = len(
                [peak for peak in self.measurements[0].chromatograms[0].peaks if peak.molecule_id]
            )
        else:
            n_peaks_in_first_chrom = len(self.measurements[0].chromatograms[0].peaks)

        if peak_vis_mode == "gaussian":
            logger.info(
                "Gaussian peaks are used for visualization, the actual peak shape might differ and is based on the previous preak processing."
            )

        if signal_exist and not processed_signal_exist:
            fig.data[n_peaks_in_first_chrom].visible = True
        elif signal_exist and processed_signal_exist:
            fig.data[n_peaks_in_first_chrom].visible = True
            fig.data[n_peaks_in_first_chrom + 1].visible = True

        if peaks_exist:
            for i in range(n_peaks_in_first_chrom):
                fig.data[i].visible = True

        steps = []
        for meas in self.measurements:
            for chrom in meas.chromatograms:
                step = {
                    "label": f"{meas.id}",
                    "method": "update",
                    "args": [
                        {
                            "visible": generate_visibility(meas.id, fig),
                        }
                    ],
                }
                steps.append(step)

        sliders = [
            {
                "active": 0,
                "currentvalue": {"prefix": "Chromatogram: "},
                "steps": steps,
            }
        ]

        fig.update_layout(
            sliders=sliders,
            xaxis_title="retention time [min]",
            yaxis_title="Intensity",
            template=theme,
        )

        if show:
            fig.show()
        else:
            return fig

    def add_standard(
        self,
        molecule: Molecule,
        wavelength: float | None = None,
        visualize: bool = True,
    ) -> None:
        """Creates a standard curve for a molecule based on the peak areas and concentrations.

        Args:
            molecule (Molecule): The molecule for which the standard curve should be created.
            wavelength (float | None, optional): The wavelength of the detector. Defaults to None.
            visualize (bool, optional): If True, the standard curve is visualized. Defaults to True.
        """
        assert any([molecule in [mol for mol in self.molecules]]), "Molecule not found in molecules of analyzer."

        # check if all measurements only contain one chromatogram
        if all([len(meas.chromatograms) == 1 for meas in self.measurements]):
            chroms = [chrom for meas in self.measurements for chrom in meas.chromatograms]
        else:
            assert (
                wavelength is not None
            ), "Multiple chromatograms found for each measurment, wavelength needs to be provided."

            chroms = self._get_chromatograms_by_wavelegnth(wavelength)

            assert len(chroms) > 0, "No chromatograms found at the specified wavelength."

        peak_areas = [peak.area for chrom in chroms for peak in chrom.peaks if peak.molecule_id]

        concs = [meas.data.value for meas in self.measurements]
        conc_unit = self.measurements[0].data.unit

        assert len(peak_areas) == len(
            concs
        ), f"Number of {molecule.name} peak areas {len(peak_areas)} and concentrations {len(concs)} do not match."

        assert all(
            meas.ph == self.measurements[0].ph for meas in self.measurements
        ), "All measurements need to have the same pH value."
        ph = self.measurements[0].ph

        assert all(
            meas.temperature == self.measurements[0].temperature for meas in self.measurements
        ), "All measurements need to have the same temperature value."
        temperature = self.measurements[0].temperature

        assert all(
            meas.temperature_unit.name == self.measurements[0].temperature_unit.name for meas in self.measurements
        ), "All measurements need to have the same temperature unit."
        temperature_unit = self.measurements[0].temperature_unit

        molecule.create_standard(
            areas=peak_areas,
            concs=concs,
            conc_unit=conc_unit,
            ph=ph,
            temperature=temperature,
            temp_unit=temperature_unit,
            visualize=visualize,
        )

    def _get_chromatograms_by_wavelegnth(self, wavelength: float) -> list[Chromatogram]:
        """Returns a list of chromatograms at a specified wavelength.

        Args:
            wavelength (float): The wavelength of the detector.

        Returns:
            list[Chromatogram]: A list of chromatograms at the specified wavelength.
        """

        chroms = []
        for meas in self.measurements:
            for chrom in meas.chromatograms:
                if chrom.wavelength == wavelength:
                    chroms.append(chrom)

        return chroms

    def _update_molecule(self, molecule: Molecule) -> None:
        """Updates the molecule if it already exists in the list of species.
        Otherwise, the molecule is added to the list of species."""
        for idx, mol in enumerate(self.molecules):
            if mol.id == molecule.id:
                self.molecules[idx] = molecule
                assert self.molecules[idx] is molecule
                return

        self.molecules.append(molecule)

    def _update_protein(self, protein: Protein) -> None:
        """Updates the protein if it already exists in the list of proteins.
        Otherwise, the protein is added to the list of proteins.
        """
        for idx, prot in enumerate(self.proteins):
            if prot.id == protein.id:
                self.proteins[idx] = protein
                return

        self.proteins.append(protein)

    def visualize_spectra(self, dark_mode: bool = False) -> go.Figure:
        """
        Plots all chromatograms in the ChromAnalyzer in a single plot.

        Args:
            dark_mode (bool, optional): If True, the figure is displayed in dark mode. Defaults to False.

        Returns:
            go.Figure: The plotly figure object.
        """

        if dark_mode:
            theme = "plotly_dark"
        else:
            theme = "plotly_white"

        fig = go.Figure()

        color_map = pc.sample_colorscale("viridis", len(self.measurements))
        for meas, color in zip(self.measurements, color_map):
            for chrom in meas.chromatograms[:1]:
                fig.add_trace(
                    go.Scatter(
                        x=chrom.times,
                        y=chrom.signals,
                        name=meas.id,
                        line=dict(width=2, color=color),
                    )
                )

        if chrom.wavelength:
            wave_string = f"({chrom.wavelength} nm)"
        else:
            wave_string = ""

        fig.update_layout(
            xaxis_title="retention time [min]",
            yaxis_title=f"Intensity {wave_string}",
            height=600,
            legend={"traceorder": "normal"},
            template=theme,
        )

        return fig
