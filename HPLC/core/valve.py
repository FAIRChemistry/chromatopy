import sdRDM

from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator


@forge_signature
class Valve(sdRDM.DataModel):
    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("valveINDEX"),
        xml="@id",
    )

    name: Optional[str] = Field(
        default=None,
        description="Name of the valve",
    )

    loop_volume: Optional[float] = Field(
        default=None,
        description="Loop volume of the valve",
    )

    load_time: Optional[float] = Field(
        default=None,
        description="Load time",
    )

    inject_time: Optional[float] = Field(
        default=None,
        description="Inject time",
    )
