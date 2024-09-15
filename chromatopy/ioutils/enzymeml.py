import warnings
from enum import Enum

from calipytion.tools.calibrator import Calibrator
from pyenzyme import (
    DataTypes,
    EnzymeMLDocument,
    MeasurementData,
    Protein,
    SmallMolecule,
)
from pyenzyme import Measurement as EnzymeMLMeasurement
from pyenzyme import UnitDefinition as EnzymeMLUnitDefinition

from chromatopy.model import Chromatogram, Measurement
from chromatopy.model import UnitDefinition as UnitDefinition
from chromatopy.tools.internal_standard import InternalStandard
from chromatopy.tools.molecule import Molecule
from chromatopy.tools.molecule import Protein as ChromProtein


class CalibratorType(Enum):
    EXTERNAL = "external_standard"
    INTERNAL = "internal_standard"
    NONE = "none"


def create_enzymeml(
    doc_name: str,
    molecules: list[Molecule],
    proteins: list[ChromProtein],
    measurements: list[Measurement],
    internal_standard: Molecule | None,
    calculate_concentration: bool,
    extrapolate: bool,
) -> EnzymeMLDocument:
    """Creates an EnzymeMLDocument instance from a list of Molecule and Measurement instances.

    Args:
        doc_name (str): Name of the EnzymeMLDocument instance.
        molecules (list[Molecule]): List of Molecule instances.
        proteins (list[Protein]): List of Protein instances.
        measurements (list[Measurement]): List of Measurement instances.
        calculate_concentration (bool): If True, the concentration of the molecules will be calculated,
            using the internal standard or defined standard.
        extrapolate (bool): If True, the concentration of the molecules will be extrapolated.

    Returns:
        EnzymeMLDocument: The EnzymeMLDocument instance.
    """

    doc = EnzymeMLDocument(name=doc_name)
    meas_data: dict[str, MeasurementData] = {}

    for protein in proteins:
        add_protein(doc, protein)
        create_MeasurementData_instances(meas_data, protein)

    for molecule in molecules:
        add_molecule(doc, molecule)
        create_MeasurementData_instances(meas_data, molecule)

    # add data to MeasurementData instances
    measurement_data_instances = add_measurement_to_MeasurementData(
        measurements=measurements,
        measurement_data_instances=meas_data,
        calculate_concentration=calculate_concentration,
        molecules=molecules,
        internal_standard=internal_standard,
        extrapolate=extrapolate,
    )

    # create EnzymeML Measurement
    ph, temp, time_unit, temp_unit = extract_measurement_conditions(measurements)

    species_data = list(measurement_data_instances.values())
    for species in species_data:
        species.time_unit = EnzymeMLUnitDefinition(**time_unit.model_dump())

    enzml_measurement = EnzymeMLMeasurement(
        id="m0",
        name="m0",
        temperature=temp,
        temperature_unit=EnzymeMLUnitDefinition(**temp_unit.model_dump()),
        ph=ph,
        species_data=list(measurement_data_instances.values()),
    )

    doc.measurements.append(enzml_measurement)

    patch_init_t0(doc)

    return doc


def add_protein(doc: EnzymeMLDocument, protein: ChromProtein) -> None:
    """Adds Protein instance to an existing EnzymeMLDocument instance.

    Args:
        doc (EnzymeMLDocument): The existing EnzymeMLDocument instance.
        protein (Protein): Protein instance to be added.
    """

    protein_data = protein.model_dump()
    protein_data.pop("conc_unit")
    protein_data.pop("init_conc")

    doc.proteins.append(Protein(**protein_data))


def add_molecule(doc: EnzymeMLDocument, molecule: Molecule) -> None:
    """Adds a Molecule instance to an existing EnzymeMLDocument instance.

    Args:
        doc (EnzymeMLDocument): The existing EnzymeMLDocument instance.
        molecule (Molecule): Molecule instance to be added.

    Returns:
        EnzymeMLDocument: The updated EnzymeMLDocument instance.
    """

    pubchem_base_url = "https://pubchem.ncbi.nlm.nih.gov/compound/"

    mol_data = {
        "id": molecule.id,
        "name": molecule.name,
        "constant": molecule.constant,
    }

    if molecule.pubchem_cid > -1:
        mol_data["ld_id"] = f"{pubchem_base_url}{molecule.pubchem_cid}"

    doc.small_molecules.append(SmallMolecule(**mol_data))


