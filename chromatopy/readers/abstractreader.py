import re
from abc import abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, model_validator

from chromatopy.model import Measurement, UnitDefinition


class ReactionTimeUnitError(Exception):
    def __init__(self, message, suggestion=None):
        if suggestion:
            message += f"\n{str(suggestion)}"
        super().__init__(message)


class UnitConsistencyError(Exception):
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

    file_paths: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def try_parse_time_and_unit_from_paths(cls, data: Any):
        """Go through the data and try to parse the reaction times and unit from the paths."""
        if not data.get("reaction_times"):
            try:
                cls._parse_time_and_unit(data)
            except ReactionTimeUnitError as e:
                logger.debug(e)
                raise ReactionTimeUnitError(
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
            raise ValueError(f"No files in found in the directory {self.dirpath}.")
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

        path = Path(data["dirpath"])
        if not path.exists():
            raise FileNotFoundError(f"Directory '{data['dirpath']}' does not exist.")
        if not path.is_dir():
            raise NotADirectoryError(f"'{data['dirpath']}' is not a directory.")

        # get all filnames of normal files in the directory. exclude hidden files
        pattern = r"(\d+(\.\d+)?)\s?(min|minutes?|sec|seconds?|hours?)"

        filenames = [
            f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")
        ]

        # check if all filenames contain a reaction time and unit
        if all(re.search(pattern, f.name) for f in filenames):
            # extract all reaction times and units from the filenames
            rctn_time_path_dict: dict[float, str] = {}
            units = []

            for file in filenames:
                match = re.search(pattern, file.name)
                assert (
                    match is not None
                ), f"Could not parse reaction time from '{file.name}'."
                reaction_time = float(match.group(1))
                units.append(match.group(3))
                rctn_time_path_dict[reaction_time] = str(file.absolute())

            if not len(list(rctn_time_path_dict.keys())) == len(filenames):
                logger.debug(
                    f"Reaction times in directory '{data['dirpath']}' are not unique."
                )
                raise ReactionTimeUnitError(
                    f"Reaction times in directory '{data['dirpath']}' are not unique."
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
                unit_definition = AbstractReader._map_unit_str_to_UnitDefinition(
                    units[0]
                )
            except ValueError:
                logger.debug(
                    f"Unit {units[0]} from directory '{data['dirpath']}' not recognized."
                )
                raise ReactionTimeUnitError(
                    f"Unit {units[0]} from directory '{data['dirpath']}' not recognized."
                )

            data["file_paths"] = []
            data["reaction_times"] = []
            for time, full_path in sorted(rctn_time_path_dict.items()):
                data["reaction_times"].append(time)
                data["file_paths"].append(full_path)
            data["time_unit"] = unit_definition

        else:
            logger.debug(
                f"Reaction times and units could not be parsed from filenames in directory '{data['dirpath']}'."
            )
            raise ReactionTimeUnitError(
                f"Reaction times and units could not be parsed from filenames in directory '{data['dirpath']}'."
            )

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
            case "min" | "minutes":
                return minute
            case "sec" | "seconds":
                return second
            case "hour" | "hours":
                return hour
            case _:
                raise ValueError(f"Unit '{unit_str}' not recognized.")

    @abstractmethod
    def read(self) -> list[Measurement]:
        """Abstract method that must be implemented by subclasses."""
        pass


# Then, instantiate the ConcreteReader instead of AbstractReader
if __name__ == "__main__":
    from chromatopy.units.predefined import C

    other = "/Users/max/Documents/GitHub/chromatopy/tests/test_readers/data/test_dir_correct_file_names"
    orig = "/Users/max/Documents/GitHub/chromatopy/docs/examples/data/asm"
    wrong = "/Users/max/Documents/GitHub/chromatopy/tests/test_readers/data/test_dir_wrong_units"

    class ConcreteReader(AbstractReader):
        def read(self) -> list[Measurement]:
            # Implement the reading logic here
            # This is just a placeholder implementation
            return []

    reader = ConcreteReader(
        dirpath=orig,
        reaction_times=[],
        ph=7.0,
        time_unit=None,
        temperature=25.0,
        temperature_unit=C,
    )

    print(reader.reaction_times)
    print(reader.file_paths)
    print(reader.time_unit.base_units)
