import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator


from .peak import Peak
from .signaltype import SignalType


@forge_signature
class Signal(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("signalINDEX"),
        xml="@id",
    )

    peaks: List[Peak] = Field(
        description="Peaks in the signal",
        default_factory=ListPlus,
        multiple=True,
    )

    type: Optional[SignalType] = Field(
        default=None,
        description="Type of signal",
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
