from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chromatopy.core import ChromHandler
    from chromatopy.core import Molecule

from typing import List
from sdRDM import DataModel

# Specify EnzymeML version
URL = "https://github.com/EnzymeML/enzymeml-specifications.git"
COMMIT = "5e5f05b9dc76134305b8f9cef65271e35563ac76"

EnzymeML = DataModel.from_git(URL, COMMIT)
SBOTerm = EnzymeML.enums.SBOTerm
DataTypes = EnzymeML.enums.DataTypes


def map_to_enzymeml(chromatogram: "ChromHandler") -> "EnzymeML.EnzymeMLDocument":
    """Map chromatogram to EnzymeML"""
    # Create EnzymeML object
    enzymeML = EnzymeML()
    # Add chromatogram peaks to EnzymeML
    for peak, retention_time, signal in zip(
        chromatogram.peaks,
        chromatogram.retention_times,
        chromatogram.signals,
    ):
        enzymeML.add_data(
            peak,
            retention_time,
            signal,
            chromatogram.time_unit,
            chromatogram.wavelength,
            chromatogram.type,
        )
    return enzymeML


def create_enzymeml(
    name: str,
    molecules: List["Molecule"],
    vessel_name: str,
    vessel_volume: float,
    vessel_unit: str,
):
    enzml = EnzymeML(name=name)

    vessel = enzml.add_to_vessels(
        name=vessel_name,
        volume=vessel_volume,
        unit=vessel_unit,
    )

    return enzml
