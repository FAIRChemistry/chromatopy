import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator


@forge_signature
class Standard(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("standardINDEX"),
        xml="@id",
    )

    concentration: List[float] = Field(
        default_factory=ListPlus,
        multiple=True,
        description="Concentration",
    )

    signal: List[float] = Field(
        default_factory=ListPlus,
        multiple=True,
        description="Signal corresponding to concentration",
    )

    concentration_unit: Optional[str] = Field(
        default=None,
        description="Concentration",
    )
