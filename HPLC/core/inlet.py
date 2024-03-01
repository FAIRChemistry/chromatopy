import sdRDM

from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator


@forge_signature
class Inlet(sdRDM.DataModel):
    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("inletINDEX"),
        xml="@id",
    )

    mode: Optional[str] = Field(
        default=None,
        description="Mode of the inlet (Split/Splitless)",
    )

    init_temp: Optional[float] = Field(
        default=None,
        description="Initial temperature",
    )

    pressure: Optional[float] = Field(
        default=None,
        description="Inlet pressure",
    )

    pressure_unit: Optional[str] = Field(
        default=None,
        description="Unit of pressure",
    )

    split_ratio: Optional[str] = Field(
        default=None,
        description="Split ratio",
        regex="(\\d+)(:)(\\d+)",
    )

    split_flow: Optional[float] = Field(
        default=None,
        description="Split flow",
    )

    total_flow: Optional[float] = Field(
        default=None,
        description="Total flow",
    )

    flow_unit: Optional[str] = Field(
        default=None,
        description="Unit of flow",
    )

    gas_saver: Optional[bool] = Field(
        default=None,
        description="Gas saver mode",
    )

    gas_type: Optional[str] = Field(
        default=None,
        description="Type of gas",
    )
