import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator


from .ramp import Ramp


@forge_signature
class Oven(sdRDM.DataModel):

    """Describes settings of the oven."""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("ovenINDEX"),
        xml="@id",
    )

    init_temp: Optional[float] = Field(
        default=None,
        description="Initial temperature of the oven",
    )

    max_temp: Optional[float] = Field(
        default=None,
        description="Maximum temperature of the oven",
    )

    equilibrate_time: Optional[float] = Field(
        default=None,
        description="Time to equilibrate the oven",
    )

    ramps: List[Ramp] = Field(
        description="Thermal protocols of the oven",
        default_factory=ListPlus,
        multiple=True,
    )

    post_temp: Optional[float] = Field(
        default=None,
        description="Temperature after protocol",
    )

    post_time: Optional[float] = Field(
        default=None,
        description="Time after protocol",
    )

    run_time: Optional[float] = Field(
        default=None,
        description="Duration of the run",
    )

    def add_to_ramps(
        self,
        temp_rate: Optional[float] = None,
        final_temp: Optional[float] = None,
        hold_time: Optional[float] = None,
        time_unit: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        """
        This method adds an object of type 'Ramp' to attribute ramps

        Args:
            id (str): Unique identifier of the 'Ramp' object. Defaults to 'None'.
            temp_rate (): Rate of temperature change during the ramp. Defaults to None
            final_temp (): Final temperature of the ramp. Defaults to None
            hold_time (): Duration to hold the final temperature before starting the next ramp. Defaults to None
            time_unit (): Unit of time. Defaults to None
        """

        params = {
            "temp_rate": temp_rate,
            "final_temp": final_temp,
            "hold_time": hold_time,
            "time_unit": time_unit,
        }

        if id is not None:
            params["id"] = id

        self.ramps.append(Ramp(**params))

        return self.ramps[-1]
