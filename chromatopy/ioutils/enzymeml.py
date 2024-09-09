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

from chromatopy.model import Measurement
from chromatopy.model import UnitDefinition as UnitDefinition
from chromatopy.tools.internal_standard import InternalStandard
from chromatopy.tools.molecule import Molecule


def create_enzymeml(
    name: str,
    molecules: list[Molecule],
    proteins: list[Protein],
    measurements: list[Measurement],
    internal_standard: Molecule | None,
    calculate_concentration: bool,
) -> EnzymeMLDocument:
    """Creates an EnzymeMLDocument instance from a list of Molecule and Measurement instances.

    Args:
        molecules (list[Molecule]): List of Molecule instances.
        proteins (list[Protein]): List of Protein instances.
        measurements (list[Measurement]): List of Measurement instances.
        calculate_concentration (bool): If True, the concentration of the molecules will be calculated,
            using the internal standard or defined standard.

    Returns:
        EnzymeMLDocument: The EnzymeMLDocument instance.
    """

    doc = EnzymeMLDocument(name=name)

    # check if concentration unit is defined for each molecule

    measurement_data_instances = {}
    # add EnzymeML SmallMolecules
    for molecule in molecules:
        _check_molecule_conc_unit_and_init_conc(molecule)
        doc.small_molecules.append(
            SmallMolecule(
                id=molecule.id,
                name=molecule.name,
                ld_id=f"https://pubchem.ncbi.nlm.nih.gov/compound/{molecule.pubchem_cid}",
            )
        )

        # create MeasurementData instances for each molecule
        measurement_data_instances[molecule.id] = MeasurementData(
            species_id=molecule.id,
            initial=molecule.init_conc,
            data_unit=EnzymeMLUnitDefinition(**molecule.conc_unit.model_dump()),  # type: ignore
            data_type=DataTypes.PEAK_AREA,
        )

    from devtools import pprint

    # add Proteins
    for protein in proteins:
        protein_data = protein.model_dump()
        pprint(protein_data)
        protein_data.pop("conc_unit")
        protein_data.pop("init_conc")

        doc.proteins.append(Protein(**protein_data))

        # create MeasurementData instances for each molecule
        measurement_data_instances[molecule.id] = MeasurementData(
            species_id=molecule.id,
            initial=molecule.init_conc,
            data_unit=EnzymeMLUnitDefinition(**protein.conc_unit.model_dump()),
            data_type=DataTypes.PEAK_AREA,
        )

    # add data to MeasurementData instances
    measurement_data_instances = measurements_to_measurmentdata(
        measurements=measurements,
        measurement_data_instances=measurement_data_instances,
        calculate_concentration=calculate_concentration,
        molecules=molecules,
        internal_standard=internal_standard,
    )

    # create EnzymeML Measurement
    ph, temp, time_unit, temp_unit = extract_measurement_conditions(measurements)

    enzml_measurement = EnzymeMLMeasurement(
        id="m0",
        name="m0",
        temperature=temp,
        temperature_unit=EnzymeMLUnitDefinition(**temp_unit.model_dump()),
        ph=ph,
        species_data=list(measurement_data_instances.values()),
    )

    doc.measurements.append(enzml_measurement)

    return doc


