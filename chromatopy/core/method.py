import sdRDM

from typing import Dict, List, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.base.datatypes import Unit
from sdRDM.tools.utils import elem2dict
from .valve import Valve
from .oven import Oven
from .inlet import Inlet
from .column import Column
from .detector import Detector


@forge_signature
class Method(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    injection_time: Optional[float] = element(
        description="Injection time",
        default=None,
        tag="injection_time",
        json_schema_extra=dict(),
    )

    injection_date: Optional[str] = element(
        description="Injection date",
        default=None,
        tag="injection_date",
        json_schema_extra=dict(),
    )

    injection_volume: Optional[float] = element(
        description="Injection volume",
        default=None,
        tag="injection_volume",
        json_schema_extra=dict(),
    )

    injection_volume_unit: Optional[Unit] = element(
        description="Unit of injection volume",
        default=None,
        tag="injection_volume_unit",
        json_schema_extra=dict(),
    )

    location: Optional[str] = element(
        description="Location of sample vial",
        default=None,
        tag="location",
        json_schema_extra=dict(),
    )

    oven: Optional[Oven] = element(
        description="Settings of the oven",
        default_factory=Oven,
        tag="oven",
        json_schema_extra=dict(),
    )

    columns: List[Column] = element(
        description="Parameters of the columns",
        default_factory=ListPlus,
        tag="columns",
        json_schema_extra=dict(multiple=True),
    )

    valves: List[Valve] = element(
        description="Settings of the valves",
        default_factory=ListPlus,
        tag="valves",
        json_schema_extra=dict(multiple=True),
    )
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="371223791b951fed8b47aa4129c84c4e7d5f82aa"
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

    def add_to_columns(
        self,
        name: Optional[str] = None,
        type: Optional[str] = None,
        max_temp: Optional[float] = None,
        length: Optional[float] = None,
        diameter: Optional[float] = None,
        film_thickness: Optional[float] = None,
        flow_mode: Optional[str] = None,
        flow_rate: Optional[float] = None,
        flow_unit: Optional[Unit] = None,
        inlet: Optional[Inlet] = None,
        detector: Optional[Detector] = None,
        outlet_pressure: Optional[float] = None,
        id: Optional[str] = None,
    ) -> Column:
        """
        This method adds an object of type 'Column' to attribute columns

        Args:
            id (str): Unique identifier of the 'Column' object. Defaults to 'None'.
            name (): Name of the column. Defaults to None
            type (): Type of column. Defaults to None
            max_temp (): Maximum temperature of the column. Defaults to None
            length (): Length of the column. Defaults to None
            diameter (): Diameter of the column. Defaults to None
            film_thickness (): Film thickness of the column. Defaults to None
            flow_mode (): Flow mode of the column. Defaults to None
            flow_rate (): Flow rate of the column. Defaults to None
            flow_unit (): Unit of flow rate. Defaults to None
            inlet (): Inlet of the column. Defaults to None
            detector (): Outlet of the column, connected to the detector. Defaults to None
            outlet_pressure (): Outlet pressure of the column. Defaults to None
        """
        params = {
            "name": name,
            "type": type,
            "max_temp": max_temp,
            "length": length,
            "diameter": diameter,
            "film_thickness": film_thickness,
            "flow_mode": flow_mode,
            "flow_rate": flow_rate,
            "flow_unit": flow_unit,
            "inlet": inlet,
            "detector": detector,
            "outlet_pressure": outlet_pressure,
        }
        if id is not None:
            params["id"] = id
        self.columns.append(Column(**params))
        return self.columns[-1]

    def add_to_valves(
        self,
        name: Optional[str] = None,
        loop_volume: Optional[float] = None,
        load_time: Optional[float] = None,
        inject_time: Optional[float] = None,
        id: Optional[str] = None,
    ) -> Valve:
        """
        This method adds an object of type 'Valve' to attribute valves

        Args:
            id (str): Unique identifier of the 'Valve' object. Defaults to 'None'.
            name (): Name of the valve. Defaults to None
            loop_volume (): Loop volume of the valve. Defaults to None
            load_time (): Load time. Defaults to None
            inject_time (): Inject time. Defaults to None
        """
        params = {
            "name": name,
            "loop_volume": loop_volume,
            "load_time": load_time,
            "inject_time": inject_time,
        }
        if id is not None:
            params["id"] = id
        self.valves.append(Valve(**params))
        return self.valves[-1]
