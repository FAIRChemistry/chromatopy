import sdRDM

from typing import Dict, List, Optional
from pydantic import PrivateAttr, model_validator
from uuid import uuid4
from pydantic_xml import attr, element
from lxml.etree import _Element
from sdRDM.base.listplus import ListPlus
from sdRDM.base.utils import forge_signature
from sdRDM.tools.utils import elem2dict
from datetime import datetime as Datetime
from .method import Method
from .measurement import Measurement
from .signal import Signal
from .molecule import Molecule


@forge_signature
class ChromatigraphicExperiment(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    method: Optional[Method] = element(
        description="Description of the HPLC method",
        default_factory=Method,
        tag="method",
        json_schema_extra=dict(),
    )

    molecules: Optional[Molecule] = element(
        description="Molecule which can be assigned to a peak.",
        default_factory=Molecule,
        tag="molecules",
        json_schema_extra=dict(),
    )

    measurements: List[Measurement] = element(
        description="Measured signals",
        default_factory=ListPlus,
        tag="measurements",
        json_schema_extra=dict(multiple=True),
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

    def add_to_measurements(
        self,
        signals: List[Signal] = ListPlus(),
        timestamp: Optional[Datetime] = None,
        injection_volume: Optional[float] = None,
        injection_volume_unit: Optional[str] = None,
        id: Optional[str] = None,
    ) -> Measurement:
        """
        This method adds an object of type 'Measurement' to attribute measurements

        Args:
            id (str): Unique identifier of the 'Measurement' object. Defaults to 'None'.
            signals (): Measured signal. Defaults to ListPlus()
            timestamp (): Timestamp of sample injection into the column. Defaults to None
            injection_volume (): Injection volume. Defaults to None
            injection_volume_unit (): Unit of injection volume. Defaults to None
        """
        params = {
            "signals": signals,
            "timestamp": timestamp,
            "injection_volume": injection_volume,
            "injection_volume_unit": injection_volume_unit,
        }
        if id is not None:
            params["id"] = id
        self.measurements.append(Measurement(**params))
        return self.measurements[-1]
