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

from .chromatogram import Chromatogram
from .peak import Peak
from .signaltype import SignalType


@forge_signature
class Measurement(sdRDM.DataModel):
    """"""

    id: Optional[str] = attr(
        name="id",
        description="Unique identifier of the given object.",
        default_factory=lambda: str(uuid4()),
        xml="@id",
    )

    chromatograms: List[Chromatogram] = element(
        description="Measured signal",
        default_factory=ListPlus,
        tag="chromatograms",
        json_schema_extra=dict(multiple=True),
    )

    timestamp: Optional[Datetime] = element(
        description="Timestamp of sample injection into the column",
        default=None,
        tag="timestamp",
        json_schema_extra=dict(),
    )

    reaction_time: Optional[float] = element(
        description="Reaction time",
        default=None,
        tag="reaction_time",
        json_schema_extra=dict(),
    )

    time_unit: Optional[Unit] = element(
        description="Unit of time",
        default=None,
        tag="time_unit",
        json_schema_extra=dict(),
    )

    injection_volume: Optional[float] = element(
        description="Injection volume",
        default=None,
        tag="injection_volume",
        json_schema_extra=dict(),
    )

    dilution_factor: Optional[float] = element(
        description="Dilution factor",
        default=None,
        tag="dilution_factor",
        json_schema_extra=dict(),
    )

    injection_volume_unit: Optional[Unit] = element(
        description="Unit of injection volume",
        default=None,
        tag="injection_volume_unit",
        json_schema_extra=dict(),
    )

    reaction_time: Optional[float] = element(
        description="Reaction time",
        default=None,
        tag="reaction_time",
        json_schema_extra=dict(),
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

    def add_to_chromatograms(
        self,
        peaks: List[Peak] = ListPlus(),
        signals: List[float] = ListPlus(),
        times: List[float] = ListPlus(),
        processed_signal: List[float] = ListPlus(),
        wavelength: Optional[float] = None,
        type: Optional[SignalType] = None,
        id: Optional[str] = None,
    ) -> Chromatogram:
        """
        This method adds an object of type 'Chromatogram' to attribute chromatograms

        Args:
            id (str): Unique identifier of the 'Chromatogram' object. Defaults to 'None'.
            peaks (): Peaks in the signal. Defaults to ListPlus()
            signals (): Signal values. Defaults to ListPlus()
            times (): Time values of the signal. Defaults to ListPlus()
            processed_signal (): Processed signal values after baseline correction and deconvolution. Defaults to ListPlus()
            wavelength (): Wavelength of the signal in nm. Defaults to None
            type (): Type of signal. Defaults to None
        """
        params = {
            "peaks": peaks,
            "signals": signals,
            "times": times,
            "processed_signal": processed_signal,
            "wavelength": wavelength,
            "type": type,
        }
        if id is not None:
            params["id"] = id
        self.chromatograms.append(Chromatogram(**params))
        return self.chromatograms[-1]

    def get_detector(self, detector: SignalType) -> List[Chromatogram]:
        """Gets the chromatogram of a specific detector"""
        for chromatogram in self.chromatograms:
            if chromatogram.type == detector:
                return chromatogram

        raise ValueError(f"No chromatogram of from {detector} found in measurement")
