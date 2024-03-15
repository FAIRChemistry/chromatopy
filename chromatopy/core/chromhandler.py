import sdRDM

import numpy as np
import warnings
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.base.datatypes import Unit
from sdRDM.tools.utils import elem2dict
from datetime import datetime as Datetime
from .standard import Standard
from .chromatogram import Chromatogram
from .analyte import Analyte
from .peak import Peak
from .role import Role
from .measurement import Measurement
from .signaltype import SignalType
from ..readers.abstractreader import AbstractReader


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
        injection_volume_unit: Optional[Unit] = None,
        id: Optional[str] = None,
    ) -> Measurement:
        """
        This method adds an object of type 'Measurement' to attribute measurements

        Args:
            id (str): Unique identifier of the 'Measurement' object. Defaults to 'None'.
            chromatograms (): Measured signal. Defaults to ListPlus()
            timestamp (): Timestamp of sample injection into the column. Defaults to None
            injection_volume (): Injection volume. Defaults to None
            injection_volume_unit (): Unit of injection volume. Defaults to None
        """
        params = {
            "chromatograms": chromatograms,
            "timestamp": timestamp,
            "injection_volume": injection_volume,
            "injection_volume_unit": injection_volume_unit,
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
        molecular_weight: float = None,
        inchi: str = None,
        tolerance: float = 0.1,
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

    @classmethod
    def read(cls, path: str, reader: AbstractReader):
        """
        Reads data from a file or directory using the specified reader.

        Args:
            path (str): The path to the file or directory.
            reader (AbstractReader): The reader object used to read the data.

        Returns:
            ChromHandler: An instance of the ChromHandler class initialized with the read data.

        Raises:
            FileNotFoundError: If the specified path does not exist.
            NotADirectoryError: If the specified path is not a directory when it should be.
            FileNotFoundError: If the specified path is not a file when it should be.

        """

        measurements = reader(path).read()
        instance = cls(measurements=measurements)

        # sort measurements by timestamp
        instance.measurements = sorted(instance.measurements, key=lambda x: x.timestamp)
        return instance

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
            standard_areas = np.array([peak.area for peak in internal_standard.peaks])

        if not analytes:
            analytes = [
                analyte
                for analyte in self.analytes
                if analyte.role == Role.ANALYTE.value
            ]

        for analyte in analytes:
            analyte_areas = np.array([peak.area for peak in analyte.peaks])
            analyte_concs = (
                analyte_areas
                / standard_areas
                / analyte.standard.factor
                * internal_standard.molecular_weight
            )

        return analyte_concs

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
