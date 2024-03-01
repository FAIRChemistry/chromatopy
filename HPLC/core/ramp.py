import sdRDM

from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator


@forge_signature
class Ramp(sdRDM.DataModel):
    """Describes properties of a temperature ramp."""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("rampINDEX"),
        xml="@id",
    )

    temp_rate: Optional[float] = Field(
        default=None,
        description="Rate of temperature change during the ramp",
    )

    final_temp: Optional[float] = Field(
        default=None,
        description="Final temperature of the ramp",
    )

    hold_time: Optional[float] = Field(
        default=None,
        description=(
            "Duration to hold the final temperature before starting the next ramp"
        ),
    )

    time_unit: Optional[str] = Field(
        default=None,
        description="Unit of time",
    )
