import logging
from typing import List, Optional

from pydantic import BaseModel, Field
from scipy.stats import linregress

LOGGER = logging.getLogger(__name__)


class Calibrator(BaseModel):
    species_id: str = Field()
    concentrations: Optional[List[float]] = Field(default=[])
    conc_unit: str = Field()
    signals: Optional[List[float]] = Field(default=[])
    slope: Optional[float] = Field(default=None)

    # Private attributes
    intercept: float = Field(default=0, private=True)
    r_value: float = Field(default=None, private=True)
    p_value: float = Field(default=None, private=True)
    std_err: float = Field(default=None, private=True)

    def calibrate(self):
        """Calibrate the detector using the calibration points."""
        slope, intercept, r_value, p_value, std_err = linregress(
            self.concentrations, self.signals
        )
        self.slope = float(slope)
        self.intercept = float(intercept)
        self.r_value = float(r_value)
        self.p_value = float(p_value)
        self.std_err = float(std_err)

    def calculate(self, signal: float) -> float:
        """Calculate the concentration of the species based on the signal.

        Args:
            signal (float): Signal from the detector.

        Returns:
            float: Concentration of the species.
        """
        if self.signals:
            if self.signals > max(self.signals):
                LOGGER.warning(
                    f"Signal {signal} is above the maximum calibration point {max(self.signals)}"
                )

        return float((signal - self.intercept) / self.slope)

    def plot(self):
        """Plot the calibration curve."""
        import matplotlib.pyplot as plt

        plt.plot(self.concentrations, self.signals, "o")
        plt.xlabel(f"{self.species_id} ({self.conc_unit})")
        plt.ylabel("Signal")
        plt.show()


if __name__ == "__main__":
    calibrator = Calibrator(
        species_id="CO2",
        concentrations=[0, 100, 200, 300, 400],
        conc_unit="ppm",
        signals=[0, 1, 2, 3, 4],
    )
    calibrator.calibrate()
    print(calibrator.calculate(2.5))
