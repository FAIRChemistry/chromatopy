import sdRDM

from typing import Optional
from pydantic import Field
from sdRDM.base.utils import forge_signature, IDGenerator


from .inlet import Inlet
from .detector import Detector


@forge_signature
class Column(sdRDM.DataModel):

    """Descibes properties of a column and its connections to the inlet and detector."""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("columnINDEX"),
        xml="@id",
    )

    name: Optional[str] = Field(
        default=None,
        description="Name of the column",
    )

    type: Optional[str] = Field(
        default=None,
        description="Type of column",
    )

    max_temp: Optional[float] = Field(
        default=None,
        description="Maximum temperature of the column",
    )

    length: Optional[float] = Field(
        default=None,
        description="Length of the column",
    )

    diameter: Optional[float] = Field(
        default=None,
        description="Diameter of the column",
    )

    film_thickness: Optional[float] = Field(
        default=None,
        description="Film thickness of the column",
    )

    flow_mode: Optional[str] = Field(
        default=None,
        description="Flow mode of the column",
    )

    flow_rate: Optional[float] = Field(
        default=None,
        description="Flow rate of the column",
    )

    flow_unit: Optional[str] = Field(
        default=None,
        description="Unit of flow rate",
    )

    inlet: Optional[Inlet] = Field(
        default=Inlet(),
        description="Inlet of the column",
    )

    detector: Optional[Detector] = Field(
        default=Detector(),
        description="Outlet of the column, connected to detector",
    )

    outlet_pressure: Optional[float] = Field(
        default=None,
        description="Outlet pressure of the column",
    )
