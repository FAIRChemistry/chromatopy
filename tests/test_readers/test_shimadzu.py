import unittest

import pytest

from chromatopy.core.measurement import Measurement
from chromatopy.readers.shimadzu import ShimadzuReader

DIR_PATH = "data/shimadzu/"
FILE_PATH = "tests/test_readers/data/shimadzu/Output-sample 0.txt"


@pytest.mark.readers
class TestShimadzuReader(unittest.TestCase):
    # can read a single file and return a dictionary
    def test_read_single_file(self):
        reader = ShimadzuReader(FILE_PATH)

        result = reader.read()

        assert isinstance(result[0], Measurement)

    # raises FileNotFoundError when path does not exist
    def test_file_not_found_error(self):
        # Arrange
        path = "nonexistent/path/to/file.txt"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ShimadzuReader(path)

    def test_map_measurement(self):
        # Arrange
        reader = ShimadzuReader(FILE_PATH)
        content = reader.open_file(FILE_PATH)
        sections = reader.create_sections(content)

        # Act
        result = reader.get_measurement_conditions(sections)

        # Assert
        assert isinstance(result, dict)
        assert result["timestamp"].isoformat() == "2023-12-12T11:15:12"
        assert result["injection_volume"] == 20
        assert result["injection_volume_unit"] == "µL"