def create_MeasurementData_instances(
    meas_data_dict: dict[str, MeasurementData],
    species: Molecule | Protein,
) -> None:
    """Adds a MeasurementData for a Protein or Molecule instance to a dictionary
    of MeasurementData instances.

    Args:
        meas_data_dict (dict[str, MeasurementData]): Dictionary of MeasurementData instances.
        molecule (Molecule | Protein): Molecule or Protein instance.

    Raises:
        ValueError: If a MeasurementData instance for the molecule or protein already exists.
        TypeError: If the species is neither a Molecule nor a Protein instance.
        AssertionError: If the concentration unit of the molecule / protein is not defined.
    """

    _check_molecule_conc_unit_and_init_conc(species)

    if species.id in meas_data_dict:
        raise ValueError(f"""
        A MeasurementData instance for molecule {species.name} already exists.
        """)

    # Determine the data type based on the species type
    if isinstance(species, Molecule):
        data_type = DataTypes.PEAK_AREA
    elif isinstance(species, ChromProtein):
        data_type = DataTypes.CONCENTRATION
    else:
        raise TypeError(f"""
        The species {species.name} is neither a Molecule nor a Protein instance. {type(species)} was found.
        """)

    assert isinstance(species.conc_unit, UnitDefinition), f"""
    The concentration unit of the molecule {species.name} needs to be defined.
    Please specify the `conc_unit` attribute of {species.name}.
    """

    meas_data_dict[species.id] = MeasurementData(
        species_id=species.id,
        initial=species.init_conc,
        data_unit=EnzymeMLUnitDefinition(**species.conc_unit.model_dump()),
        data_type=data_type,
    )


def add_measurements_to_enzymeml(
    doc: EnzymeMLDocument,
    new_measurements: list[Measurement],
    molecules: list[Molecule],
    calculate_concentration: bool,
    extrapolate: bool,
    internal_standard: Molecule | None = None,
) -> EnzymeMLDocument:
    """
    Adds new measurements to an existing EnzymeMLDocument instance.

    Args:
        doc (EnzymeMLDocument): The existing EnzymeMLDocument instance.
        new_measurements (list[Measurement]): List of new Measurement instances to be added.
        molecules (list[Molecule]): List of Molecule instances.
        internal_standard (Molecule, optional): The internal standard molecule, if any.
        calculate_concentration (bool, optional): If True, the concentration of the molecules will be calculated.

    Returns:
        EnzymeMLDocument: The updated EnzymeMLDocument instance.
    """

    # Extract measurement conditions from the new measurements
    ph, temp, time_unit, temp_unit = extract_measurement_conditions(new_measurements)

    # Create MeasurementData instances for existing molecules
    measurement_data_instances = {
        mol.id: MeasurementData(
            species_id=mol.id,
            initial=mol.init_conc,
            data_unit=EnzymeMLUnitDefinition(**mol.conc_unit.model_dump()),  # type: ignore
            data_type=DataTypes.PEAK_AREA,
            time_unit=EnzymeMLUnitDefinition(**time_unit.model_dump()),
        )
        for mol in molecules
    }

    # Convert new measurements to MeasurementData instances
    measurement_data_instances = add_measurement_to_MeasurementData(
        measurements=new_measurements,
        measurement_data_instances=measurement_data_instances,
        calculate_concentration=calculate_concentration,
        molecules=molecules,
        internal_standard=internal_standard,
        extrapolate=extrapolate,
    )

    # Create new EnzymeMLMeasurement and append to the document
    new_measurement_id = f"m{len(doc.measurements)}"
    enzml_measurement = EnzymeMLMeasurement(
        id=new_measurement_id,
        name=new_measurement_id,
        temperature=temp,
        temperature_unit=EnzymeMLUnitDefinition(**temp_unit.model_dump()),
        ph=ph,
        species_data=list(measurement_data_instances.values()),
    )

    doc.measurements.append(enzml_measurement)

    return doc


