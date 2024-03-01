
from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator
from .detector import Detector


@forge_signature
class FIDDetector(Detector):
    """Describes properties of a flame ionization detector."""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("fiddetectorINDEX"),
        xml="@id",
    )

    reference_flow: Optional[float] = Field(
        default=None,
        description="Reference flow",
    )

    filament: Optional[bool] = Field(
        default=None,
        description="Filament on/off",
    )

    negative_polarity: Optional[bool] = Field(
        default=None,
        description="Negative polarity on/off",
    )
