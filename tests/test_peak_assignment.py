from typing import Any

import pytest
from pytest import CaptureFixture

from chromhandler.handler import Handler
from chromhandler.model import (
    Chromatogram,
    Data,
    DataType,
    Measurement,
    Peak,
    SignalType,
)
from chromhandler.molecule import Molecule


class TestPeakAssignment:
    """Test class for peak assignment functionality."""

    @pytest.fixture
    def mock_molecule(self) -> Molecule:
        """Create a test molecule with defined retention time."""
        return Molecule(
            id="test_mol",
            pubchem_cid=12345,
            name="Test Molecule",
            retention_time=5.0,  # 5 minutes
            retention_tolerance=0.2,  # ±0.2 minutes
            min_signal=100.0,  # Minimum peak area of 100
        )

    @pytest.fixture
    def mock_data(self) -> Data:
        """Create mock data for measurements."""
        return Data(value=1.0, unit="mmol/L", data_type=DataType.TIMECOURSE)

    def create_peak(self, retention_time: float, area: float) -> Peak:
        """Helper method to create a peak."""
        return Peak(retention_time=retention_time, area=area)

    def create_chromatogram(self, peaks: list[Peak]) -> Chromatogram:
        """Helper method to create a chromatogram with peaks."""
        return Chromatogram(type=SignalType.UV, peaks=peaks, wavelength=254.0)

    def create_measurement(
        self, measurement_id: str, peaks: list[Peak], data: Data
    ) -> Measurement:
        """Helper method to create a measurement with chromatograms."""
        chromatogram = self.create_chromatogram(peaks)
        return Measurement(
            id=measurement_id,
            data=data,
            temperature=25.0,
            temperature_unit="Celsius",
            ph=7.0,
            chromatograms=[chromatogram],
        )

    def create_analyzer(self, measurements: list[Measurement]) -> Handler:
        """Helper method to create an analyzer with measurements."""
        return Handler(
            id="test_analyzer",
            name="Test Analyzer",
            mode="timecourse",
            measurements=measurements,
        )

    def test_single_peak_assignment(
        self, mock_molecule: Molecule, mock_data: Data, capsys: CaptureFixture[Any]
    ) -> None:
        """Test normal case: single peak within tolerance gets assigned."""
        # Create a peak exactly at the molecule's retention time
        peaks = [self.create_peak(retention_time=5.0, area=500.0)]
        measurement = self.create_measurement("meas_001", peaks, mock_data)
        analyzer = self.create_analyzer([measurement])

        # Add molecule to analyzer
        analyzer.molecules.append(mock_molecule)

        # Register peaks
        analyzer._register_peaks(
            mock_molecule, mock_molecule.retention_tolerance, 254.0
        )

        # Check that peak was assigned
        assert peaks[0].molecule_id == "test_mol"

        # Check output message
        captured = capsys.readouterr()
        assert "🎯 Assigned Test Molecule to 1 peaks" in captured.out
        assert "Warning" not in captured.out

    def test_multiple_peaks_closest_assigned(
        self, mock_molecule: Molecule, mock_data: Data, capsys: CaptureFixture[Any]
    ) -> None:
        """Test multiple peaks: closest one gets assigned with warning."""
        # Create multiple peaks within tolerance
        peaks = [
            self.create_peak(retention_time=4.9, area=300.0),  # 0.1 min away
            self.create_peak(retention_time=5.15, area=400.0),  # 0.15 min away
            self.create_peak(retention_time=4.85, area=200.0),  # 0.15 min away
        ]
        measurement = self.create_measurement("meas_001", peaks, mock_data)
        analyzer = self.create_analyzer([measurement])

        # Add molecule to analyzer
        analyzer.molecules.append(mock_molecule)

        # Register peaks
        analyzer._register_peaks(
            mock_molecule, mock_molecule.retention_tolerance, 254.0
        )

        # Check that closest peak (4.9) was assigned
        assigned_peaks = [p for p in peaks if p.molecule_id == "test_mol"]
        assert len(assigned_peaks) == 1
        assert assigned_peaks[0].retention_time == 4.9

        # Check warning output
        captured = capsys.readouterr()
        assert "🎯 Assigned Test Molecule to 1 peaks" in captured.out
        assert "⚠️  Warning: Multiple peaks found within tolerance" in captured.out
        # The new format shows retention times in a table, check for key elements
        assert (
            "4.900" in captured.out
            and "5.150" in captured.out
            and "4.850" in captured.out
        )
        assert "4.900" in captured.out  # Should show the assigned RT
        assert "💡 Tip: Consider setting a higher min_signal value" in captured.out
        # Tips panel removed - no longer checking for it

    def test_no_peaks_found_warning(
        self, mock_molecule: Molecule, mock_data: Data, capsys: CaptureFixture[Any]
    ) -> None:
        """Test no peaks found: warning is displayed."""
        # Create measurement with no peaks in tolerance
        peaks = [
            self.create_peak(retention_time=3.0, area=500.0),  # Too far away
            self.create_peak(retention_time=7.0, area=500.0),  # Too far away
        ]
        measurement = self.create_measurement("meas_001", peaks, mock_data)
        analyzer = self.create_analyzer([measurement])

        # Add molecule to analyzer
        analyzer.molecules.append(mock_molecule)

        # Register peaks
        analyzer._register_peaks(
            mock_molecule, mock_molecule.retention_tolerance, 254.0
        )

        # Check that no peaks were assigned
        assigned_peaks = [p for p in peaks if p.molecule_id == "test_mol"]
        assert len(assigned_peaks) == 0

        # Check warning output - with new format, 0 peaks message is not shown when there are warnings
        captured = capsys.readouterr()
        assert (
            "🎯 Assigned Test Molecule to 0 peaks" not in captured.out
        )  # Should not show when warnings present
        assert (
            "⚠️  Warning: No peaks found for Test Molecule in 1 measurement(s)"
            in captured.out
        )
        assert "meas_001" in captured.out  # Should be in the table
        assert "5.000 min" in captured.out  # Expected RT in table
        # Tips panel removed - no longer checking for it

    def test_min_signal_filtering(
        self, mock_molecule: Molecule, mock_data: Data, capsys: CaptureFixture[Any]
    ) -> None:
        """Test that peaks below min_signal are filtered out."""
        # Create peaks within tolerance but below min_signal
        peaks = [
            self.create_peak(retention_time=5.0, area=50.0),  # Below min_signal (100)
            self.create_peak(retention_time=5.1, area=150.0),  # Above min_signal
        ]
        measurement = self.create_measurement("meas_001", peaks, mock_data)
        analyzer = self.create_analyzer([measurement])

        # Add molecule to analyzer
        analyzer.molecules.append(mock_molecule)

        # Register peaks
        analyzer._register_peaks(
            mock_molecule, mock_molecule.retention_tolerance, 254.0
        )

        # Check that only the peak above min_signal was assigned
        assigned_peaks = [p for p in peaks if p.molecule_id == "test_mol"]
        assert len(assigned_peaks) == 1
        assert assigned_peaks[0].area == 150.0

        # Check output
        captured = capsys.readouterr()
        assert "🎯 Assigned Test Molecule to 1 peaks" in captured.out

    def test_multiple_measurements_mixed_scenarios(
        self, mock_molecule: Molecule, mock_data: Data, capsys: CaptureFixture[Any]
    ) -> None:
        """Test complex scenario with multiple measurements having different peak scenarios."""
        # Measurement 1: Single peak (normal case)
        peaks1 = [self.create_peak(retention_time=5.0, area=300.0)]
        measurement1 = self.create_measurement("meas_001", peaks1, mock_data)

        # Measurement 2: Multiple peaks (closest assigned)
        peaks2 = [
            self.create_peak(retention_time=4.95, area=200.0),
            self.create_peak(retention_time=5.1, area=400.0),
        ]
        measurement2 = self.create_measurement("meas_002", peaks2, mock_data)

        # Measurement 3: No peaks in range
        peaks3 = [self.create_peak(retention_time=3.0, area=500.0)]
        measurement3 = self.create_measurement("meas_003", peaks3, mock_data)

        # Measurement 4: Peaks below min_signal
        peaks4 = [self.create_peak(retention_time=5.0, area=50.0)]  # Below min_signal
        measurement4 = self.create_measurement("meas_004", peaks4, mock_data)

        analyzer = self.create_analyzer(
            [measurement1, measurement2, measurement3, measurement4]
        )
        analyzer.molecules.append(mock_molecule)

        # Register peaks
        analyzer._register_peaks(
            mock_molecule, mock_molecule.retention_tolerance, 254.0
        )

        # Check assignments
        # Measurement 1: 1 peak assigned
        assigned_peaks1 = [p for p in peaks1 if p.molecule_id == "test_mol"]
        assert len(assigned_peaks1) == 1

        # Measurement 2: 1 peak assigned (closest one: 4.95)
        assigned_peaks2 = [p for p in peaks2 if p.molecule_id == "test_mol"]
        assert len(assigned_peaks2) == 1
        assert assigned_peaks2[0].retention_time == 4.95

        # Measurement 3: 0 peaks assigned
        assigned_peaks3 = [p for p in peaks3 if p.molecule_id == "test_mol"]
        assert len(assigned_peaks3) == 0

        # Measurement 4: 0 peaks assigned (below min_signal)
        assigned_peaks4 = [p for p in peaks4 if p.molecule_id == "test_mol"]
        assert len(assigned_peaks4) == 0

        # Check output contains all warnings
        captured = capsys.readouterr()
        assert "🎯 Assigned Test Molecule to 2 peaks" in captured.out
        assert "⚠️  Warning: Multiple peaks found within tolerance" in captured.out
        assert (
            "⚠️  Warning: No peaks found for Test Molecule in 2 measurement(s)"
            in captured.out
        )
        # Check that both measurement IDs appear in the new table format
        assert "meas_003" in captured.out and "meas_004" in captured.out
        # Tips panel removed - no longer checking for it

    def test_no_retention_time_raises_error(self, mock_data: Data) -> None:
        """Test that molecule without retention time raises ValueError."""
        # Create molecule without retention time
        molecule_no_rt = Molecule(
            id="no_rt_mol",
            pubchem_cid=67890,
            name="No RT Molecule",
            retention_time=None,  # No retention time
        )

        peaks = [self.create_peak(retention_time=5.0, area=300.0)]
        measurement = self.create_measurement("meas_001", peaks, mock_data)
        analyzer = self.create_analyzer([measurement])

        analyzer.molecules.append(molecule_no_rt)

        # Should raise ValueError
        with pytest.raises(
            ValueError, match="Molecule no_rt_mol has no retention time"
        ):
            analyzer._register_peaks(molecule_no_rt, 0.2, 254.0)

    def test_tolerance_boundary_conditions(
        self,
        mock_data: Data,
        capsys: CaptureFixture[Any],
    ) -> None:
        """Test peaks exactly at tolerance boundaries."""
        molecule = Molecule(
            id="boundary_mol",
            pubchem_cid=11111,
            name="Boundary Molecule",
            retention_time=5.0,
            retention_tolerance=0.2,
            min_signal=100.0,
        )

        # Create peaks: some within tolerance, one outside
        peaks = [
            self.create_peak(
                retention_time=4.85, area=300.0
            ),  # Within tolerance (-0.15)
            self.create_peak(
                retention_time=5.15, area=400.0
            ),  # Within tolerance (+0.15)
            self.create_peak(
                retention_time=4.75, area=200.0
            ),  # Outside tolerance (-0.25)
        ]
        measurement = self.create_measurement("meas_001", peaks, mock_data)
        analyzer = self.create_analyzer([measurement])

        analyzer.molecules.append(molecule)

        # Register peaks
        analyzer._register_peaks(molecule, molecule.retention_tolerance, 254.0)

        # Check that only the peaks within tolerance were considered
        assigned_peaks = [p for p in peaks if p.molecule_id == "boundary_mol"]
        assert (
            len(assigned_peaks) == 1
        )  # Only one should be assigned (closest of the 2 valid ones)

        # The closest of the two valid peaks (4.85 and 5.15) to 5.0 should be 4.85
        assert assigned_peaks[0].retention_time == 4.85

        # Should show multiple peaks warning for the 2 valid peaks
        captured = capsys.readouterr()
        assert "⚠️  Warning: Multiple peaks found within tolerance" in captured.out
        # Check that both retention times appear in the new table format
        assert "4.850" in captured.out and "5.150" in captured.out
        # Tips panel removed - no longer checking for it

    def test_empty_measurements(self, mock_molecule: Molecule) -> None:
        """Test behavior with empty measurements list."""
        analyzer = self.create_analyzer([])
        analyzer.molecules.append(mock_molecule)

        # Should not raise error, but no peaks assigned
        analyzer._register_peaks(
            mock_molecule, mock_molecule.retention_tolerance, 254.0
        )

        # No peaks to check assignments on since no measurements

    def test_chromatogram_with_no_peaks(
        self, mock_molecule: Molecule, mock_data: Data, capsys: CaptureFixture[Any]
    ) -> None:
        """Test behavior with chromatogram containing no peaks."""
        # Create measurement with empty chromatogram
        measurement = Measurement(
            id="empty_meas",
            data=mock_data,
            temperature=25.0,
            temperature_unit="Celsius",
            ph=7.0,
            chromatograms=[
                Chromatogram(type=SignalType.UV, peaks=[], wavelength=254.0)
            ],
        )

        analyzer = self.create_analyzer([measurement])
        analyzer.molecules.append(mock_molecule)

        # Register peaks
        analyzer._register_peaks(
            mock_molecule, mock_molecule.retention_tolerance, 254.0
        )

        # Check warning for no peaks
        captured = capsys.readouterr()
        # With new format, 0 peaks message is not shown when there are warnings
        assert "🎯 Assigned Test Molecule to 0 peaks" not in captured.out
        assert (
            "⚠️  Warning: No peaks found for Test Molecule in 1 measurement(s)"
            in captured.out
        )
        assert "empty_meas" in captured.out  # Should appear in the table
        # Tips panel removed - no longer checking for it
