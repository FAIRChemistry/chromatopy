from unittest.mock import MagicMock, patch

import pytest

from chromatopy.readers.abstractreader import AbstractReader
from chromatopy.units import minute


class TestAbstractReader(AbstractReader):
    def read(self):
        pass


@pytest.fixture
def mock_path():
    with patch("chromatopy.readers.abstractreader.Path") as mock_path:
        yield mock_path


@pytest.fixture
def mock_inconsistent_units(mock_path):
    with patch("chromatopy.readers.abstractreader.Path") as mock_path:
        yield mock_path


def test_parse_time_and_unit_success(mock_path):
    mock_path_instance = mock_path.return_value
    mock_path_instance.exists.return_value = True
    mock_path_instance.is_dir.return_value = True
    mock_path_instance.iterdir.return_value = [
        MagicMock(name="10 min"),
        MagicMock(name="20 min"),
        MagicMock(name="30 min"),
    ]

    reader = TestAbstractReader(
        dirpath="dummy_path",
        reaction_times=[],
        time_unit=minute,
        ph=7.0,
        temperature=25.0,
        temperature_unit=minute,
    )

    times, unit = reader._parse_time_and_unit()
    assert times == [10.0, 20.0, 30.0]
    assert unit == minute


def test_parse_time_and_unit_file_not_found(mock_path):
    mock_path_instance = mock_path.return_value
    mock_path_instance.exists.return_value = False

    reader = TestAbstractReader(
        dirpath="dummy_path",
        reaction_times=[],
        time_unit=minute,
        ph=7.0,
        temperature=25.0,
        temperature_unit=minute,
    )

    with pytest.raises(FileNotFoundError):
        reader._parse_time_and_unit()


def test_parse_time_and_unit_not_a_directory(mock_path):
    mock_path_instance = mock_path.return_value
    mock_path_instance.exists.return_value = True
    mock_path_instance.is_dir.return_value = False

    reader = TestAbstractReader(
        dirpath="dummy_path",
        reaction_times=[],
        time_unit=minute,
        ph=7.0,
        temperature=25.0,
        temperature_unit=minute,
    )

    with pytest.raises(NotADirectoryError):
        reader._parse_time_and_unit()


def test_parse_time_and_unit_inconsistent_units(mock_path):
    mock_path_instance = mock_path.return_value
    mock_path_instance.exists.return_value = True
    mock_path_instance.is_dir.return_value = True
    mock_path_instance.iterdir.return_value = [
        MagicMock(name="10 min"),
        MagicMock(name="20 sec"),
    ]

    reader = TestAbstractReader(
        dirpath="dummy_path",
        reaction_times=[],
        time_unit=minute,
        ph=7.0,
        temperature=25.0,
        temperature_unit=minute,
    )

    with pytest.raises(
        ValueError,
        match="Units of reaction times in directory 'dummy_path' are not consistent",
    ):
        reader._parse_time_and_unit()


def test_parse_time_and_unit_unrecognized_unit(mock_path):
    mock_path_instance = mock_path.return_value
    mock_path_instance.exists.return_value = True
    mock_path_instance.is_dir.return_value = True
    mock_path_instance.iterdir.return_value = [
        MagicMock(name="10 xyz"),
    ]

    reader = TestAbstractReader(
        dirpath="dummy_path",
        reaction_times=[],
        time_unit=minute,
        ph=7.0,
        temperature=25.0,
        temperature_unit=minute,
    )

    with pytest.raises(
        ValueError, match="Unit xyz from directory 'dummy_path' not recognized"
    ):
        reader._parse_time_and_unit()


def test_parse_time_and_unit_non_unique_times(mock_path):
    mock_path_instance = mock_path.return_value
    mock_path_instance.exists.return_value = True
    mock_path_instance.is_dir.return_value = True
    mock_path_instance.iterdir.return_value = [
        MagicMock(name="10 min"),
        MagicMock(name="10 min"),
    ]

    reader = TestAbstractReader(
        dirpath="dummy_path",
        reaction_times=[],
        time_unit=minute,
        ph=7.0,
        temperature=25.0,
        temperature_unit=minute,
    )

    with pytest.raises(
        ValueError, match="Reaction times in directory 'dummy_path' are not unique"
    ):
        reader._parse_time_and_unit()
