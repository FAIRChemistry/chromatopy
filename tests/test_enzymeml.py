import warnings
from unittest.mock import Mock

import pytest
from pyenzyme import (
    DataTypes,
    EnzymeMLDocument,
    MeasurementData,
)
from pyenzyme import Measurement as EnzymeMLMeasurement

from chromhandler.enzymeml import (
    CalibratorType,
    _check_molecule_conc_unit_and_init_conc,
    add_data,
    add_measurement_to_MeasurementData,
    add_measurements_to_enzymeml,
    add_molecule,
    add_protein,
    create_enzymeml,
    extract_measurement_conditions,
    get_measured_once,
    patch_init_t0,
    setup_external_calibrators,
    to_enzymeml,
)
from chromhandler.handler import Handler
from chromhandler.internal_standard import InternalStandard
from chromhandler.model import Chromatogram, Data, Measurement, Peak
from chromhandler.molecule import Molecule
from chromhandler.protein import Protein as ChromProtein


class TestCalibratorType:
    """Test the CalibratorType enum."""

    def test_calibrator_type_values(self) -> None:
        """Test that enum values are correct."""
        assert CalibratorType.EXTERNAL.value == "external_standard"
        assert CalibratorType.INTERNAL.value == "internal_standard"
        assert CalibratorType.NONE.value == "none"


class TestFixtures:
    """Test fixture setup for enzymeml tests with real objects."""

    @pytest.fixture
    def unit_definition(self) -> str:
        """Create a real unit definition for millimolar."""
        return "mmol / l"

    @pytest.fixture
    def time_unit(self) -> str:
        """Create a real time unit definition."""
        return "minute"

    @pytest.fixture
    def temp_unit(self) -> str:
        """Create a real temperature unit definition."""
        return "Celsius"

    @pytest.fixture
    def molecule(self, unit_definition: str) -> Molecule:
        """Create a real Molecule."""
        return Molecule(
            id="mol1",
            name="Molecule 1",
            pubchem_cid=123,
            init_conc=1.0,
            conc_unit=unit_definition,
            constant=False,
            internal_standard=False,
        )

    @pytest.fixture
    def internal_standard_molecule(self, unit_definition: str) -> Molecule:
        """Create a real internal standard Molecule."""
        return Molecule(
            id="is_mol",
            name="Internal Standard",
            pubchem_cid=456,
            init_conc=2.0,
            conc_unit=unit_definition,
            constant=False,
            internal_standard=True,
        )

    @pytest.fixture
    def protein(self, unit_definition: str) -> ChromProtein:
        """Create a real Protein."""
        return ChromProtein(
            id="prot1",
            name="Protein 1",
            init_conc=0.5,
            conc_unit=unit_definition,
            constant=True,
        )

    @pytest.fixture
    def peak(self) -> Peak:
        """Create a real Peak."""
        return Peak(retention_time=5.2, area=1000.0, molecule_id="mol1")

    @pytest.fixture
    def chromatogram(self, peak: Peak) -> Chromatogram:
        """Create a real Chromatogram."""
        chromatogram = Chromatogram()
        chromatogram.peaks = [peak]
        return chromatogram

    @pytest.fixture
    def measurement(
        self, chromatogram: Chromatogram, time_unit: str, temp_unit: str
    ) -> Measurement:
        """Create a real Measurement."""
        from chromhandler.model import DataType

        data = Data(value=0.0, unit=time_unit, data_type=DataType.TIMECOURSE)
        return Measurement(
            id="meas1",
            data=data,
            temperature=25.0,
            temperature_unit=temp_unit,
            ph=7.0,
            chromatograms=[chromatogram],
            dilution_factor=1.0,
        )

    @pytest.fixture
    def analyzer(
        self, molecule: Molecule, protein: ChromProtein, measurement: Measurement
    ) -> Handler:
        """Create a real Handler."""
        return Handler(
            id="analyzer1",
            name="Test Analyzer",
            mode="timecourse",
            molecules=[molecule],
            proteins=[protein],
            measurements=[measurement],
        )

    @pytest.fixture
    def internal_standard(self, unit_definition: str) -> InternalStandard:
        """Create a real InternalStandard."""
        return InternalStandard(
            molecule_id="mol1",
            standard_molecule_id="is_mol",
            molecule_init_conc=1.0,
            standard_init_conc=2.0,
            molecule_conc_unit=unit_definition,
            molecule_t0_signal=1000.0,
            standard_t0_signal=500.0,
        )


