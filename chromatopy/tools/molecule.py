from datetime import datetime as Datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from chromatopy.model import Peak, UnitDefinition


class Molecule(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
        use_enum_values=True,
    )  # type: ignore

    id: str
    name: str
    retention_time: float
    ld_id: Optional[str] = Field(default=None)
    molecular_weight: Optional[float] = Field(default=None)
    prep_conc: Optional[UnitDefinition] = Field(
        default=None, description="Prepared concentration prior to reaction start"
    )
    conc_unit: Optional[UnitDefinition] = Field(default=None)
    uniprot_id: Optional[str] = Field(default=None)
    peaks: List[Peak] = Field(default_factory=list)
    reaction_times: List[float] = Field(
        default_factory=list,
        description="Reaction times of the molecule measured peaks",
    )

    def add_to_peaks(
        self,
        molecule_id: Optional[str] = None,
        retention_time: Optional[float] = None,
        timestamp: Optional[Datetime] = None,
        retention_time_unit: Optional[UnitDefinition] = None,
        type: Optional[str] = None,
        peak_start: Optional[float] = None,
        peak_end: Optional[float] = None,
        width: Optional[float] = None,
        area: Optional[float] = None,
        height: Optional[float] = None,
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
            "analyte_id": molecule_id,
            "retention_time": retention_time,
            "timestamp": timestamp,
            "retention_time_unit": retention_time_unit,
            "type": type,
            "peak_start": peak_start,
            "peak_end": peak_end,
            "width": width,
            "area": area,
            "height": height,
            "percent_area": percent_area,
            "tailing_factor": tailing_factor,
            "separation_factor": separation_factor,
        }
        if id is not None:
            params["id"] = id
        self.peaks.append(Peak(**params))
        return self.peaks[-1]
