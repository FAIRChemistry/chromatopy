from datetime import datetime as Datetime
from typing import Dict, List, Optional
from uuid import uuid4

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sdRDM
from hplc.quant import Chromatogram as hplcChromatogram
from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM.base.datatypes import Unit
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict

from .peak import Peak
from .signaltype import SignalType


@forge_signature
class Chromatogram(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    peaks: List[Peak] = element(
        description="Peaks in the signal",
        default_factory=ListPlus,
        tag="peaks",
        json_schema_extra=dict(multiple=True),
    )

    retention_times: List[float] = element(
        description="Retention times of the signal",
        default_factory=ListPlus,
        tag="retention_times",
        json_schema_extra=dict(multiple=True),
    )

    time_unit: Optional[Unit] = element(
        description="Unit of retention time",
        default=None,
        tag="time_unit",
        json_schema_extra=dict(),
    )

    signals: List[float] = element(
        description="Signal values",
        default_factory=ListPlus,
        tag="signals",
        json_schema_extra=dict(multiple=True),
    )

    processed_signal: List[float] = element(
        description=(
            "Processed signal values after baseline correction and deconvolution"
        ),
        default_factory=ListPlus,
        tag="processed_signal",
        json_schema_extra=dict(multiple=True),
    )

    wavelength: Optional[float] = element(
        description="Wavelength of the signal in nm",
        default=None,
        tag="wavelength",
        json_schema_extra=dict(),
    )

    type: Optional[SignalType] = element(
        description="Type of signal",
        default=None,
        tag="type",
        json_schema_extra=dict(),
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

    def add_to_peaks(
        self,
        analyte_id: Optional[str] = None,
        retention_time: Optional[float] = None,
        timestamp: Optional[Datetime] = None,
        retention_time_unit: Optional[Unit] = None,
        type: Optional[str] = None,
        peak_start: Optional[float] = None,
        peak_end: Optional[float] = None,
        width: Optional[float] = None,
        width_unit: Optional[Unit] = None,
        area: Optional[float] = None,
        area_unit: Optional[Unit] = None,
        height: Optional[float] = None,
        height_unit: Optional[Unit] = None,
        percent_area: Optional[float] = None,
        tailing_factor: Optional[float] = None,
        separation_factor: Optional[float] = None,
        id: Optional[str] = None,
    ) -> Peak:
        """
        This method adds an object of type 'Peak' to attribute peaks

        Args:
            id (str): Unique identifier of the 'Peak' object. Defaults to 'None'.
            analyte_id (): ID of the analyte. Defaults to None
            retention_time (): Retention time of the peak. Defaults to None
            timestamp (): Timestamp of the peak. Defaults to None
            retention_time_unit (): Unit of retention time. Defaults to None
            type (): Type of peak (baseline-baseline / baseline-valley / ...). Defaults to None
            peak_start (): Start retention time of the peak. Defaults to None
            peak_end (): End retention time of the peak. Defaults to None
            width (): Width of the peak. Defaults to None
            width_unit (): Unit of width. Defaults to None
            area (): Area of the peak. Defaults to None
            area_unit (): Unit of area. Defaults to None
            height (): Height of the peak. Defaults to None
            height_unit (): Unit of height. Defaults to None
            percent_area (): Percent area of the peak. Defaults to None
            tailing_factor (): Tailing factor of the peak. Defaults to None
            separation_factor (): Separation factor of the peak. Defaults to None
        """
        params = {
            "analyte_id": analyte_id,
            "retention_time": retention_time,
            "timestamp": timestamp,
            "retention_time_unit": retention_time_unit,
            "type": type,
            "peak_start": peak_start,
            "peak_end": peak_end,
            "width": width,
            "width_unit": width_unit,
            "area": area,
            "area_unit": area_unit,
            "height": height,
            "height_unit": height_unit,
            "percent_area": percent_area,
            "tailing_factor": tailing_factor,
            "separation_factor": separation_factor,
        }
        if id is not None:
            params["id"] = id
        self.peaks.append(Peak(**params))
        return self.peaks[-1]

    @classmethod
    def from_csv(cls, path: str, time_unit: Unit) -> "Chromatogram":
        """
        This method reads a chromatogram from a CSV file

        Args:
            path (str): Path to the CSV file
        """
        df = pd.read_csv(path, header=None)
        retention_times = df[0].values.tolist()
        signals = df[1].values.tolist()

        return cls(
            retention_times=retention_times,
            signals=signals,
            time_unit=time_unit,
        )

    def fit(
        self,
        visualize: bool = False,
        **hplc_py_kwargs,
    ) -> hplcChromatogram:
        """
        Fit the chromatogram peaks using the `hplc-py` `Chromatogram` class.

        Parameters:
            visualize (bool, optional): Whether to visualize the fitted peaks. Defaults to False.
            **hplc_py_kwargs: Additional keyword arguments to pass to the hplc.quant.Chromatogram.fit_peaks() method.

        Returns:
            hplcChromatogram: The fitted chromatogram.
        """
        fitter = hplcChromatogram(file=self.to_dataframe())
        fitter.fit_peaks(**hplc_py_kwargs)
        if visualize:
            fitter.show()
        self.peaks = self._map_hplcpy_peaks(fitter.peaks)
        self.processed_signal = np.sum(fitter.unmixed_chromatograms, axis=1)

        return fitter

    def _map_hplcpy_peaks(self, fitter_peaks: pd.DataFrame) -> List[Peak]:
        peaks = fitter_peaks.to_dict(orient="records")
        return [
            Peak(
                retention_time=peak["retention_time"],
                retention_time_unit=self.time_unit,
                area=peak["area"],
                height=peak["amplitude"],
            )
            for peak in peaks
        ]

    def to_dataframe(self) -> pd.DataFrame:
        """
        Returns the chromatogram as a pandas DataFrame with the columns 'time' and 'signal'
        """
        return pd.DataFrame({
            "time": self.retention_times,
            "signal": self.signals,
        })

    def visualize(self) -> go.Figure:
        """
        Plot the chromatogram.

        This method creates a plot of the chromatogram using the plotly library.
        It adds a scatter trace for the retention times and signals, and if there are peaks present, it adds vertical lines for each peak.

        Returns:
            go.Figure: The plotly figure object.
        """
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=self.retention_times,
                y=self.signals,
                name="Signal",
            )
        )

        if self.peaks:
            for peak in self.peaks:
                fig.add_vline(
                    x=peak.retention_time,
                    line_dash="dash",
                    line_color="gray",
                )

        if self.processed_signal:
            fig.add_trace(
                go.Scatter(
                    x=self.retention_times,
                    y=self.processed_signal,
                    mode="lines",
                    line=dict(dash="dot", width=1),
                    name="Processed signal",
                )
            )

        fig.update_layout(
            xaxis_title=f"Retention time / {self.time_unit.name}",
            yaxis_title="Signal",
            height=600,
        )

        return fig
