from datetime import datetime as Datetime
from typing import Dict, List, Optional
from uuid import uuid4

import sdRDM
from lxml.etree import _Element
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from sdRDM.base.datatypes import Unit
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict

from ..core.peak import Peak
from ..core.role import Role


@forge_signature
class Species(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    name: Optional[str] = element(
        description="Name of the analyte",
        default=None,
        tag="name",
        json_schema_extra=dict(),
    )

    chebi: Optional[int] = element(
        description="Chebi identifier of the molecule",
        default=None,
        tag="chebi",
        json_schema_extra=dict(),
    )

    molecular_weight: Optional[float] = element(
        description="Molar weight of the molecule in g/mol",
        default=None,
        tag="molecular_weight",
        json_schema_extra=dict(),
    )

    init_conc: Optional[float] = element(
        description="Initial concentration of the molecule",
        tag="init_conc",
        json_schema_extra=dict(),
    )

    conc_unit: Optional[Unit] = element(
        description="Unit of the concentration",
        tag="conc_unit",
        json_schema_extra=dict(),
    )

    time_unit: Optional[Unit] = element(
        description="Unit of the concentration",
        tag="time_unit",
        json_schema_extra=dict(),
    )

    uniprot_id: Optional[str] = element(
        description="UniProt ID of the molecule",
        default=None,
        tag="uniprot_id",
        json_schema_extra=dict(),
    )

    retention_time: Optional[float] = element(
        description="Characteristic retention time of the species.",
        default=None,
        tag="retention_time",
        json_schema_extra=dict(),
    )

    peaks: List[Peak] = element(
        description=(
            "All peaks of the dataset, which are within the same retention time"
            " interval related to the molecule"
        ),
        default_factory=ListPlus,
        tag="peaks",
        json_schema_extra=dict(multiple=True),
    )

    concentrations: List[float] = element(
        description="Concentration of the molecule",
        default_factory=ListPlus,
        tag="concentrations",
        json_schema_extra=dict(multiple=True),
    )

    role: Optional[Role] = element(
        description="Role of the molecule in the experiment",
        default=None,
        tag="role",
        json_schema_extra=dict(),
    )

    reaction_times: List[float] = element(
        description="Reaction times of the molecule measured peaks",
        default_factory=[],
        tag="reaction_times",
        json_schema_extra=dict(multiple=True),
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

    def add_to_peaks(
        self,
        analyte_id: Optional[str] = None,
        retention_time: Optional[float] = None,
        timestamp: Optional[Datetime] = None,
        retention_time_unit: Optional[Unit] = None,
        type: Optional[str] = None,
        peak_start: Optional[float] = None,
        peak_end: Optional[float] = None,
        width: Optional[float] = None,
        width_unit: Optional[Unit] = None,
        area: Optional[float] = None,
        area_unit: Optional[Unit] = None,
        height: Optional[float] = None,
        height_unit: Optional[Unit] = None,
        percent_area: Optional[float] = None,
        tailing_factor: Optional[float] = None,
        separation_factor: Optional[float] = None,
        id: Optional[str] = None,
    ) -> Peak:
        """
        This method adds an object of type 'Peak' to attribute peaks

        Args:
            id (str): Unique identifier of the 'Peak' object. Defaults to 'None'.
            analyte_id (): ID of the analyte. Defaults to None
            retention_time (): Retention time of the peak. Defaults to None
            timestamp (): Timestamp of the peak. Defaults to None
            retention_time_unit (): Unit of retention time. Defaults to None
            type (): Type of peak (baseline-baseline / baseline-valley / ...). Defaults to None
            peak_start (): Start retention time of the peak. Defaults to None
            peak_end (): End retention time of the peak. Defaults to None
            width (): Width of the peak. Defaults to None
            width_unit (): Unit of width. Defaults to None
            area (): Area of the peak. Defaults to None
            area_unit (): Unit of area. Defaults to None
            height (): Height of the peak. Defaults to None
            height_unit (): Unit of height. Defaults to None
            percent_area (): Percent area of the peak. Defaults to None
            tailing_factor (): Tailing factor of the peak. Defaults to None
            separation_factor (): Separation factor of the peak. Defaults to None
        """
        params = {
            "analyte_id": analyte_id,
            "retention_time": retention_time,
            "timestamp": timestamp,
            "retention_time_unit": retention_time_unit,
            "type": type,
            "peak_start": peak_start,
            "peak_end": peak_end,
            "width": width,
            "width_unit": width_unit,
            "area": area,
            "area_unit": area_unit,
            "height": height,
            "height_unit": height_unit,
            "percent_area": percent_area,
            "tailing_factor": tailing_factor,
            "separation_factor": separation_factor,
        }
        if id is not None:
            params["id"] = id
        self.peaks.append(Peak(**params))
        return self.peaks[-1]

    def get_peak_by_injection_time(self, injection_time: Datetime) -> Peak:
        """
        This method returns the peak with the given injection time

        Args:
            injection_time (Datetime): Injection time of the peak
        """
        for peak, peak_injection_time in zip(self.peaks, self.injection_times):
            if injection_time == peak_injection_time:
                return peak
        return None