class TestToEnzymeML(TestFixtures):
    """Test the to_enzymeml function."""

    def test_to_enzymeml_single_analyzer(self, analyzer: Handler) -> None:
        """Test converting a single analyzer to EnzymeML."""
        result = to_enzymeml(
            document_name="Test Document",
            analyzers=analyzer,
            calculate_concentration=False,
        )

        assert isinstance(result, EnzymeMLDocument)
        assert result.name == "Test Document"
        assert len(result.measurements) == 1
        assert len(result.small_molecules) == 1
        assert len(result.proteins) == 1

    def test_to_enzymeml_multiple_analyzers(self, analyzer: Handler) -> None:
        """Test converting multiple analyzers to EnzymeML."""
        # Create a second measurement for the second analyzer
        from chromhandler.model import DataType

        second_measurement = Measurement(
            id="meas2",
            data=Data(value=5.0, unit="minute", data_type=DataType.TIMECOURSE),
            temperature=25.0,
            temperature_unit="Celsius",
            ph=7.0,
            chromatograms=analyzer.measurements[0].chromatograms,
            dilution_factor=1.0,
        )

        # Create second analyzer with different measurement
        analyzer2 = Handler(
            id="analyzer2",
            name="Test Analyzer 2",
            mode="timecourse",
            molecules=analyzer.molecules,
            proteins=analyzer.proteins,
            measurements=[second_measurement],
        )

        result = to_enzymeml(
            document_name="Test Document",
            analyzers=[analyzer, analyzer2],
            calculate_concentration=False,
        )

        assert isinstance(result, EnzymeMLDocument)
        assert result.name == "Test Document"
        assert len(result.measurements) == 2
        assert len(result.small_molecules) == 1
        assert len(result.proteins) == 1

    def test_to_enzymeml_with_internal_standard_invalid_count(
        self, analyzer: Handler
    ) -> None:
        """Test with invalid internal standard count (should raise ValueError)."""
        # No internal standard molecules in the analyzer
        with pytest.raises(ValueError, match="Exaclty one internal standard molecule"):
            to_enzymeml(
                document_name="Test Document",
                analyzers=analyzer,
                calculate_concentration=True,
                internal_standard=True,
            )

    def test_to_enzymeml_converts_single_analyzer_to_list(
        self, analyzer: Handler
    ) -> None:
        """Test that single analyzer is converted to list."""
        result = to_enzymeml(
            document_name="Test Document",
            analyzers=analyzer,  # Single analyzer, not list
            calculate_concentration=False,
        )

        assert isinstance(result, EnzymeMLDocument)
        assert result.name == "Test Document"


class TestCreateEnzymeML(TestFixtures):
    """Test the create_enzymeml function."""

    def test_create_enzymeml_basic(
        self, molecule: Molecule, protein: ChromProtein, measurement: Measurement
    ) -> None:
        """Test basic create_enzymeml functionality."""
        result = create_enzymeml(
            document_name="Test Document",
            molecules=[molecule],
            proteins=[protein],
            measurements=[measurement],
            measurement_id="test_measurement",
            calculate_concentration=False,
            extrapolate=False,
        )

        assert isinstance(result, EnzymeMLDocument)
        assert result.name == "Test Document"
        assert len(result.measurements) == 1
        assert len(result.small_molecules) == 1
        assert len(result.proteins) == 1

        # Check that measurement data was created correctly
        enzml_measurement = result.measurements[0]
        assert enzml_measurement.id == "test_measurement"
        assert enzml_measurement.ph == 7.0
        assert enzml_measurement.temperature == 25.0
        assert len(enzml_measurement.species_data) == 2  # molecule + protein

    def test_create_enzymeml_skips_internal_standard_molecules(
        self,
        molecule: Molecule,
        internal_standard_molecule: Molecule,
        protein: ChromProtein,
        measurement: Measurement,
    ) -> None:
        """Test that internal standard molecules are skipped when adding to document."""
        result = create_enzymeml(
            document_name="Test Document",
            molecules=[molecule, internal_standard_molecule],
            proteins=[protein],
            measurements=[measurement],
            measurement_id="test_measurement",
            calculate_concentration=False,
            extrapolate=False,
        )

        # Should only have 1 small molecule (not the internal standard)
        assert len(result.small_molecules) == 1
        assert result.small_molecules[0].id == "mol1"


