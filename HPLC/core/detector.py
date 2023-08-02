import sdRDM

from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator


@forge_signature
class Detector(sdRDM.DataModel):

    """Base class for detectors."""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("detectorINDEX"),
        xml="@id",
    )

    type: Optional[str] = Field(
        default=None,
        description="Type of detector",
    )

    flow_mode: Optional[str] = Field(
        default=None,
        description="Air flow mode",
    )

    makeup_flow: Optional[float] = Field(
        default=None,
        description="Makeup flow",
    )

    makeup_gas: Optional[str] = Field(
        default=None,
        description="Makeup gas",
    )

    flow_unit: Optional[str] = Field(
        default=None,
        description="Unit of flow",
    )

    reference_flow: Optional[float] = Field(
        default=None,
        description="Reference flow",
    )
