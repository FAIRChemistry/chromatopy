import sdRDM

from typing import Dict, List, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict
from .ramp import Ramp


@forge_signature
class Oven(sdRDM.DataModel):
    """Describes the settings of the oven."""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    init_temp: Optional[float] = element(
        description="Initial temperature of the oven",
        default=None,
        tag="init_temp",
        json_schema_extra=dict(),
    )

    max_temp: Optional[float] = element(
        description="Maximum temperature of the oven",
        default=None,
        tag="max_temp",
        json_schema_extra=dict(),
    )

    equilibrate_time: Optional[float] = element(
        description="Time to equilibrate the oven",
        default=None,
        tag="equilibrate_time",
        json_schema_extra=dict(),
    )

    ramps: List[Ramp] = element(
        description="Thermal protocols of the oven",
        default_factory=ListPlus,
        tag="ramps",
        json_schema_extra=dict(multiple=True),
    )

    post_temp: Optional[float] = element(
        description="Temperature after protocol",
        default=None,
        tag="post_temp",
        json_schema_extra=dict(),
    )

    post_time: Optional[float] = element(
        description="Time after protocol",
        default=None,
        tag="post_time",
        json_schema_extra=dict(),
    )

    run_time: Optional[float] = element(
        description="Duration of the run",
        default=None,
        tag="run_time",
        json_schema_extra=dict(),
    )
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="f0b2259e601e7ba4be017d348f7315a280ca776d"
    )
    _raw_xml_data: Dict = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _parse_raw_xml_data(self):
        for attr, value in self:
            if isinstance(value, (ListPlus, list)) and all(
                (isinstance(i, _Element) for i in value)
            ):
                self._raw_xml_data[attr] = [elem2dict(i) for i in value]
            elif isinstance(value, _Element):
                self._raw_xml_data[attr] = elem2dict(value)
        return self

    def add_to_ramps(
        self,
        temp_rate: Optional[float] = None,
        final_temp: Optional[float] = None,
        hold_time: Optional[float] = None,
        time_unit: Optional[str] = None,
        id: Optional[str] = None,
    ) -> Ramp:
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