class TestAddMeasurementsToEnzymeML(TestFixtures):
    """Test the add_measurements_to_enzymeml function."""

    def test_add_measurements_basic(
        self, molecule: Molecule, protein: ChromProtein, measurement: Measurement
    ) -> None:
        """Test basic functionality of adding measurements."""
        # Create initial document
        doc = EnzymeMLDocument(name="Test Document")

        # Create a second measurement
        from chromhandler.model import DataType

        second_measurement = Measurement(
            id="meas2",
            data=Data(value=5.0, unit="minute", data_type=DataType.TIMECOURSE),
            temperature=25.0,
            temperature_unit="Celsius",
            ph=7.0,
            chromatograms=measurement.chromatograms,
            dilution_factor=1.0,
        )

        result = add_measurements_to_enzymeml(
            doc=doc,
            new_measurements=[second_measurement],
            molecules=[molecule],
            proteins=[protein],
            calculate_concentration=False,
            extrapolate=False,
            measurement_id="test_measurement_2",
        )

        assert result == doc
        assert len(doc.measurements) == 1
        assert doc.measurements[0].id == "test_measurement_2"

    def test_add_measurements_missing_molecule_conc_unit(
        self, measurement: Measurement
    ) -> None:
        """Test error when molecule concentration unit is missing."""
        doc = EnzymeMLDocument(name="Test Document")
        molecule_no_unit = Molecule(
            id="mol_no_unit",
            name="Molecule No Unit",
            pubchem_cid=789,
            init_conc=1.0,
            conc_unit=None,  # Missing unit
        )

        with pytest.raises(
            ValueError, match="Concentration unit is not defined for molecule"
        ):
            add_measurements_to_enzymeml(
                doc=doc,
                new_measurements=[measurement],
                molecules=[molecule_no_unit],
                proteins=[],
                calculate_concentration=False,
                extrapolate=False,
                measurement_id="test_measurement",
            )


class TestExtractMeasurementConditions(TestFixtures):
    """Test the extract_measurement_conditions function."""

    def test_extract_measurement_conditions_success(
        self, measurement: Measurement
    ) -> None:
        """Test successful extraction of measurement conditions."""
        measurements = [measurement, measurement]  # Same conditions

        result = extract_measurement_conditions(measurements)

        ph, temp, time_unit, temp_unit = result
        assert ph == 7.0
        assert temp == 25.0
        assert time_unit.name == "min"
        assert temp_unit.name == "deg_C"

    def test_extract_measurement_conditions_different_ph(
        self, measurement: Measurement
    ) -> None:
        """Test error when measurements have different pH values."""
        from chromhandler.model import DataType

        measurement2 = Measurement(
            id="meas2",
            data=Data(value=0.0, unit="minute", data_type=DataType.TIMECOURSE),
            temperature=25.0,
            temperature_unit="Celsius",
            ph=8.0,  # Different pH
            chromatograms=measurement.chromatograms,
            dilution_factor=1.0,
        )

        with pytest.raises(
            AssertionError, match="All measurements need to have the same pH"
        ):
            extract_measurement_conditions([measurement, measurement2])

    def test_extract_measurement_conditions_missing_ph(self) -> None:
        """Test error when pH is missing (create measurement without pH validation)."""
        # Since Measurement model validates pH, we test the assertion by
        # directly patching the measurement object

        mock_measurement = Mock()
        mock_measurement.ph = None
        mock_measurement.temperature = 25.0
        mock_measurement.temperature_unit = Mock()
        mock_measurement.temperature_unit.name = "Celsius"
        mock_measurement.data = Mock()
        mock_measurement.data.unit = Mock()
        mock_measurement.data.unit.name = "minute"

        with pytest.raises(AssertionError, match="The pH needs to be defined"):
            extract_measurement_conditions([mock_measurement])


class TestGetMeasuredOnce(TestFixtures):
    """Test the get_measured_once function."""

    def test_get_measured_once_with_peaks(self, measurement: Measurement) -> None:
        """Test getting molecules that are measured at least once."""
        # Add additional peaks
        peak2 = Peak(retention_time=3.0, area=500.0, molecule_id="mol2")
        peak3 = Peak(
            retention_time=4.0, area=750.0, molecule_id=None
        )  # Should be ignored

        measurement.chromatograms[0].peaks.extend([peak2, peak3])

        result = get_measured_once(["mol1", "mol2", "mol3"], [measurement])

        assert result == {"mol1", "mol2"}

    def test_get_measured_once_no_peaks(self, measurement: Measurement) -> None:
        """Test when no peaks are assigned to molecules."""
        measurement.chromatograms[0].peaks = []

        result = get_measured_once(["mol1", "mol2"], [measurement])

        assert result == set()


