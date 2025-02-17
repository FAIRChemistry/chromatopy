from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from chromatopy.model import UnitDefinition


class Protein(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
        use_enum_values=True,
    )

    id: str = Field(
        description="ID of the Protein",
    )
    name: str = Field(
        description="Name of the protein",
    )
    init_conc: Optional[float] = Field(
        description="Initial concentration of the protein at t=0",
        default=None,
    )
    conc_unit: Optional[UnitDefinition] = Field(
        description="Unit of the concentration",
        default=None,
    )
    sequence: Optional[str] = Field(
        description="Amino acid sequence of the protein",
        default=None,
    )
    organism: Optional[str] = Field(
        description="Organism from which the protein originates",
        default=None,
    )
    organism_tax_id: Optional[str] = Field(
        description="Taxonomic ID of the organism",
        default=None,
    )
    constant: bool = Field(
        description="Boolean indicating whether the protein concentration is constant",
        default=True,
    )