def add_measurement_to_MeasurementData(
    measurements: list[Measurement],
    measurement_data_instances: dict[str, MeasurementData],
    calculate_concentration: bool,
    molecules: list[Molecule],
    internal_standard: Molecule | None,
    extrapolate: bool,
) -> dict[str, MeasurementData]:
    """Converts a list of chromatographic Measurement instances to
    EnzymeML MeasurementData instances.
    This method takes into account that not all molecules are measured in each
    chromatographic measurement.
    If a peak in any of the measurements is assigned to a molecule, the molecule
    is considered as a measured molecule. Thus, if in one of the measurements
    this molecule is not measured, the data array of the MeasurementData instance
    will be filled with a peak area of 0.

    Args:
        measurements (list[Measurement]): List of Measurement instances.
        measurement_data_instances (dict[str, MeasurementData]): Dictionary containing
            the molecule IDs as keys and MeasurementData instances as values.
        calculate_concentration (bool): If True, the concentration of the molecules will be calculated,
            using the internal standard or defined standard.
        internal_standard (Molecule, optional): The internal standard molecule.

    Returns:
        dict[str, EnzymeMLMeasurement]: Dictionary containing the molecule IDs as keys
            and EnzymeMLMeasurement instances as values.
    """
    all_moecules = {molecule.id: molecule for molecule in molecules}
    measured_once = get_measured_once(list(all_moecules.keys()), measurements)

    # exclude internal stanard molecules if there are any
    if internal_standard:
        measured_once.discard(internal_standard.id)

    # check if any molecule has an external standard
    has_external_standard = any([molecule.standard for molecule in molecules])

    # decide concentration calculation strategy for each molecule

    if calculate_concentration:
        if internal_standard and has_external_standard:
            raise ValueError(
                """
                Both internal and external standards are defined. Please choose one.
                """
            )
        elif has_external_standard:
            strategy = CalibratorType.EXTERNAL
            calibrators = setup_external_calibrators(molecules)

        elif internal_standard is not None:
            strategy = CalibratorType.INTERNAL
            calibrators = setup_internal_calibrators(
                internal_standard,
                molecules,
                measurements[0],
            )
        else:
            warnings.warn(
                "`calculate_concentration` is set to True, but no internal or external standards are defined."
            )
            strategy = CalibratorType.NONE
            calibrators = {}
            calculate_concentration = False

    else:
        strategy = CalibratorType.NONE
        calibrators = {}
        calculate_concentration = False

    for meas_idx, measurement in enumerate(measurements):
        for chrom in measurement.chromatograms:
            for molecule_id in measured_once:
                add_data(
                    measurement_data=measurement_data_instances[molecule_id],
                    chromatogram=chrom,
                    reaction_time=measurement.reaction_time,
                    calibrators=calibrators,
                    calibrator_type=strategy,
                    extrapolate=extrapolate,
                )

    return measurement_data_instances


def add_data(
    measurement_data: MeasurementData,
    chromatogram: Chromatogram,
    reaction_time: float,
    calibrators: dict[str, Calibrator | InternalStandard],
    calibrator_type: CalibratorType,
    extrapolate: bool,
):
    peak = next(
        (
            peak
            for peak in chromatogram.peaks
            if peak.molecule_id == measurement_data.species_id
        ),
        None,
    )

    measurement_data.time.append(reaction_time)

    if calibrator_type == CalibratorType.EXTERNAL:
        calibrator = calibrators[measurement_data.species_id]
        assert isinstance(
            calibrator, Calibrator
        ), "Calibrator must be of type Calibrator."

        if peak is not None:
            conc = calibrator.calculate_concentrations(
                model=calibrator.standard.result,
                signals=[peak.area],
                extrapolate=extrapolate,
            )[0]

            measurement_data.data.append(conc)
            measurement_data.data_type = DataTypes.CONCENTRATION

        else:
            measurement_data.data.append(float(0))
            measurement_data.data_type = DataTypes.CONCENTRATION

    elif calibrator_type == CalibratorType.INTERNAL:
        calibrator = calibrators[measurement_data.species_id]
        assert isinstance(
            calibrator, InternalStandard
        ), "Calibrator must be of type InternalStandard."

        if peak is not None:
            internal_std_peak = next(
                (
                    peak
                    for peak in chromatogram.peaks
                    if peak.molecule_id == calibrator.standard_molecule_id
                ),
                None,
            )

            assert internal_std_peak is not None, f"""
                No peak for the internal standard molecule {calibrator.molecule_id}
                was detected in one of the chromatograms.
                """

            conc = calibrator.calculate_conc(peak.area, internal_std_peak.area)
            measurement_data.data.append(conc)
            measurement_data.data_type = DataTypes.CONCENTRATION

        else:
            measurement_data.data.append(float(0))
            measurement_data.data_type = DataTypes.CONCENTRATION

    elif calibrator_type == CalibratorType.NONE:
        assert calibrators == {}, "Calibrators must be empty."

        if peak is not None:
            measurement_data.data.append(peak.area)
            measurement_data.data_type = DataTypes.PEAK_AREA

        else:
            measurement_data.data.append(float(0))
            measurement_data.data_type = DataTypes.PEAK_AREA


def setup_external_calibrators(
    molecules: list[Molecule],
) -> dict[str, Calibrator]:
    """Creates calibrators for molecules with defined external standards.

    Args:
        molecules (list[Molecule]): List of Molecule instances.

    Returns:
        dict[str, Calibrator]: Dictionary containing molecule IDs as keys and
        Calibrator instances as values.

    Raises:
        AssertionError: If no calibrators were created.
    """

    calibrators: dict[str, Calibrator] = {}
    for molecule in molecules:
        if molecule.standard:
            calibrators[molecule.id] = Calibrator.from_standard(molecule.standard)

    assert (
        calibrators
    ), "No calibrators were created. Please define standards for the molecules."

    return calibrators


