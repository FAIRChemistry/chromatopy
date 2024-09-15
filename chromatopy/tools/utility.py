import sys

import numpy as np
import plotly.graph_objects as go
from loguru import logger
from matplotlib import pyplot as plt
from pyenzyme import DataTypes, EnzymeMLDocument

from chromatopy.model import Chromatogram, UnitDefinition

logger.remove()
logger.add(sys.stderr, level="INFO")


def _resolve_chromatogram(
    chromatograms: list[Chromatogram], wavelength: float | None
) -> Chromatogram:
    if len(chromatograms) == 1:
        return chromatograms[0]

    if len(chromatograms) > 1:
        assert (
            wavelength is not None
        ), "Multiple chromatograms found, but no wavelength is specified."

        # check that any of the chromatograms has the specified wavelength
        assert any(
            [chrom.wavelength == wavelength for chrom in chromatograms]
        ), f"No chromatogram found with wavelength {wavelength} nm."

        return next(chrom for chrom in chromatograms if chrom.wavelength == wavelength)

    raise ValueError("No chromatogram found.")


def pick_peak(
    chromatograms: list[Chromatogram], retention_time: float, tolerance: float
):
    current_retention = retention_time
    peaks = []

    for chrom in chromatograms:
        for peak in chrom.peaks:
            if abs(peak.retention_time - current_retention) < tolerance:
                peaks.append(peak)
                current_retention = peak.retention_time
        else:
            pass


def generate_visibility(hover_text: str, fig: go.Figure) -> list[bool]:
    visibility = []
    for trace in fig.data:
        if trace.hovertext == hover_text:
            visibility.append(True)
        else:
            visibility.append(False)
    return visibility


def generate_gaussian_data(
    amplitude, center, half_height_diameter, start, end, num_points=100
):
    """
    Generate x and y data for a Gaussian curve.

    Parameters:
    - amplitude: The peak height of the Gaussian.
    - center: The position of the center of the peak.
    - half_height_diameter: The full width at half maximum (FWHM) of the peak.
    - start: The starting x-value.
    - end: The ending x-value.
    - num_points: Number of points to generate (default is 100).

    Returns:
    - x_values: Array of x-values.
    - y_values: Array of y-values corresponding to the Gaussian curve.
    """
    # Calculate sigma from the half-height diameter (FWHM)
    sigma = half_height_diameter / (2 * np.sqrt(2 * np.log(2)))

    # Generate x values
    x_values = np.linspace(start, end, num_points)

    # Generate y values using the Gaussian function
    y_values = amplitude * np.exp(-((x_values - center) ** 2) / (2 * sigma**2))

    return x_values, y_values


def visualize_enzymeml(enzymeml_doc: EnzymeMLDocument):
    """visualize the data in the EnzymeML document

    Args:
        enzymeml_doc (EnzymeMLDocument): The EnzymeML document to visualize
    """
    for species in enzymeml_doc.measurements[0].species_data:
        if species.data:
            plt.scatter(
                species.time,
                species.data,
                label=get_species_by_id(enzymeml_doc, species.species_id).name,
            )
    plt.legend()

    # handel y label
    if species.data_type == DataTypes.PEAK_AREA:
        plt.ylabel("Peak Area [-]")
    elif species.data_type == DataTypes.CONCENTRATION:
        plt.ylabel(f"concentration [{unit_to_str(species.data_unit)}]")
    plt.xlabel(f"reaction time [{unit_to_str(species.time_unit)}]")
    plt.show()


def get_species_by_id(enzymeml_doc: EnzymeMLDocument, species_id: str):
    for species in enzymeml_doc.small_molecules:
        if species.id == species_id:
            return species


def unit_to_str(unit: UnitDefinition) -> str:
    magnitude_dict = {
        1: "",
        -1: "",
        -3: "m",
        -6: "µ",
        -9: "n",
        -12: "p",
    }

    # Handle single base unit cases
    if len(unit.base_units) == 1:
        base_unit = unit.base_units[0]

        if base_unit.kind.value == "second":
            if base_unit.multiplier == 1:
                return "s"
            elif base_unit.multiplier == 60:
                return "min"
            elif base_unit.multiplier == 3600:
                return "h"
            else:
                return unit.name or ""
        else:
            return unit.name or ""

    # Handle mole per litre cases
    elif len(unit.base_units) == 2:
        u1, u2 = unit.base_units
        if u1.kind.value == "mole" and u2.kind.value == "litre" and u2.exponent == -1:
            return f"{magnitude_dict[u1.scale]}M"
        else:
            return unit.name or ""

    # Default return for other cases
    return unit.name or ""


###########

# def _apply_calibrators(calibrators = list[Calibrator]):
#     if not self.calibrators:
#         raise ValueError("No calibrators provided. Define calibrators first.")

#     if not self.molecules:
#         raise ValueError("No species provided. Define species first.")

#     for calibrator in self.calibrators:
#         calib_species = self.get_molecule(calibrator.name)
#         if not calib_species.peaks:
#             continue

#         calib_species.concentrations = calibrator.calculate(species=calib_species)

###########
# def apply_standards(self, tolerance: float = 1):
#     data = defaultdict(list)

#     for standard in self.molecules:
#         lower_ret = standard.retention_time - tolerance
#         upper_ret = standard.retention_time + tolerance
#         calibrator = Calibrator.from_standard(standard)
#         model = calibrator.models[0]

#         for meas in self.measurements:
#             for chrom in meas.chromatograms:
#                 for peak in chrom.peaks:
#                     if lower_ret < peak.retention_time < upper_ret:
#                         data[standard.name].append(
#                             calibrator.calculate_concentrations(
#                                 model=model, signals=[peak.area]
#                             )[0]
#                         )

#     return data
