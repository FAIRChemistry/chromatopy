import sdRDM

from typing import List, Optional
from pydantic import Field
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature, IDGenerator


from .valve import Valve
from .oven import Oven
from .inlet import Inlet
from .detector import Detector
from .column import Column


@forge_signature
class Method(sdRDM.DataModel):

    """"""

    id: Optional[str] = Field(
        description="Unique identifier of the given object.",
        default_factory=IDGenerator("methodINDEX"),
        xml="@id",
    )

    injection_time: Optional[float] = Field(
        default=None,
        description="Injection time",
    )

    injection_date: Optional[str] = Field(
        default=None,
        description="Injection date",
    )

    injection_volume: Optional[float] = Field(
        default=None,
        description="Injection volume",
    )

    injection_volume_unit: Optional[str] = Field(
        default=None,
        description="Unit of injection volume",
    )

    location: Optional[str] = Field(
        default=None,
        description="Location of sample vial",
    )

    oven: Optional[Oven] = Field(
        default=Oven(),
        description="Settings of the oven",
    )

    columns: List[Column] = Field(
        description="Parameters of the columns",
        default_factory=ListPlus,
        multiple=True,
    )

    valves: List[Valve] = Field(
        description="Settings of the valves",
        default_factory=ListPlus,
        multiple=True,
    )

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
        flow_unit: Optional[str] = None,
        inlet: Optional[Inlet] = None,
        detector: Optional[Detector] = None,
        outlet_pressure: Optional[float] = None,
        id: Optional[str] = None,
    ) -> None:
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
            detector (): Outlet of the column, connected to detector. Defaults to None
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
    ) -> None:
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
