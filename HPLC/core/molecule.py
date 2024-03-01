import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator
from datetime import datetime as Datetime
from scipy.stats import linregress
from .peak import Peak
from .role import Role
from .standard import Standard


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

    concentrations: List[float] = Field(
        default_factory=ListPlus,
        multiple=True,
        description="Concentration of the molecule",
    )

    standard: Optional[Standard] = Field(
        default=Standard(),
        description="Standard, describing the signal to concentration relationship",
    )

    role: Optional[Role] = Field(
        default=None,
        description="Role of the molecule in the experiment",
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

    def calculate_concentrations(
        self,
        internal_standard: "Molecule",
    ) -> List[float]:
        if not self.role == Role.ANALYTE.value:
            raise ValueError(f"Analyte {self.name} is not an analyte")
        if not internal_standard.role == Role.INTERNAL_STANDARD.value:
            raise ValueError(
                f"Internal standard {internal_standard.name} is not an internal"
                " standard"
            )

        analyte_ares = (peak.area for peak in self.peaks)
        standard_areas = (peak.area for peak in internal_standard.peaks)

        self.concentrations = [
            area_analyte
            / area_standard
            / internal_standard.slope
            * internal_standard.molecular_weight
            for area_analyte, area_standard in zip(analyte_ares, standard_areas)
        ]

    @property
    def slope(self):
        if self.standard:
            return linregress(
                x=self.standard.concentration, y=self.standard.signal
            ).slope

        else:
            return None

    @property
    def seconds(self):
        return self.datetime_to_relative_time(self.times, unit="s")

    @property
    def minutes(self):
        return self.datetime_to_relative_time(self.times, unit="m")

    @property
    def hours(self):
        return self.datetime_to_relative_time(self.times, unit="h")

    @staticmethod
    def datetime_to_relative_time(
        datetimes: List[Datetime], unit: str = "s"
    ) -> List[float]:
        time_converter = dict(
            s=1,
            m=60,
            h=3600,
        )

        deltas = (dt - datetimes[0] for dt in datetimes)
        total_seconds = (delta.total_seconds() for delta in deltas)

        return [seconds / time_converter[unit] for seconds in total_seconds]
