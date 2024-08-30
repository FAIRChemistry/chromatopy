from calipytion.model import Standard
from pydantic import BaseModel, ConfigDict, Field

from chromatopy.model import UnitDefinition as ChromatopyUnitDefinition


class Molecule(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
        use_enum_values=True,
    )  # type: ignore

    id: str = Field(description="ID of the molecule")
    pubchem_cid: int = Field(description="PubChem CID of the molecule")
    name: str = Field(description="Name of the molecule")
    init_conc: float = Field(description="Initial concentration of the molecule at t=0")
    conc_unit: ChromatopyUnitDefinition = Field(description="Unit of the concentration")
    retention_time: float = Field(
        description="Retention time of the molecule in minutes"
    )
    wavelength: float = Field(
        description="Wavelength at which the molecule was detected", default=None
    )
    standard: Standard | None = Field(
        description="Standard instance associated with the molecule", default=None
    )

    # @model_validator(mode="before")
    # @classmethod
    # def get_molecule_name(cls, data: Any) -> Any:
    #     """Retrieves the molecule name from the PubChem database based on the PubChem CID."""

    #     if "name" not in data:
    #         data["molecule_name"] = pubchem_request_molecule_name(data["pubchem_cid"])
    #     return data

    # # validator that if a standard is provided, the retention time must be defined and vice versa

    # @model_validator(mode="before")
    # @classmethod
    # def validate_standard_and_retention_time(cls, data: Any) -> Any:
    #     if data.get("standard") and data.get("retention_time"):
    #         assert data["standard"].retention_time == data["retention_time"], """
    #         The retention time of the standard and the molecule must be the same.
    #         """

    @classmethod
    def from_standard(
        cls, standard: Standard, init_conc: float, conc_unit: ChromatopyUnitDefinition
    ):
        """Creates a Molecule instance from a Standard instance."""

        assert standard.retention_time, """
        The retention time of the standard needs to be defined. 
        Specify the `retention_time` attribute of the standard.
        """

        return cls(
            id=standard.molecule_id,
            pubchem_cid=standard.pubchem_cid,
            name=standard.molecule_name,
            init_conc=init_conc,
            conc_unit=conc_unit,
            retention_time=standard.retention_time,
            standard=standard,
        )


if __name__ == "__main__":
    from calipytion.model import Standard
    from calipytion.units import C

    from chromatopy.units import mM as chrommM

    standard = Standard(
        molecule_name="Standard",
        molecule_id="1",
        pubchem_cid=123,
        ph=3,
        temperature=23,
        temp_unit=C,
        retention_time=10.0,
    )

    print(standard)

    # breaks as soon as units from two different libraries are used

    molecule = Molecule.from_standard(standard, init_conc=1.0, conc_unit=chrommM)
    print(molecule)

    molecule = Molecule(
        id="m2",
        pubchem_cid=456,
        name="Molecule 2",
        init_conc=2.0,
        conc_unit=chrommM,
        retention_time=20.0,
        standard=standard,
    )

    print(molecule)