def setup_internal_calibrators(
    internal_standard: Molecule,
    molecules: list[Molecule],
    first_measurement: Measurement,
) -> dict[str, InternalStandard]:
    """Creates an internal calibrator for each measured molecule."""

    calibrators: dict[str, InternalStandard] = {}

    for molecule in molecules:
        if molecule.id == internal_standard.id:
            continue

        if internal_standard.init_conc is None:
            raise ValueError(f"""
            No initial concentration is defined for the internal standard molecule {internal_standard.name}.
            """)
        if internal_standard.conc_unit is None:
            raise ValueError(f"""
            No concentration unit is defined for the internal standard molecule {internal_standard.name}.
            """)
        if molecule.init_conc is None:
            raise ValueError(f"""
            No initial concentration is defined for molecule {molecule.name}.
            """)
        if molecule.conc_unit is None:
            raise ValueError(f"""
            No concentration unit is defined for molecule {molecule.name}.
            """)

        for chrom in first_measurement.chromatograms:
            peak_analyte = next(
                (peak for peak in chrom.peaks if peak.molecule_id == molecule.id),
                None,
            )

            peak_internal_standard = next(
                (
                    peak
                    for peak in chrom.peaks
                    if peak.molecule_id == internal_standard.id
                ),
                None,
            )

        if peak_analyte and peak_internal_standard:
            calibrators[molecule.id] = InternalStandard(
                molecule_id=molecule.id,
                standard_molecule_id=internal_standard.id,
                molecule_init_conc=molecule.init_conc,
                standard_init_conc=internal_standard.init_conc,
                molecule_conc_unit=molecule.conc_unit,
                molecule_t0_signal=peak_analyte.area,
                standard_t0_signal=peak_internal_standard.area,
            )

    return calibrators


def extract_measurement_conditions(
    measurements: list[Measurement],
) -> tuple[float, float, UnitDefinition, UnitDefinition]:
    """Asserts and extracts the measurement conditions from a list of Measurement instances.

    Args:
        measurements (list[Measurement]): List of Measurement instances.

    Returns:
        tuple: A tuple containing the extracted measurement conditions
            (ph, temperature, time_unit, temperature_unit).
    """

    # extract measurement conditions
    phs = [measurement.ph for measurement in measurements]
    temperatures = [measurement.temperature for measurement in measurements]
    time_units = [measurement.time_unit.name for measurement in measurements]
    temperature_units = [
        measurement.temperature_unit.name  # type: ignore
        for measurement in measurements  # type: ignore
    ]

    assert len(set(phs)) == 1, "All measurements need to have the same pH."
    assert (
        len(set(temperatures)) == 1
    ), "All measurements need to have the same temperature."
    assert (
        len(set(time_units)) == 1
    ), "All measurements need to have the same time unit."
    assert (
        len(set(temperature_units)) == 1
    ), "All measurements need to have the same temperature unit."

    assert measurements[0].ph is not None, "The pH needs to be defined."
    assert (
        measurements[0].temperature is not None
    ), "The temperature needs to be defined."
    assert measurements[0].time_unit is not None, "The time unit needs to be defined."
    assert (
        measurements[0].temperature_unit is not None
    ), "The temperature unit needs to be defined."

    ph = measurements[0].ph
    temperature = measurements[0].temperature
    time_unit = measurements[0].time_unit
    temperature_unit = measurements[0].temperature_unit

    return ph, temperature, time_unit, temperature_unit


def get_measured_once(
    molecule_ids: list[str], measurements: list[Measurement]
) -> set[str]:
    """Checks if a molecule is assigned to a peak at least once in the measurements.

    Args:
        molecule_ids (list[str]): List of molecule IDs.
        measurements (list[Measurement]): List of Measurement instances.

    Returns:
        set[str]: Set containing the molecule IDs that are assigned to a peak at least once.
    """

    # Initialize the dictionary with False for each molecule ID
    return {
        peak.molecule_id
        for measurement in measurements
        for chrom in measurement.chromatograms
        for peak in chrom.peaks
        if peak.molecule_id is not None
    }


def _check_molecule_conc_unit_and_init_conc(molecule: Molecule):
    if molecule.init_conc is None:
        raise ValueError(f"""
        No initial concentration is defined for molecule {molecule.name}.
        Please specify the initial concentration of the molecule.
        """)

    if molecule.conc_unit is None:
        if molecule.standard:
            molecule.conc_unit = molecule.standard.samples[0].conc_unit
        else:
            raise ValueError(f"""
            No concentration unit is defined for molecule {molecule.name}.
            Please specify the concentration unit or define a standard for the molecule.
            """)


def patch_init_t0(doc: EnzymeMLDocument):
    for meas in doc.measurements:
        for species_data in meas.species_data:
            if species_data.data:
                if not species_data.initial == species_data.data[0]:
                    species_data.prepared = species_data.initial
                    species_data.initial = species_data.data[0]
