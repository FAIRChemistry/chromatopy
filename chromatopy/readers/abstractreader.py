import re
from abc import abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, model_validator

from chromatopy.model import Measurement, UnitDefinition


class MetadataExtractionError(Exception):
    def __init__(self, message, suggestion=None):
        if suggestion:
            message += f"\n{str(suggestion)}"
        super().__init__(message)


class UnitConsistencyError(Exception):
    def __init__(self, message, suggestion=None):
        if suggestion:
            message += f"\n{str(suggestion)}"
        super().__init__(message)


class FileNotFoundInDirectoryError(Exception):
    def __init__(self, message, suggestion=None):
        if suggestion:
            message += f"\n{str(suggestion)}"
        super().__init__(message)


class AbstractReader(BaseModel):
    """Abstract class for reading chromatographic data from files."""

    dirpath: str
    reaction_times: list[float]
    time_unit: UnitDefinition
    ph: float
    temperature: float
    temperature_unit: UnitDefinition
    silent: bool

    file_paths: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def try_parse_time_and_unit_from_paths(cls, data: Any):
        """Go through the data and try to parse the reaction times and unit from the paths."""
        if not data.get("reaction_times"):
            try:
                cls._parse_time_and_unit(data)
            except MetadataExtractionError as e:
                logger.debug(e)
                raise MetadataExtractionError(
                    str(e),
                    suggestion="Alternatively, provide the reaction times and unit manually.",
                )
            except UnitConsistencyError as e:
                logger.debug(e)
                raise UnitConsistencyError(
                    str(e),
                )
        return data

    @model_validator(mode="after")
    def validate_data_consistency(self):
        """Validate the data consistency."""
        if not self.file_paths:
            raise FileNotFoundInDirectoryError(
                f"No files found in the directory {self.dirpath}."
            )
        if not self.reaction_times:
            raise ValueError("No reaction times provided.")
        if not self.time_unit:
            raise ValueError("No time unit provided.")
        if len(self.file_paths) != len(self.reaction_times):
            raise ValueError(
                f"Number of files in {self.dirpath} ({len(self.file_paths)}) does not match the number of reaction times ({len(self.reaction_times)})."
            )

        return self

    @classmethod
    def _parse_time_and_unit(
        cls,
        data: dict[str, Any],
    ) -> None:
        """Check if reaction time and unit can be parsed from filenames in the directory."""

        try:
            filenames = [Path(f) for f in data["file_paths"]]
            if len(filenames) == 0:
                raise KeyError
        except KeyError:
            path = Path(data["dirpath"])
            if not path.exists():
                raise FileNotFoundError(
                    f"Directory '{data['dirpath']}' does not exist."
                )
            if not path.is_dir():
                raise NotADirectoryError(f"'{data['dirpath']}' is not a directory.")

            # get all filnames of normal files in the directory. exclude hidden files

            filenames = [f for f in path.iterdir() if not f.name.startswith(".")]

        pattern = r".*?(\d+(\.\d+)?)\s*[_-]?\s*(min|minutes?|sec|seconds?|hours?)"

        # extract all reaction times and units from the filenames or parent directories
        rctn_time_path_dict: dict[float, str] = {}
        units = []

        for file in filenames:
            match = re.search(pattern, file.name)
            if not match:
                match = re.search(pattern, file.parent.name)
            if match:
                reaction_time = float(match.group(1))
                unit = match.group(3)
                if reaction_time in rctn_time_path_dict:
                    logger.debug(
                        f"Duplicate reaction time '{reaction_time}' found in directory '{data['dirpath']}'."
                    )
                    raise MetadataExtractionError(
                        f"Reaction times in directory '{data['dirpath']}' are not unique."
                    )
                rctn_time_path_dict[reaction_time] = str(file.absolute())
                units.append(unit)
            else:
                logger.debug(f"Could not parse reaction time from '{file}'.")
                raise MetadataExtractionError(
                    f"Could not parse reaction time from '{file}'."
                )

        # check if all units are the same
        if not all(unit == units[0] for unit in units):
            logger.debug(
                f"Units of reaction times in directory '{data['dirpath']}' are not consistent: {units}"
            )
            raise UnitConsistencyError(
                f"Units of reaction times in directory '{data['dirpath']}' are not consistent: {units}"
            )

        try:
            unit_definition = AbstractReader._map_unit_str_to_UnitDefinition(units[0])
        except ValueError:
            logger.debug(
                f"Unit {units[0]} from directory '{data['dirpath']}' not recognized."
            )
            raise MetadataExtractionError(
                f"Unit {units[0]} from directory '{data['dirpath']}' not recognized."
            )

        data["file_paths"] = []
        data["reaction_times"] = []
        for time, full_path in sorted(rctn_time_path_dict.items()):
            data["reaction_times"].append(time)
            data["file_paths"].append(full_path)
        data["time_unit"] = unit_definition

    @staticmethod
    def _map_unit_str_to_UnitDefinition(
        unit_str: str,
    ) -> UnitDefinition:
        """Maps a string representation of a unit to a `UnitDefinition` object.

        Parameters:
            unit_str (str): The string representation of the unit.

        Returns:
            UnitDefinition: The `UnitDefinition` object.

        Raises:
            ValueError: If the unit string is not recognized.
        """

        from chromatopy.units import hour, minute, second

        unit_str = unit_str.lower()
        match unit_str:
            case "min" | "mins" | "minutes":
                return minute
            case "sec" | "secs" | "seconds":
                return second
            case "hour" | "hours":
                return hour
            case _:
                raise ValueError(f"Unit '{unit_str}' not recognized.")

    @abstractmethod
    def read(self) -> list[Measurement]:
        """Abstract method that must be implemented by subclasses."""
        pass

    def print_success(self, n_measurement_objects: int) -> None:
        """Prints a success message."""
        print(f"✅ Loaded {n_measurement_objects} chromatograms.")
