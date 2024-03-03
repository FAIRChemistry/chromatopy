from typing import Any, List, Tuple, Dict
from collections import defaultdict
from dotted_dict import DottedDict
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px

from pydantic import BaseModel, Field

from HPLC.core.hplcexperiment import HPLCExperiment
from HPLC.core.molecule import Molecule
from HPLC.core.peak import Peak
from HPLC.core.role import Role
from HPLC.core.standard import Standard
from HPLC.core.signaltype import SignalType
from HPLC.tools.parser import parse_experiment


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
        detector: SignalType = "fid",
    ) -> Molecule:

        analyte = self._set_molecule(
            name=name,
            retention_time=retention_time,
            role=Role.ANALYTE,
            molecular_weight=molecular_weight,
            inchi=inchi,
            tolerance=tolerance,
            detector=detector,
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
        detector: SignalType = "fid",
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
            detector=detector,
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
            analyte.calculate_concentrations(internal_standard=internal_standard)

    def _analytes_to_records(self, analytes: List[Molecule] = None) -> List[Dict]:

        if analytes is None:
            analytes = self.analytes.values()
        if isinstance(analytes, Molecule):
            analytes = [analytes]

        dict_records = []
        for analyte in analytes:

            if not analyte.concentrations:
                raise ValueError(
                    f"No calculated concentrations found for {analyte.name}. \
                    Use 'calculate_concentrations' method first."
                )

            for time, rel_time, concenrtation in zip(
                analyte.times, analyte.minutes, analyte.concentrations
            ):

                dict_records.append(
                    {
                        "name": analyte.name,
                        "time": time,
                        "rel_time": rel_time,
                        "concentration": concenrtation,
                    }
                )

        return dict_records

    def _get_concentration_dict(
        self, analytes: List[Molecule] = None
    ) -> Dict[str, List[float]]:

        if analytes is None:
            analytes = self.analytes.values()
        if isinstance(analytes, Molecule):
            analytes = [analytes]

        # Get unique times across all analytes
        unique_times = self._get_sorted_set_of_attr_values(
            objects=analytes, attribute="minutes"
        )

        molecules_conc_dict = defaultdict(list)
        for time in unique_times:
            molecules_conc_dict["time [min]"].append(time)

            for analyte in analytes:
                if time in set(analyte.minutes):
                    pos = analyte.minutes.index(time)
                    molecules_conc_dict[analyte.name].append(
                        analyte.concentrations[pos]
                    )
                else:
                    molecules_conc_dict[analyte.name].append(float("nan"))

        return molecules_conc_dict

    def visualize_concentrations(
        self,
        analytes: List[Molecule] = None,
    ):
        if analytes is None:
            analytes = self.analytes.values()
        if isinstance(analytes, Molecule):
            analytes = [analytes]

        df = pd.DataFrame.from_records(self._analytes_to_records(analytes=analytes))

        return px.scatter(
            data_frame=df,
            x="rel_time",
            y="concentration",
            color="name",
        )

    def visualize_measurements(self, detector: SignalType = "fid"):

        df = pd.DataFrame(self.data._get_peak_records())
        df = df[df["signal_type"] == detector]

        return px.scatter(
            x=df["timestamp"],
            y=df["retention_time"],
            color=np.log(df["area"]),
            labels=dict(
                x="time of HPLC run", y="retention time / min", color="log(peak area)"
            ),
            title=f"{detector} detector data",
        )

    def to_csv(
        self,
        path: str,
        analytes: List[Molecule] = None,
    ) -> None:

        if analytes is None:
            analytes = self.analytes.values()
        if isinstance(analytes, Molecule):
            analytes = [analytes]

        conc_dict = self._get_concentration_dict(analytes=analytes)

        df = pd.DataFrame.from_dict(conc_dict)
        df = df.set_index(df.columns[0])

        return df.to_csv(path)

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
    ) -> Tuple[List[datetime], List[Peak]]:

        lower_ret = retention_time - tolerance
        upper_ret = retention_time + tolerance

        times = []
        peaks = []

        for measurement in self.data.measurements:

            time = measurement.timestamp

            detector_signals = measurement.get(
                path="signals", attribute="type", target=detector
            )[0][0]

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

    @staticmethod
    def _get_sorted_set_of_attr_values(objects: list, attribute: Any) -> List:
        """Gets a sorted set of unique values of a given attribute from a list of objects"""

        uniques = set(value for obj in objects for value in getattr(obj, attribute))

        return sorted(uniques)

    @staticmethod
    def _add_standard_to_molecule(
        molecule: Molecule,
        concentrations: List[float],
        signals: List[float],
        concentration_unit: str,
    ):

        assert len(concentrations) == len(signals)

        molecule.standard = Standard(
            concentration=concentrations,
            signal=signals,
            concentration_unit=concentration_unit,
        )

        return molecule

    @classmethod
    def from_directory(cls, path: str):

        data = parse_experiment(path)

        return cls(data=data)
