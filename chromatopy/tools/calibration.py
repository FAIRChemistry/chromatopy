import logging
import warnings
from typing import List, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator
from scipy.stats import linregress
from sdRDM.base.datatypes import Unit

from chromatopy.tools.species import Species

LOGGER = logging.getLogger(__name__)


class Calibrator(BaseModel):
    name: str = Field()
    chebi: Optional[str] = Field(default=None)
    concentrations: Optional[List[float]] = Field(default=[])
    conc_unit: Unit = Field()
    signals: Optional[List[float]] = Field(default=[])
    slope: Optional[float] = Field(default=None)

    # Private attributes
    intercept: float = Field(default=0, private=True)
    r_value: float = Field(default=None, private=True)
    p_value: float = Field(default=None, private=True)
    std_err: float = Field(default=None, private=True)

    def __init__(
        self,
        name: str,
        conc_unit: str,
        chebi: str = None,
        concentrations: List[float] = [],
        signals: List[float] = [],
        slope: float = None,
        intercept: float = 0,
    ):
        super().__init__(
            name=name,
            chebi=chebi,
            conc_unit=conc_unit,
            concentrations=concentrations,
            signals=signals,
            slope=slope,
            intercept=intercept,
        )
        if concentrations and signals:
            self.calibrate()

    @field_validator("chebi", mode="before")
    def check_chebi(cls, v):
        if v is None:
            warnings.warn(
                "No value for 'chebi' provided; Consider setting a value for 'chebi'."
            )
        return None

    @field_validator("conc_unit", mode="before")
    def unit_from_string(cls, v):
        if isinstance(v, str):
            return Unit.from_string(v)

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

        symbol = "" if self.r_value >= 0.95 else "❗️ "

        print(f"🎯 Calibration model created.\n{symbol}R²: {self.r_value:.4f}")

    def calculate(self, signals: List[float] = None, species: Species = None):
        """Calculate the concentration of the species based on the signal"""

        if not signals and species:
            return self.calculate_species_concs(species)
        elif signals and not species:
            return [self._calculate(signal) for signal in signals]
        else:
            raise ValueError("Either signals or species must be provided.")

    def _calculate(self, signal: float) -> float:
        """Calculate the concentration of the species based on the signal.

        Args:
            signal (float): Signal from the detector.

        Returns:
            float: Concentration of the species.
        """
        if self.signals:
            if signal > max(self.signals):
                LOGGER.warning(
                    f"Signal {signal} is above the maximum calibration point {max(self.signals)}"
                )

        return float((signal - self.intercept) / self.slope)

    def calculate_species_concs(self, species: Species) -> List[float]:
        """Calculate the concentration of the species based on the signal.

        Args:
            species (Species): Species object.

        Returns:
            List[float]: Concentration of the species.
        """
        try:
            assert self.chebi == species.chebi, "Chebi does not match"
        except AssertionError as e:
            if self.name.lower() != species.name.lower():
                raise e

        return [self._calculate(peak.area) for peak in species.peaks]

    def plot(self):
        """Plot the calibration curve."""
        import matplotlib.pyplot as plt

        model_range = np.linspace(min(self.concentrations), max(self.concentrations), 2)
        plt.plot(
            model_range,
            self.slope * model_range + self.intercept,
            "--",
            label=r"$R^2$ = %.4f" % self.r_value,
            color="tab:blue",
        )
        plt.scatter(self.concentrations, self.signals)
        plt.xlabel(f"{self.name} ({self.conc_unit._unit._repr_latex_()})")
        plt.ylabel("Signal")
        plt.legend()
        plt.show()

    @classmethod
    def from_species(
        cls,
        species: Species,
        concentrations: Optional[List[float]],
        conc_unit: Unit,
    ):
        """Create a calibrator object from a species object.

        Args:
            species (Species): Species object.
            concentrations (Optional[List[float]]): Respective concentrations
               matching the peaks areas of the `Species`.
            conc_unit (str): Unit of the concentration.

        Returns:
            _type_: _description_
        """
        assert len(concentrations) == len(
            species.peaks
        ), "Concentration and signal must have the same length"

        return cls(
            chebi=species.chebi,
            name=species.name,
            concentrations=concentrations,
            conc_unit=conc_unit,
            signals=[peak.area for peak in species.peaks],
        )

    def __repr__(self):
        concentration_range = (
            f"{min(self.concentrations, default='N/A')}-{max(self.concentrations, default='N/A')} {self.conc_unit.name}"
            if self.concentrations
            else "No concentrations"
        )
        signal_range = (
            f"{min(self.signals, default='N/A')}-{max(self.signals, default='N/A')}"
            if self.signals
            else "No signals"
        )
        slope_info = f"Slope: {self.slope}" if self.slope is not None else "Slope: None"

        return (
            f"Name: {self.name}\n"
            f"Chebi: {self.chebi}\n"
            f"Concentration Range: {concentration_range}\n"
            f"Signal Range: {signal_range}\n"
            f"{slope_info}"
        )


if __name__ == "__main__":
    calibrator = Calibrator(
        species_id="CO2",
        concentrations=[0, 100, 200, 300, 400],
        conc_unit="ppm",
        signals=[0, 1, 2, 3, 4],
    )
    calibrator.calibrate()
    print(calibrator.calculate(2.5))
