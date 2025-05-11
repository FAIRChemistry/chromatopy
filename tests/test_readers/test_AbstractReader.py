import os

import pytest

from chromatopy.readers.abstractreader import AbstractReader, UnitConsistencyError


class TestAbstractReader(AbstractReader):
    def read(self):
        pass


@pytest.fixture
def working_data_dir() -> str:
    # Path to the test data directory
    path = "tests/test_readers/data/test_dir_correct_file_names"

    return path


@pytest.fixture
def inconsistent_units_dir() -> str:
    # Path to the test data directory
    path = "tests/test_readers/data/test_inconsistent_units"

    return path


def test_parse_time_and_unit_success(working_data_dir: str) -> None:
    reader = TestAbstractReader(
        dirpath=working_data_dir,
        ph=7.0,
        temperature=25.0,
        temperature_unit="C",
        silent=False,
        mode="timecourse",
    )

    # Extract only the filenames
    file_names = [os.path.basename(file) for file in reader.file_paths]

    assert reader.values == [0.0, 0.33, 3.4, 10]
    assert reader.unit.name == "min"
    assert reader.unit.base_units[0].multiplier == 60
    assert reader.mode == "timecourse"
    assert file_names == [
        "0min.json",
        "m3 0.33 min.txt",
        "a34h2_3.4min.txt",
        "10 min.json",
    ]


def test_parse_time_and_unit_inconsistent_units(inconsistent_units_dir: str) -> None:
    with pytest.raises(
        UnitConsistencyError,
    ):
        TestAbstractReader(
            dirpath=inconsistent_units_dir,
            values=None,
            unit=None,
            ph=7.0,
            temperature=25.0,
            temperature_unit="C",
            mode="timecourse",
        )
