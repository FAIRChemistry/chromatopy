import sdRDM

from typing import Dict, List, Optional
from uuid import uuid4
from pydantic import PrivateAttr, model_validator
from pydantic_xml import attr, element
from lxml.etree import _Element

from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.base.datatypes import Unit
from sdRDM.tools.utils import elem2dict


from datetime import datetime as Datetime
from sdRDM.base.datatypes import Unit

from .analyte import Analyte
from .measurement import Measurement
from .standard import Standard
from .chromatogram import Chromatogram
from .peak import Peak
from .role import Role


@forge_signature
class ChromHandler(
    sdRDM.DataModel,
):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    analytes: List[Analyte] = element(
        description="Molecule that can be assigned to a peak.",
        default_factory=ListPlus,
        tag="analytes",
        json_schema_extra=dict(
            multiple=True,
        ),
    )

    measurements: List[Measurement] = element(
        description="Measured signals",
        default_factory=ListPlus,
        tag="measurements",
        json_schema_extra=dict(
            multiple=True,
        ),
    )

    _repo: Optional[str] = PrivateAttr(
        default="https://github.com/FAIRChemistry/chromatopy"
    )
    _commit: Optional[str] = PrivateAttr(
        default="a2315aa263d2980bb5b222724cbb01fc09cb5e65"
    )
    _raw_xml_data: Dict = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def _parse_raw_xml_data(self):
        for attr, value in self:
            if isinstance(value, (ListPlus, list)) and all(
                isinstance(i, _Element) for i in value
            ):
                self._raw_xml_data[attr] = [elem2dict(i) for i in value]
            elif isinstance(value, _Element):
                self._raw_xml_data[attr] = elem2dict(value)

        return self

    def add_to_analytes(
        self,
        name: Optional[str] = None,
        inchi: Optional[str] = None,
        molecular_weight: Optional[float] = None,
        retention_time: Optional[float] = None,
        peaks: List[Peak] = ListPlus(),
        concentrations: List[float] = ListPlus(),
        standard: Optional[Standard] = None,
        role: Optional[Role] = None,
        id: Optional[str] = None,
    ) -> Analyte:
        """
        This method adds an object of type 'Analyte' to attribute analytes

        Args:
            id (str): Unique identifier of the 'Analyte' object. Defaults to 'None'.
            name (): Name of the analyte. Defaults to None
            inchi (): InCHI code of the molecule. Defaults to None
            molecular_weight (): Molar weight of the molecule in g/mol. Defaults to None
            retention_time (): Approximated retention time of the molecule. Defaults to None
            peaks (): All peaks of the dataset, which are within the same retention time interval related to the molecule. Defaults to ListPlus()
            concentrations (): Concentration of the molecule. Defaults to ListPlus()
            standard (): Standard, describing the signal-to-concentration relationship. Defaults to None
            role (): Role of the molecule in the experiment. Defaults to None
        """

        params = {
            "name": name,
            "inchi": inchi,
            "molecular_weight": molecular_weight,
            "retention_time": retention_time,
            "peaks": peaks,
            "concentrations": concentrations,
            "standard": standard,
            "role": role,
        }

        if id is not None:
            params["id"] = id

        self.analytes.append(Analyte(**params))

        return self.analytes[-1]

    def add_to_measurements(
        self,
        chromatograms: List[Chromatogram] = ListPlus(),
        timestamp: Optional[Datetime] = None,
        injection_volume: Optional[float] = None,
        injection_volume_unit: Optional[Unit] = None,
        id: Optional[str] = None,
    ) -> Measurement:
        """
        This method adds an object of type 'Measurement' to attribute measurements

        Args:
            id (str): Unique identifier of the 'Measurement' object. Defaults to 'None'.
            chromatograms (): Measured signal. Defaults to ListPlus()
            timestamp (): Timestamp of sample injection into the column. Defaults to None
            injection_volume (): Injection volume. Defaults to None
            injection_volume_unit (): Unit of injection volume. Defaults to None
        """

        params = {
            "chromatograms": chromatograms,
            "timestamp": timestamp,
            "injection_volume": injection_volume,
            "injection_volume_unit": injection_volume_unit,
        }

        if id is not None:
            params["id"] = id

        self.measurements.append(Measurement(**params))

        return self.measurements[-1]
