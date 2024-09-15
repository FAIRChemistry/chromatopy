from __future__ import annotations

import os
import sys
from typing import Any

import numpy as np
import pandas as pd

# from scipy.ndimage import uniform_filter1d
# from scipy.signal import find_peaks
from hplc.quant import Chromatogram as hplcChromatogram

# from lmfit.models import GaussianModel
from loguru import logger

# from pybaselines import Baseline
from pydantic import BaseModel

from chromatopy.model import Peak

logger.remove()
logger.add(sys.stderr, level="INFO")


class SpectrumProcessor(BaseModel):
    time: list[float]
    raw_data: list[float]
    smoothed_data: list[float] = []
    baseline: list[float] = []
    processed_signal: list[float] = []
    peak_indices: list[int] = []
    peaks: list[Peak] = []
    silent: bool = False
    smooth_window: int = 11
    baseline_half_window: int | None = None
    peak_prominence: float = 4
    min_peak_height: float | None = None

    def model_post_init(self, __context: Any) -> None:
        self._remove_nan()

    def _remove_nan(self) -> None:
        """Removes NaN values from the data and the corresponding time values."""
        self.raw_data = [d for d in self.raw_data if not np.isnan(d)]
        self.time = [t for t, d in zip(self.time, self.raw_data) if not np.isnan(d)]

    def silent_fit(self, **hplc_py_kwargs) -> hplcChromatogram:
        """Wrapper function to suppress the output of the hplc-py Chromatogram.fit_peaks() method."""

        # Save the original stdout and stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        # Redirect stdout and stderr to /dev/null
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

        try:
            # Call the function that prints the unwanted output
            return self.fit(**hplc_py_kwargs)
        finally:
            # Restore the original stdout and stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def fit(
        self,
        **hplc_py_kwargs,
    ) -> SpectrumProcessor:
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
        try:
            fitter.fit_peaks(**hplc_py_kwargs)
        except KeyError as e:
            if "retention_time" in str(e):
                logger.info(
                    "No peaks found in the chromatogram. Halving the prominence and trying again."
                )
                hplc_py_kwargs["prominence"] /= 2
                self.fit(**hplc_py_kwargs)

        self.processed_signal = np.sum(fitter.unmixed_chromatograms, axis=1).tolist()

        peaks = []
        for record in fitter.peaks.to_dict(orient="records"):
            peaks.append(
                Peak(
                    retention_time=record["retention_time"],
                    area=record["area"],
                    amplitude=record["amplitude"],
                    skew=record["skew"],
                    width=record["scale"],
                    # max_signal=record["signal_maximum"],
                )
            )

        if len(peaks) > 0:
            peaks = sorted(peaks, key=lambda x: x.retention_time)

        self.peaks = peaks

        return self

    def to_dataframe(self) -> pd.DataFrame:
        """
        Returns the chromatogram as a pandas DataFrame with the columns 'time' and 'signal'
        """
        return pd.DataFrame(
            {
                "time": self.time,
                "signal": self.raw_data,
            }
        ).dropna()
