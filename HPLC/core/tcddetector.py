
from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator


from .detector import Detector


@forge_signature
class TCDDetector(Detector):

    """Describes properties of a thermal conductivity detector."""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("tcddetectorINDEX"),
        xml="@id",
    )

    hydrogen_flow: Optional[float] = Field(
        default=None,
        description="Hydrogen flow",
    )

    air_flow: Optional[float] = Field(
        default=None,
        description="Air flow",
    )

    flame: Optional[bool] = Field(
        default=None,
        description="Flame on/off",
    )

    electrometer: Optional[bool] = Field(
        default=None,
        description="Electrometer on/off",
    )

    lit_offset: Optional[float] = Field(
        default=None,
        description="Lit offset",
    )
