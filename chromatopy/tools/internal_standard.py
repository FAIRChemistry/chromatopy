from loguru import logger
from pydantic import BaseModel, Field

from chromatopy.model import Measurement, UnitDefinition
from chromatopy.tools.utility import _resolve_chromatogram

logger.level("INFO")


class InternalStandard(BaseModel):
    molecule_id: str = Field(description="The ID of the molecule.")

    standard_molecule_id: str = Field(description="The ID of the standard molecule.")

    molecule_init_conc: float = Field(
        description="The initial concentration of the molecule."
    )
    molecule_conc_unit: UnitDefinition = Field(
        description="The unit of concentration for the molecule."
    )
    standard_init_conc: float = Field(
        description="The initial concentration of the standard."
    )
    molecule_t0_signal: float | None = Field(
        description="The t0 signal of the molecule.", default=None
    )
    standard_t0_signal: float | None = Field(
        description="The t0 signal of the standard.", default=None
    )

    def _set_t0_signals(self, measurement: Measurement):
        """Sets the t0 signals of the molecule and the standard based on the data in the measurement."""

        assert measurement.reaction_time == 0, """
        No measurement data is available at t=0. Concentration calculation is not possible
        without a measurement at t=0.
        """

        for peak in _resolve_chromatogram(
            chromatograms=measurement.chromatograms, wavelength=None
        ).peaks:
            if peak.molecule_id == self.molecule_id:
                self.molecule_t0_signal = peak.area
            elif peak.molecule_id == self.standard_molecule_id:
                self.standard_t0_signal = peak.area

        assert self.molecule_t0_signal is not None, f"""
        No peak area for {self.molecule_id} was found in measurement at t=0.
        """

        assert self.standard_t0_signal is not None, f"""
        No peak area for {self.standard_molecule_id} was found in measurement at t=0.
        """

        logger.debug(
            f"molecule t0: {self.molecule_t0_signal}, standard t0: {self.standard_t0_signal}"
        )

    def calculate_conc(
        self, molecue_signal: float, standard_molecule_signal: float
    ) -> float:
        """Calculates the concentration of the internal standard based on the peak area.

        Args:
            molecue_signal (float): The signal of the molecule.
            standard_molecule_signal (float): The signal of the standard molecule.

        Returns:
            float: The concentration of the internal standard.
        """

        assert self.molecule_t0_signal is not None, """
        The t0 signal of the molecule is not defined.
        Use the `_set_t0_signals` method to set the t0 signals.
        """

        assert self.standard_t0_signal is not None, """
        The t0 signal of the standard is not defined.
        Use the `_set_t0_signals` method to set the t0 signals.
        """

        t0_ratio = self.molecule_t0_signal / self.standard_t0_signal
        ratio = molecue_signal / standard_molecule_signal

        conc = self.molecule_init_conc * (ratio / t0_ratio)

        logger.debug(f"initial conc: {self.molecule_init_conc}")
        logger.debug(f"t0 ratio: {t0_ratio}, ratio: {ratio}, conc: {conc}")

        return conc