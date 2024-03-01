import sdRDM

from typing import Dict, List, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict
from .standard import Standard
from .peak import Peak
from .role import Role


@forge_signature
class Molecule(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    name: Optional[str] = element(
        description="Molecule name",
        default=None,
        tag="name",
        json_schema_extra=dict(),
    )

    inchi: Optional[str] = element(
        description="InCHI code of the molecule",
        default=None,
        tag="inchi",
        json_schema_extra=dict(),
    )

    molecular_weight: Optional[float] = element(
        description="Molar weight of the molecule in g/mol",
        default=None,
        tag="molecular_weight",
        json_schema_extra=dict(),
    )

    retention_time: Optional[float] = element(
        description="Approximated retention time of the molecule",
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

    standard: Optional[Standard] = element(
        description="Standard, describing the signal-to-concentration relationship",
        default_factory=Standard,
        tag="standard",
        json_schema_extra=dict(),
    )

    role: Optional[Role] = element(
        description="Role of the molecule in the experiment",
        default=None,
        tag="role",
        json_schema_extra=dict(),
    )
    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/HPLC-specification"
    )
    _commit: Optional[str] = PrivateAttr(
        default="e1922ec9220fac3332dbf180c6db0a5fe1eefd25"
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
        retention_time: Optional[float] = None,
        retention_time_unit: Optional[str] = None,
        type: Optional[str] = None,
        width: Optional[float] = None,
        width_unit: Optional[str] = None,
        area: Optional[float] = None,
        area_unit: Optional[str] = None,
        height: Optional[float] = None,
        height_unit: Optional[str] = None,
        percent_area: Optional[float] = None,
        id: Optional[str] = None,
    ) -> Peak:
        """
        This method adds an object of type 'Peak' to attribute peaks

        Args:
            id (str): Unique identifier of the 'Peak' object. Defaults to 'None'.
            retention_time (): Retention time of the peak. Defaults to None
            retention_time_unit (): Unit of retention time. Defaults to None
            type (): Type of peak (baseline-baseline / baseline-valey / ...). Defaults to None
            width (): Width of the peak. Defaults to None
            width_unit (): Unit of width. Defaults to None
            area (): Area of the peak. Defaults to None
            area_unit (): Unit of area. Defaults to None
            height (): Height of the peak. Defaults to None
            height_unit (): Unit of height. Defaults to None
            percent_area (): Percent area of the peak. Defaults to None
        """
        params = {
            "retention_time": retention_time,
            "retention_time_unit": retention_time_unit,
            "type": type,
            "width": width,
            "width_unit": width_unit,
            "area": area,
            "area_unit": area_unit,
            "height": height,
            "height_unit": height_unit,
            "percent_area": percent_area,
        }
        if id is not None:
            params["id"] = id
        self.peaks.append(Peak(**params))
        return self.peaks[-1]
