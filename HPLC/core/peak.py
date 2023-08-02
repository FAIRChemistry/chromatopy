import sdRDM

from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator


@forge_signature
class Peak(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("peakINDEX"),
        xml="@id",
    )

    retention_time: Optional[float] = Field(
        default=None,
        description="Retention time of the peak",
    )

    retention_time_unit: Optional[str] = Field(
        default=None,
        description="Unit of retention time",
    )

    type: Optional[str] = Field(
        default=None,
        description="Type of peak (baseline-baseline / baseline-valey / ...)",
    )

    width: Optional[float] = Field(
        default=None,
        description="Width of the peak",
    )

    width_unit: Optional[str] = Field(
        default=None,
        description="Unit of width",
    )

    area: Optional[float] = Field(
        default=None,
        description="Area of the peak",
    )

    area_unit: Optional[str] = Field(
        default=None,
        description="Unit of area",
    )

    height: Optional[float] = Field(
        default=None,
        description="Height of the peak",
    )

    height_unit: Optional[str] = Field(
        default=None,
        description="Unit of height",
    )

    percent_area: Optional[float] = Field(
        default=None,
        description="Percent area of the peak",
    )
