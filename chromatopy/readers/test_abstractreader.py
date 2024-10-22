import pytest

from chromatopy.readers.abstractreader import (
    AbstractReader,
    DataType,
    FileNotFoundInDirectoryError,
    UnitConsistencyError,
    UnitDefinition,
)


def test_abstract_reader_initialization():
    reader = AbstractReader(
        dirpath="/path/to/data",
        mode=DataType.TIMECOURSE,
        values=[1.0, 2.0, 3.0],
        unit=UnitDefinition("minute"),
        ph=7.0,
        temperature=25.0,
        temperature_unit=UnitDefinition("Celsius"),
        silent=True,
        file_paths=["file1.txt", "file2.txt", "file3.txt"],
    )
    assert reader.dirpath == "/path/to/data"
    assert reader.mode == DataType.TIMECOURSE
    assert reader.values == [1.0, 2.0, 3.0]
    assert reader.unit == UnitDefinition("minute")
    assert reader.ph == 7.0
    assert reader.temperature == 25.0
    assert reader.temperature_unit == UnitDefinition("Celsius")
    assert reader.silent is True
    assert reader.file_paths == ["file1.txt", "file2.txt", "file3.txt"]


def test_infer_fields_based_on_mode_timecourse():
    data = {
        "dirpath": "/path/to/data",
        "mode": DataType.TIMECOURSE,
        "file_paths": ["file1_1min.txt", "file2_2min.txt"],
    }
    result = AbstractReader.infer_fields_based_on_mode(data)
    assert result["values"] == [1.0, 2.0]
    assert result["unit"] == UnitDefinition("minute")


def test_infer_fields_based_on_mode_calibration():
    data = {
        "dirpath": "/path/to/data",
        "mode": DataType.CALIBRATION,
        "file_paths": ["file1_1mM.txt", "file2_2mM.txt"],
    }
    result = AbstractReader.infer_fields_based_on_mode(data)
    assert result["values"] == [1.0, 2.0]
    assert result["unit"] == UnitDefinition("mM")


def test_validate_data_consistency_timecourse():
    reader = AbstractReader(
        dirpath="/path/to/data",
        mode=DataType.TIMECOURSE,
        values=[1.0, 2.0],
        unit=UnitDefinition("minute"),
        ph=7.0,
        temperature=25.0,
        temperature_unit=UnitDefinition("Celsius"),
        silent=True,
        file_paths=["file1.txt", "file2.txt"],
    )
    validated_reader = reader.validate_data_consistency()
    assert validated_reader is reader


def test_validate_data_consistency_calibration():
    reader = AbstractReader(
        dirpath="/path/to/data",
        mode=DataType.CALIBRATION,
        values=[1.0, 2.0],
        unit=UnitDefinition("mM"),
        ph=7.0,
        temperature=25.0,
        temperature_unit=UnitDefinition("Celsius"),
        silent=True,
        file_paths=["file1.txt", "file2.txt"],
    )
    validated_reader = reader.validate_data_consistency()
    assert validated_reader is reader


def test_missing_files_error():
    with pytest.raises(FileNotFoundInDirectoryError):
        reader = AbstractReader(
            dirpath="/path/to/data",
            mode=DataType.TIMECOURSE,
            values=[1.0, 2.0],
            unit=UnitDefinition("minute"),
            ph=7.0,
            temperature=25.0,
            temperature_unit=UnitDefinition("Celsius"),
            silent=True,
            file_paths=[],
        )
        reader.validate_data_consistency()


def test_inconsistent_units_error():
    data = {
        "dirpath": "/path/to/data",
        "mode": DataType.TIMECOURSE,
        "file_paths": ["file1_1min.txt", "file2_2sec.txt"],
    }
    with pytest.raises(UnitConsistencyError):
        AbstractReader.infer_fields_based_on_mode(data)


def test_invalid_mode_error():
    with pytest.raises(ValueError):
        AbstractReader(
            dirpath="/path/to/data",
            mode="invalid_mode",
            values=[1.0, 2.0],
            unit=UnitDefinition("minute"),
            ph=7.0,
            temperature=25.0,
            temperature_unit=UnitDefinition("Celsius"),
            silent=True,
            file_paths=["file1.txt", "file2.txt"],
        )