def add_measurements_to_enzymeml(
    doc: EnzymeMLDocument,
    new_measurements: list[Measurement],
    molecules: list[Molecule],
    internal_standard: Molecule | None = None,
    calculate_concentration: bool = False,
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

    # Create MeasurementData instances for existing molecules
    measurement_data_instances = {
        mol.id: MeasurementData(
            species_id=mol.id,
            initial=mol.init_conc,
            data_unit=EnzymeMLUnitDefinition(**mol.conc_unit.model_dump()),  # type: ignore
            data_type=DataTypes.PEAK_AREA,
        )
        for mol in molecules
    }

    # Convert new measurements to MeasurementData instances
    measurement_data_instances = measurements_to_measurmentdata(
        measurements=new_measurements,
        measurement_data_instances=measurement_data_instances,
        calculate_concentration=calculate_concentration,
        molecules=molecules,
        internal_standard=internal_standard,
    )

    # Extract measurement conditions from the new measurements
    ph, temp, time_unit, temp_unit = extract_measurement_conditions(new_measurements)

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


def measurements_to_measurmentdata(
    measurements: list[Measurement],
    measurement_data_instances: dict[str, MeasurementData],
    calculate_concentration: bool,
    molecules: list[Molecule],
    internal_standard: Molecule | None,
) -> dict[str, EnzymeMLMeasurement]:
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
    measured_once = measured_molecule_dict(list(all_moecules.keys()), measurements)
    has_external_standard = any([molecule.standard for molecule in molecules])

    # setup internal standard if it exists
    if calculate_concentration and internal_standard:
        internal_std_dict = {}
        for molecule_id in measured_once:
            if internal_standard.id == molecule_id:
                continue
            assert internal_standard.init_conc, f"""
            The initial concentration of the internal standard molecule {internal_standard.name}
            needs to be defined. Please specify the `init_conc` attribute of the molecule.
            """
            assert internal_standard.conc_unit, f"""
            The concentration unit of the internal standard molecule {internal_standard.name}
            needs to be defined. Please specify the `conc_unit` attribute of the molecule.
            """

            assert all_moecules[molecule_id].init_conc, f"""
            The initial concentration of the molecule {all_moecules[molecule_id].name}
            needs to be defined. Please specify the `init_conc` attribute of the molecule.
            """

            internal_std_dict[molecule_id] = InternalStandard(
                molecule_id=molecule_id,
                standard_molecule_id=internal_standard.id,
                molecule_init_conc=all_moecules[molecule_id].init_conc,  # type: ignore
                standard_init_conc=internal_standard.init_conc,
                molecule_conc_unit=internal_standard.conc_unit,
            )

    if calculate_concentration and has_external_standard:
        calibrators: dict[str, Calibrator] = {}
        for molecule in molecules:
            if molecule.standard:
                calibrators[molecule.id] = Calibrator.from_standard(molecule.standard)

    for meas_idx, measurement in enumerate(measurements):
        if calculate_concentration:
            # set t0 signals for each internal standard if the measurement is at t=0
            if internal_standard:
                if meas_idx == 0:
                    for internal_std in internal_std_dict.values():
                        internal_std._set_t0_signals(measurement)

        for molecule_id in measurement_data_instances:
            # skip virtual molecules without peaks
            if not measured_once[molecule_id]:
                continue
            # add time and time unit to MeasurementData instance
            measurement_data_instances[molecule_id].time.append(
                measurement.reaction_time
            )
            measurement_data_instances[molecule_id].time_unit = (
                EnzymeMLUnitDefinition(**measurement.time_unit.model_dump()),
            )

            # get peak of measurement, if it exists for the molecule_id
            for chrom in measurement.chromatograms:
                peak = next(
                    (peak for peak in chrom.peaks if peak.molecule_id == molecule_id),
                    None,
                )
                if peak:
                    break

            if internal_standard and peak:
                internal_std_peak = next(
                    (
                        peak
                        for peak in chrom.peaks
                        if peak.molecule_id
                        == internal_std_dict[molecule_id].standard_molecule_id
                    ),
                    None,
                )
                if internal_std_peak:
                    break

                assert internal_std_peak is not None, f"""
                No peak for the internal standard molecule {internal_std_dict[molecule_id]}
                was assigned in measurement {meas_idx}.
                """

                internal_calibrator = internal_std_dict[molecule_id]
                measurement_data_instances[molecule_id].data.append(
                    internal_calibrator.calculate_conc(
                        peak.area, internal_std_peak.area
                    )
                )
                measurement_data_instances[
                    molecule_id
                ].data_type = DataTypes.CONCENTRATION

            elif has_external_standard and peak:
                try:
                    print(f"calculating concentration for molecule {molecule_id}")
                    print(
                        f"is not extrapolate: {peak.area < calibrators[molecule_id].standard.result.calibration_range.signal_upper}"
                    )
                    print(calibrators[molecule_id].molecule_id)
                    measurement_data_instances[molecule_id].data.append(
                        calibrators[molecule_id].calculate_concentrations(
                            model=calibrators[molecule_id].standard.result,
                            signals=[peak.area],
                        )[0]
                    )
                    measurement_data_instances[
                        molecule_id
                    ].data_type = DataTypes.CONCENTRATION

                except KeyError:
                    print(f"no calibrator for molecule {molecule_id}")
                    continue

            elif peak and not calculate_concentration:
                measurement_data_instances[molecule_id].data.append(peak.area)
                measurement_data_instances[molecule_id].data_type = DataTypes.PEAK_AREA

            # if no peak is assigned, add 0 to data array
            elif not peak and calculate_concentration:
                measurement_data_instances[molecule_id].data.append(0)
                measurement_data_instances[
                    molecule_id
                ].data_type = DataTypes.CONCENTRATION

            else:
                measurement_data_instances[molecule_id].data_type = DataTypes.PEAK_AREA
                measurement_data_instances[molecule_id].data.append(0)

    return measurement_data_instances


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


def measured_molecule_dict(
    molecule_ids: list[str], measurements: list[Measurement]
) -> dict[str, bool]:
    """Checks if all molecules are assigned at least one peak in the measurements.

    Args:
        molecule_ids (list[str]): List of molecule IDs.
        measurements (list[Measurement]): List of Measurement instances.

    Returns:
        dict[str, bool]: A dictionary with molecule IDs as keys and boolean values indicating
                         whether each molecule is assigned to at least one peak.
    """

    # Initialize the dictionary with False for each molecule ID
    measured_dict = {mol_id: False for mol_id in molecule_ids}

    # Iterate through each measurement
    for measurement in measurements:
        # Iterate through each chromatogram in the measurement
        for chrom in measurement.chromatograms:
            # Iterate through each peak in the chromatogram
            for peak in chrom.peaks:
                # Mark the molecule ID as True if it is found in a peak
                if peak.molecule_id in measured_dict:
                    measured_dict[peak.molecule_id] = True

    return measured_dict


def _check_molecule_conc_unit_and_init_conc(molecule: Molecule):
    if molecule.init_conc is None:
        raise ValueError(f"""
        No initial concentration is defined for molecule {molecule.name}.
        Please specify the initial concentration of the molecule.
        """)

    elif molecule.conc_unit:
        return

    elif molecule.conc_unit is None and molecule.standard:
        molecule.conc_unit = molecule.standard.samples[0].conc_unit
        return

    else:
        raise ValueError(f"""
        No concentration unit is defined for molecule {molecule.name}.
        Please specify the concentration unit or define a standard for the molecule.
        """)
