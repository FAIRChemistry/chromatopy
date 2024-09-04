from __future__ import annotations

import numpy as np
from lmfit.models import GaussianModel
from matplotlib import pyplot as plt
from pybaselines import Baseline
from pydantic import BaseModel
from rich import print
from scipy.ndimage import uniform_filter1d
from scipy.signal import find_peaks

# from chromatopy.model import UnitDefinition


class PeakFitResult(BaseModel):
    peak_index: int
    amplitude: float
    center: float
    width: float
    mode: str
    area: float | None = None  # You can calculate and store the area if needed

    def calculate_area(self, model: str = "gaussian"):
        """Calculates the area under the peak based on the model."""
        models = ("gaussian", "lorentzian")

        if model == "gaussian":
            # For Gaussian: Area = Amplitude * Width * sqrt(2*pi)
            self.area = self.amplitude * self.width * np.sqrt(2 * np.pi)
        elif model == "lorentzian":
            # For Lorentzian: Area = Amplitude * Width * pi
            self.area = self.amplitude * self.width * np.pi

        else:
            raise ValueError(f"Model {model} not supported. Choose from {models}.")


class SpectrumProcessor(BaseModel):
    time: list[float]
    raw_data: list[float]
    smoothed_data: list[float] = []
    baseline: list[float] = []
    baseline_corrected_data: list[float] = []
    peak_indices: list[int] = []
    peak_params: list[PeakFitResult] = []
    silent: bool = False
    # time_unit: UnitDefinition

    def smooth_data(self, window: int = 11) -> list[float]:
        """Smooths the raw data using a uniform filter.

        Args:
            window (int, optional): The size of the window. Defaults to 11.
        """
        self._remove_nan()

        filtered = uniform_filter1d(self.raw_data, size=window)
        if not self.silent:
            print("Data smoothed.")
        return filtered

    # private method that checks the data for nan values adn removes them, deletes the corresponding time values
    def _remove_nan(self) -> None:
        """Removes NaN values from the data and the corresponding time values."""
        self.raw_data = [d for d in self.raw_data if not np.isnan(d)]
        self.time = [t for t, d in zip(self.time, self.raw_data) if not np.isnan(d)]

    def correct_baseline(self) -> None:
        # smooth the data
        self.smoothed_data = self.smooth_data(window=11)

        baseliner = Baseline(self.smoothed_data)

        self.baseline = baseliner.mor(self.smoothed_data)[0]
        self.baseline_corrected_data = self.smoothed_data - self.baseline

        if not self.silent:
            print("Baseline corrected.")

    def search_peaks(self):
        peaks, _ = find_peaks(self.baseline_corrected_data, height=None, prominence=4)
        self.peak_indices = peaks

        if not self.silent:
            print(f"Found {len(peaks)} peaks.")

    def fit_multiple_gaussians(self):
        """
        Fits multiple Gaussians to the baseline-corrected data using the peaks found.

        Returns:
            dict: A dictionary containing the fit results and individual component fits.
        """
        # Check if peak_indices is empty
        if self.peak_indices is None or len(self.peak_indices) == 0:
            raise ValueError("No peaks found. Run search_peaks() first.")

        # Create a combined model by summing Gaussian models for each peak
        mod = None
        pars = None
        for i, peak in enumerate(self.peak_indices, start=1):
            prefix = f"g{i}_"
            gauss = GaussianModel(prefix=prefix)
            center = self.time[peak]
            amplitude = self.baseline_corrected_data[peak]
            sigma = (
                self.time[min(len(self.time) - 1, peak + 10)]
                - self.time[max(0, peak - 10)]
            ) / 2.355  # FWHM estimate

            if mod is None:
                mod = gauss
            else:
                mod += gauss

            # Update parameters with initial guesses
            if pars is None:
                pars = gauss.make_params(
                    center=center, sigma=sigma, amplitude=amplitude
                )
            else:
                pars.update(
                    gauss.make_params(center=center, sigma=sigma, amplitude=amplitude)
                )

        # Fit the combined model to the data
        out = mod.fit(self.baseline_corrected_data, pars, x=np.array(self.time))

        # Extract the peak parameters
        self.peak_params = [
            PeakFitResult(
                peak_index=i,
                amplitude=out.params[f"g{i}_amplitude"].value,
                center=out.params[f"g{i}_center"].value,
                width=out.params[f"g{i}_sigma"].value,
                mode="gaussian",
            )
            for i in range(1, len(self.peak_indices) + 1)
        ]

        if not self.silent:
            print("Fitted Gaussians to peaks.")

    def run_pripeline(self):
        self.correct_baseline()
        self.search_peaks()
        self.fit_multiple_gaussians()
        self.calculate_peak_areas()

    def plot(self):
        plt.plot(self.time, self.raw_data, label="Raw Data")
        plt.plot(self.time, self.baseline, "--", label="Baseline")
        plt.plot(self.time, self.baseline_corrected_data, label="Corrected")
        # highlight peaks
        plt.plot(
            [self.time[i] for i in self.peak_indices],
            [self.baseline_corrected_data[i] for i in self.peak_indices],
            "x",
            label="Peaks",
        )
        # plot the fitted Gaussians
        for peak in self.peak_params:
            gaussian = GaussianModel()
            peak_start = max(0, int(peak.center - 3 * peak.width))
            peak_end = min(len(self.time) - 1, int(peak.center + 3 * peak.width))
            x_arr = np.array(self.time[peak_start:peak_end])
            plt.plot(
                x_arr,
                gaussian.eval(
                    x=x_arr,
                    amplitude=peak.amplitude,
                    center=peak.center,
                    sigma=peak.width,
                ),
                ":",
                label=f"Peak {peak.peak_index}",
            )
        plt.legend()
        plt.show()

    def calculate_peak_areas(self):
        for peak in self.peak_params:
            peak.calculate_area()

        if not self.silent:
            print("Calculated peak areas.")


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    from chromatopy.tools.analyzer import ChromAnalyzer
    from chromatopy.units import min as min_

    path = "/Users/max/Documents/jan-niklas/MjNK"

    reaction_times = [0.0] * 18

    ana = ChromAnalyzer.read_chromeleon(
        path=path,
        reaction_times=reaction_times,
        time_unit=min_,
        ph=7.4,
        temperature=25.0,
    )

    chrom = ana.measurements[2].chromatograms[0]
    # Check if chrom.times is not empty, contains only floats, and has the expected length

    fitter = SpectrumProcessor(time=chrom.times, raw_data=chrom.signals)
    fitter.correct_baseline()
    fitter.search_peaks()
    fitter.fit_multiple_gaussians()
    fitter.calculate_peak_areas()
    print(fitter.peak_params[0])
    fitter.plot()

    print(fitter.baseline_corrected_data)
