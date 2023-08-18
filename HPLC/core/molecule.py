import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator

from datetime import datetime as Datetime

from .peak import Peak


@forge_signature
class Molecule(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("moleculeINDEX"),
        xml="@id",
    )

    name: Optional[str] = Field(
        default=None,
        description="Molecule name",
    )

    inchi: Optional[str] = Field(
        default=None,
        description="Inchi code of the molecule",
    )

    molecular_weight: Optional[float] = Field(
        default=None,
        description="Molar weight of the molecule in g/mol",
    )

    retention_time: Optional[float] = Field(
        default=None,
        description="Approximated retention time of the molecule",
    )

    times: List[Datetime] = Field(
        default_factory=ListPlus,
        multiple=True,
        description="Time points when the molecule concentration was measured",
    )

    peaks: List[Peak] = Field(
        default_factory=ListPlus,
        multiple=True,
        description=(
            "All peaks of the dataset which are within the same retention time interval"
        ),
    )

    concentration: List[float] = Field(
        default_factory=ListPlus,
        multiple=True,
        description="Concentration of the molecule",
    )

    def add_to_peaks(
        self,
        retention_time: Optional[float] = None,
        retention_time_unit: Optional[str] = None,
        type: Optional[str] = None,
        width: Optional[float] = None,
        width_unit: Optional[str] = None,
        area: Optional[float] = None,
        area_unit: Optional[str] = None,
        height: Optional[float] = None,
        height_unit: Optional[str] = None,
        percent_area: Optional[float] = None,
        id: Optional[str] = None,
    ) -> None:
        """
        This method adds an object of type 'Peak' to attribute peaks

        Args:
            id (str): Unique identifier of the 'Peak' object. Defaults to 'None'.
            retention_time (): Retention time of the peak. Defaults to None
            retention_time_unit (): Unit of retention time. Defaults to None
            type (): Type of peak (baseline-baseline / baseline-valey / ...). Defaults to None
            width (): Width of the peak. Defaults to None
            width_unit (): Unit of width. Defaults to None
            area (): Area of the peak. Defaults to None
            area_unit (): Unit of area. Defaults to None
            height (): Height of the peak. Defaults to None
            height_unit (): Unit of height. Defaults to None
            percent_area (): Percent area of the peak. Defaults to None
        """

        params = {
            "retention_time": retention_time,
            "retention_time_unit": retention_time_unit,
            "type": type,
            "width": width,
            "width_unit": width_unit,
            "area": area,
            "area_unit": area_unit,
            "height": height,
            "height_unit": height_unit,
            "percent_area": percent_area,
        }

        if id is not None:
            params["id"] = id

        self.peaks.append(Peak(**params))

        return self.peaks[-1]