class TestAddProtein(TestFixtures):
    """Test the add_protein function."""

    def test_add_protein_success(self, protein: ChromProtein) -> None:
        """Test successfully adding a protein to EnzymeML document."""
        doc = EnzymeMLDocument(name="Test Document")

        add_protein(doc, protein)

        assert len(doc.proteins) == 1
        added_protein = doc.proteins[0]
        assert added_protein.id == "prot1"
        assert added_protein.name == "Protein 1"


class TestAddMolecule(TestFixtures):
    """Test the add_molecule function."""

    def test_add_molecule_with_pubchem_cid(self, molecule: Molecule) -> None:
        """Test adding molecule with PubChem CID."""
        doc = EnzymeMLDocument(name="Test Document")

        add_molecule(doc, molecule)

        assert len(doc.small_molecules) == 1
        added_molecule = doc.small_molecules[0]
        assert added_molecule.id == "mol1"
        assert added_molecule.name == "Molecule 1"
        assert not added_molecule.constant
        assert added_molecule.ld_id == "https://pubchem.ncbi.nlm.nih.gov/compound/123"

    def test_add_molecule_without_pubchem_cid(self, unit_definition: str) -> None:
        """Test adding molecule without PubChem CID."""
        doc = EnzymeMLDocument(name="Test Document")
        molecule_no_cid = Molecule(
            id="mol_no_cid",
            name="Molecule No CID",
            pubchem_cid=-1,  # No PubChem CID
            init_conc=1.0,
            conc_unit=unit_definition,
        )

        add_molecule(doc, molecule_no_cid)

        assert len(doc.small_molecules) == 1
        added_molecule = doc.small_molecules[0]
        assert added_molecule.id == "mol_no_cid"
        assert added_molecule.name == "Molecule No CID"
        # ld_id is automatically generated, so we just check it's not the PubChem one
        assert "pubchem" not in added_molecule.ld_id


class TestSetupExternalCalibrators(TestFixtures):
    """Test the setup_external_calibrators function."""

    def test_setup_external_calibrators_no_standards(self, molecule: Molecule) -> None:
        """Test error when no standards are defined."""
        molecule.standard = None

        with pytest.raises(AssertionError, match="No calibrators were created"):
            setup_external_calibrators([molecule])

    # Note: test_setup_external_calibrators_success is skipped because
    # creating a proper Calibration object requires complex setup with fitting models
    # The functionality is tested indirectly in integration tests


