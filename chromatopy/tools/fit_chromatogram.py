import numpy as np
import pandas as pd
from hplc.quant import Chromatogram as hplcChromatogram
from plotly import graph_objects as go

from chromatopy.model import Peak

# from chromatopy.tools.species import Species


class ChromFit:
    def __init__(self, signals: list[float], times: list[float]):
        self.signals = signals
        self.times = times
        self.prcessed_signal: list[float] = []
        self.peaks: list[Peak] = []
        self._remove_nan()

    def fit(
        self,
        # molecules: Optional[list[Species]] = [],
        visualize: bool = False,
        tolerance: float = 0.1,
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
        # if not isinstance(molecules, list):
        #    molecules = [molecules]
        fitter = hplcChromatogram(file=self.to_dataframe())
        fitter.fit_peaks(**hplc_py_kwargs)
        if visualize:
            fitter.show()
        # self.peaks = self._map_hplcpy_peaks(fitter.peaks)
        self.processed_signal = np.sum(fitter.unmixed_chromatograms, axis=1)

        for record in fitter.peaks.to_dict(orient="records"):
            self.peaks.append(
                Peak(
                    retention_time=record["retention_time"],
                    area=record["area"],
                    height=record["amplitude"],
                )
            )

    def _map_hplcpy_peaks(self, fitter_peaks: pd.DataFrame) -> list[Peak]:
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
        return pd.DataFrame(
            {
                "time": self.times,
                "signal": self.signals,
            }
        ).dropna()

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
                x=self.times,
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
                    annotation_text=peak.retention_time,
                )

        if self.processed_signal:
            fig.add_trace(
                go.Scatter(
                    x=self.times,
                    y=self.processed_signal,
                    mode="lines",
                    line=dict(dash="dot", width=1),
                    name="Processed signal",
                )
            )

        if self.wavelength:
            wave_string = f"({self.wavelength} nm)"
        else:
            wave_string = ""

        fig.update_layout(
            xaxis_title=f"Retention time / {self.time_unit.name}",
            yaxis_title=f"Signal {wave_string}",
            height=600,
        )

        return fig
