import warnings
from datetime import datetime as Datetime
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sdRDM
from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM.base.datatypes import Unit
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict

from ..tools.calibration import Calibrator
from .analyte import Analyte
from .chromatogram import Chromatogram
from .measurement import Measurement
from .peak import Peak
from .role import Role
from .signaltype import SignalType
from .standard import Standard


@forge_signature
class ChromHandler(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    analytes: List[Analyte] = element(
        description="Molecule that can be assigned to a peak.",
        default_factory=ListPlus,
        tag="analytes",
        json_schema_extra=dict(multiple=True),
    )

    measurements: List[Measurement] = element(
        description="Measured signals",
        default_factory=ListPlus,
        tag="measurements",
        json_schema_extra=dict(multiple=True),
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

    def add_to_analytes(
        self,
        name: Optional[str] = None,
        inchi: Optional[str] = None,
        molecular_weight: Optional[float] = None,
        retention_time: Optional[float] = None,
        peaks: List[Peak] = ListPlus(),
        injection_times: List[Datetime] = ListPlus(),
        concentrations: List[float] = ListPlus(),
        standard: Optional[Standard] = None,
        role: Optional[Role] = None,
        reaction_times: List[float] = ListPlus(),
        id: Optional[str] = None,
    ) -> Analyte:
        """
        This method adds an object of type 'Analyte' to attribute analytes

        Args:
            id (str): Unique identifier of the 'Analyte' object. Defaults to 'None'.
            name (): Name of the analyte. Defaults to None
            inchi (): InCHI code of the molecule. Defaults to None
            molecular_weight (): Molar weight of the molecule in g/mol. Defaults to None
            retention_time (): Approximated retention time of the molecule. Defaults to None
            peaks (): All peaks of the dataset, which are within the same retention time interval related to the molecule. Defaults to ListPlus()
            injection_times (): Injection times of the molecule measured peaks. Defaults to ListPlus()
            concentrations (): Concentration of the molecule. Defaults to ListPlus()
            standard (): Standard, describing the signal-to-concentration relationship. Defaults to None
            role (): Role of the molecule in the experiment. Defaults to None
            reaction_times (): Reaction times of the molecule measured peaks. Defaults to ListPlus()
        """
        params = {
            "name": name,
            "inchi": inchi,
            "molecular_weight": molecular_weight,
            "retention_time": retention_time,
            "peaks": peaks,
            "injection_times": injection_times,
            "concentrations": concentrations,
            "standard": standard,
            "role": role,
            "reaction_times": reaction_times,
        }
        if id is not None:
            params["id"] = id
        self.analytes.append(Analyte(**params))
        return self.analytes[-1]

    def add_to_measurements(
        self,
        chromatograms: List[Chromatogram] = ListPlus(),
        timestamp: Optional[Datetime] = None,
        injection_volume: Optional[float] = None,
        dilution_factor: Optional[float] = None,
        injection_volume_unit: Optional[Unit] = None,
        reaction_time: Optional[float] = None,
        id: Optional[str] = None,
    ) -> Measurement:
        """
        This method adds an object of type 'Measurement' to attribute measurements

        Args:
            id (str): Unique identifier of the 'Measurement' object. Defaults to 'None'.
            chromatograms (): Measured signal. Defaults to ListPlus()
            timestamp (): Timestamp of sample injection into the column. Defaults to None
            injection_volume (): Injection volume. Defaults to None
            dilution_factor (): Dilution factor. Defaults to None
            injection_volume_unit (): Unit of injection volume. Defaults to None
            reaction_time (): Reaction time. Defaults to None
        """
        params = {
            "chromatograms": chromatograms,
            "timestamp": timestamp,
            "injection_volume": injection_volume,
            "dilution_factor": dilution_factor,
            "injection_volume_unit": injection_volume_unit,
            "reaction_time": reaction_time,
        }
        if id is not None:
            params["id"] = id
        self.measurements.append(Measurement(**params))
        return self.measurements[-1]

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
        chromatograms = self.get(path="measurements/chromatograms")[0]
        detectors = [chromatogram.type for chromatogram in chromatograms]

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
        times, peaks = self._get_peaks_by_retention_time(
            retention_time=retention_time, tolerance=tolerance, detector=detector
        )

        analyte = Analyte(
            name=name,
            inchi=inchi,
            retention_time=retention_time,
            molecular_weight=molecular_weight,
            peaks=peaks,
            injection_times=times,
            role=role,
        )

        if calibration_factor is not None:
            analyte.standard = Standard(factor=calibration_factor)

        return analyte

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

    def _get_peaks_by_retention_time(
        self,
        retention_time: float,
        detector: SignalType,
        tolerance: float = 0.1,
    ) -> "Tuple[List[Datetime], List[Peak]]":
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

        times = []
        peaks = []
        sorted_measurements = sorted(self.measurements, key=lambda x: x.timestamp)

        for measurement in sorted_measurements:
            time = measurement.timestamp

            chromatogram = measurement.get_detector(detector)

            peaks_in_retention_interval = self._get_peaks_in_retention_interval(
                chromatogram=chromatogram,
                lower_retention_time=lower_ret,
                upper_retention_time=upper_ret,
            )

            if len(peaks_in_retention_interval) == 1:
                times.append(time)
                peaks.append(peaks_in_retention_interval[0])

            elif len(peaks_in_retention_interval) == 0:
                warnings.warn(
                    "No peak annotated within retention time interval"
                    f" [{lower_ret:.2f} : {upper_ret:.2f}] for masurement at"
                    f" {time} from {detector} found. Skipping measurement."
                )

            else:
                raise ValueError(
                    f"Multiple {len(peaks_in_retention_interval)} peaks found within"
                    f"retention time interval [{lower_ret} : {upper_ret}]"
                )

        assert len(times) == len(peaks)
        return times, peaks

    def visualize_chromatograms(self, color_scale: str = "Turbo"):
        fig = go.Figure()

        colors = self._sample_colorscale(len(self.measurements), color_scale)
        for color, measurement in zip(colors, self.measurements):
            for chromatogram in measurement.chromatograms:
                fig.add_trace(
                    go.Scatter(
                        x=chromatogram.retention_times,
                        y=chromatogram.signals,
                        mode="lines",
                        name=f"{measurement.timestamp.time()}",
                        customdata=[chromatogram.type],
                        line=dict(color=color),
                        hovertemplate=(
                            "<br>Retention Time: %{x:.2f} min<br>Signal:"
                            " %{y:.2f}<extra></extra>"
                        ),
                    )
                )

        fig.update_xaxes(title_text=f"Retention Time / {chromatogram.time_unit.name} ")
        fig.update_yaxes(title_text="Signal")
        fig.update_layout(legend_title_text="Injection Time")

        return fig

    def visualize_peaks(self, detector: SignalType = None, color_scale: str = "Turbo"):
        detector = self._handel_detector(detector)

        df = pd.DataFrame(self._get_peak_records())
        df = df[df["signal_type"] == detector]

        return px.scatter(
            x=df["timestamp"],
            y=df["retention_time"],
            color=df["area"],
            labels=dict(
                x="Injection Time", y="retention time / min", color="Peak Area"
            ),
        )

    def _get_peak_records(self) -> List[dict]:
        records = []
        for measurement in self.measurements:
            for chromatogram in measurement.chromatograms:
                for peak in chromatogram.peaks:
                    peak_data = dict(
                        timestamp=measurement.timestamp,
                        signal_type=chromatogram.type,
                        peak_id=peak.id,
                        retention_time=peak.retention_time,
                        area=peak.area,
                        height=peak.height,
                        width=peak.width,
                    )

                    records.append(peak_data)

        return records

    def add_internal_standard(
        self,
        name: str,
        retention_time: float,
        molecular_weight: float,
        detector: SignalType,
        inchi: str = None,
        tolerance: float = 0.1,
    ) -> Analyte:
        internal_standard = self._set_analyte(
            name=name,
            retention_time=retention_time,
            role=Role.STANDARD,
            molecular_weight=molecular_weight,
            inchi=inchi,
            tolerance=tolerance,
            detector=detector,
        )

        self.analytes.append(internal_standard)

        return internal_standard

    def calculate_concentrations(
        self,
        analytes: List[Analyte] = None,
        internal_standard: Analyte = None,
    ):
        if not internal_standard:
            internal_standard = [
                analyte
                for analyte in self.analytes
                if analyte.role == Role.STANDARD.value
            ][0]

        if not analytes:
            analytes = [
                analyte
                for analyte in self.analytes
                if analyte.role == Role.ANALYTE.value
            ]

        entries = []

        for peak, injection_time in zip(
            internal_standard.peaks, internal_standard.injection_times
        ):
            standard_area = peak.area

            for analyte in analytes:
                analyte_peak = analyte.get_peak_by_injection_time(injection_time)
                if not analyte_peak:
                    continue

                # print(
                #     analyte.name,
                #     analyte_area,
                #     standard_area,
                #     analyte.standard.factor,
                #     internal_standard.molecular_weight,
                # )
                analyte_conc = (
                    analyte_peak.area
                    / standard_area
                    / analyte.standard.factor
                    * internal_standard.molecular_weight
                )
                analyte.concentrations.append(analyte_conc)

                entries.append({
                    "analyte": analyte.name,
                    "injection_time": injection_time,
                    "concentration": analyte_conc,
                })
                # print(
                #     f"Concentration of {analyte.name} at {injection_time} is {analyte_conc:.2f}"
                # )

        df = pd.DataFrame(entries)
        df = df.pivot_table(
            index="injection_time",
            columns="analyte",
            values="concentration",
            aggfunc="first",
        )
        df.reset_index(inplace=True)
        df.columns.name = None

        # df.drop("analyte", axis=1, inplace=True)

        df["injection_time"] = pd.to_datetime(df["injection_time"])

        df["relative_time"] = (
            df["injection_time"] - df["injection_time"].iloc[0]
        ).dt.total_seconds()

        return df

    @staticmethod
    def _sample_colorscale(size: int, plotly_scale: str) -> List[str]:
        return px.colors.sample_colorscale(
            plotly_scale, [i / size for i in range(size)]
        )

    @property
    def injection_times(self):
        # convert timestamps to relative times
        start_time = self.measurements[0].timestamp
        relative_times = [
            (measurement.timestamp - start_time).total_seconds()
            for measurement in self.measurements
        ]
        return relative_times

    def visualize_concentrations(self, analytes: List[Analyte] = None):
        if analytes is None:
            analytes = [
                analyte
                for analyte in self.analytes
                if analyte.role == Role.ANALYTE.value
            ]

        fig = go.Figure()

        for analyte in analytes:
            fig.add_trace(
                go.Scatter(
                    x=analyte.injection_times,
                    y=analyte.concentrations,
                    # mode is lines and markers
                    mode="lines+markers",
                    name=analyte.name,
                    hovertemplate=(
                        "<br>Time: %{x}<br>Concentration:"
                        " %{y:.2f} mmol/l<extra></extra>"
                    ),
                )
            )

        fig.update_xaxes(title_text="Time")

        fig.update_yaxes(title_text="Concentration / mmol l<sup>-1<sup>")

        return fig

    def get_calibrator(analyte: Analyte, concentrations: List[float]) -> Calibrator:
        # TODO: Add species_id to data model

        signals = [peak.area for peak in analyte.peaks]
        assert len(signals) == len(concentrations), (
            f"Number of signals {len(signals)} and concentrations {concentrations} must"
            " be equal"
        )

        calibration = Calibrator(
            signals=signals, concentrations=concentrations, species_id=analyte.name
        ).calibrate()

        return calibration

    def concentration_to_df(self, analytes: List[Analyte] = None):
        if analytes is None:
            analytes = [
                analyte
                for analyte in self.analytes
                if analyte.role == Role.ANALYTE.value
            ]

        data = []
        for analyte in analytes:
            for injection_time, concentration in zip(
                analyte.injection_times, analyte.concentrations
            ):
                data.append({
                    "analyte": analyte.name,
                    "injection_time": injection_time,
                    "concentration": concentration,
                })

        # Create DataFrame
        df = pd.DataFrame(data)

        df["injection_time"] = pd.to_datetime(df["injection_time"])

        # Pivot the DataFrame
        df = df.pivot_table(
            index="injection_time",
            columns="analyte",
            values="concentration",
            aggfunc="first",
        )

        earliest_time = df.index.min()

        df["relative_time"] = (
            pd.Series(df.index)
            .apply(lambda x: (x - earliest_time).total_seconds())
            .values
        )

        df.set_index("relative_time", inplace=True)
        df.columns.name = None
        df.rename_axis("relative time [s]", inplace=True)
        df.columns = [col + " [mmol/l]" for col in df.columns]

        # Your pivoted DataFrame now has a 'relative_time' column
        return df

    def concentrations_to_csv(self, path: str, analytes: List[Analyte] = None):
        df = self.concentration_to_df(analytes)
        df.to_csv(path)