class TestUtilityFunctions(TestFixtures):
    """Test utility functions."""

    def test_check_molecule_conc_unit_and_init_conc_success(
        self, molecule: Molecule
    ) -> None:
        """Test successful validation of molecule concentration unit and initial concentration."""
        # Should not raise any exception
        _check_molecule_conc_unit_and_init_conc(molecule)

    def test_check_molecule_conc_unit_and_init_conc_missing_init_conc(
        self, unit_definition: str
    ) -> None:
        """Test error when initial concentration is missing."""
        molecule_no_init = Molecule(
            id="mol_no_init",
            name="Molecule No Init",
            pubchem_cid=789,
            init_conc=None,  # Missing init_conc
            conc_unit=unit_definition,
        )

        with pytest.raises(ValueError, match="No initial concentration is defined"):
            _check_molecule_conc_unit_and_init_conc(molecule_no_init)

    def test_check_molecule_conc_unit_and_init_conc_missing_conc_unit(self) -> None:
        """Test error when concentration unit is missing."""
        molecule_no_unit = Molecule(
            id="mol_no_unit",
            name="Molecule No Unit",
            pubchem_cid=789,
            init_conc=1.0,
            conc_unit=None,  # Missing conc_unit
        )

        with pytest.raises(ValueError, match="No concentration unit is defined"):
            _check_molecule_conc_unit_and_init_conc(molecule_no_unit)

    def test_patch_init_t0_with_data(self) -> None:
        """Test patch_init_t0 updates initial values when data exists."""
        doc = EnzymeMLDocument(name="Test Document")

        # Create measurement data with different initial and first data values
        species_data = MeasurementData(
            species_id="mol1",
            initial=1.0,
            prepared=1.0,
            data_unit="mmol / l",
            data_type=DataTypes.CONCENTRATION,
        )
        species_data.data = [1.5, 2.0, 2.5]  # First value different from initial

        measurement = EnzymeMLMeasurement(
            id="test_measurement",
            name="Test Measurement",
            temperature=25.0,
            temperature_unit="Celsius",
            ph=7.0,
            species_data=[species_data],
        )

        doc.measurements = [measurement]

        patch_init_t0(doc)

        # Should update initial to match first data point
        assert species_data.initial == 1.5

    def test_patch_init_t0_without_data(self) -> None:
        """Test patch_init_t0 when no data exists."""
        doc = EnzymeMLDocument(name="Test Document")

        # Create measurement data with no data
        species_data = MeasurementData(
            species_id="mol1",
            initial=1.0,
            prepared=1.0,
            data_unit="mmol / l",
            data_type=DataTypes.CONCENTRATION,
        )
        species_data.data = []  # No data

        measurement = EnzymeMLMeasurement(
            id="test_measurement",
            name="Test Measurement",
            temperature=25.0,
            temperature_unit="Celsius",
            ph=7.0,
            species_data=[species_data],
        )

        doc.measurements = [measurement]

        patch_init_t0(doc)

        # Should not change initial value
        assert species_data.initial == 1.0


class TestAddData(TestFixtures):
    """Test the add_data function with real objects."""

    # Note: test_add_data_external_calibrator_with_peak is skipped because
    # creating a proper Calibrator requires complex Calibration setup

    def test_add_data_no_calibrator_with_peak(self) -> None:
        """Test adding data without calibrator when peak exists."""
        measurement_data = MeasurementData(
            species_id="mol1",
            initial=1.0,
            prepared=1.0,
            data_unit="mmol / l",
            data_type=DataTypes.PEAK_AREA,
        )

        chromatogram = Chromatogram()
        peak = Peak(retention_time=5.0, area=1000.0, molecule_id="mol1")
        chromatogram.peaks = [peak]

        add_data(
            measurement_data=measurement_data,
            chromatogram=chromatogram,
            reaction_time=5.0,
            calibrators={},
            calibrator_type=CalibratorType.NONE,
            extrapolate=False,
            dilution_factor=1.0,
        )

        assert measurement_data.time == [5.0]
        assert measurement_data.data == [1000.0]  # Raw peak area
        assert measurement_data.data_type == DataTypes.PEAK_AREA

    def test_add_data_no_calibrator_without_peak(self) -> None:
        """Test adding data without calibrator when no peak exists."""
        measurement_data = MeasurementData(
            species_id="mol1",
            initial=1.0,
            prepared=1.0,
            data_unit="mmol / l",
            data_type=DataTypes.PEAK_AREA,
        )

        chromatogram = Chromatogram()
        chromatogram.peaks = []  # No peaks

        add_data(
            measurement_data=measurement_data,
            chromatogram=chromatogram,
            reaction_time=5.0,
            calibrators={},
            calibrator_type=CalibratorType.NONE,
            extrapolate=False,
            dilution_factor=1.0,
        )

        assert measurement_data.time == [5.0]
        assert measurement_data.data == [0.0]
        assert measurement_data.data_type == DataTypes.PEAK_AREA


class TestAddMeasurementToMeasurementData(TestFixtures):
    """Test the add_measurement_to_MeasurementData function with real objects."""

    def test_no_standards_warning(
        self, molecule: Molecule, measurement: Measurement
    ) -> None:
        """Test warning when no standards are defined but concentration calculation is requested."""
        molecule.standard = None  # No external standard

        measurement_data = MeasurementData(
            species_id="mol1",
            initial=1.0,
            prepared=1.0,
            data_unit="mmol / l",
            data_type=DataTypes.PEAK_AREA,
        )
        measurement_data_instances = {"mol1": measurement_data}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            add_measurement_to_MeasurementData(
                measurements=[measurement],
                measurement_data_instances=measurement_data_instances,
                calculate_concentration=True,
                molecules=[molecule],
            )

            assert len(w) == 1
            assert "no internal or external standards are defined" in str(w[0].message)
