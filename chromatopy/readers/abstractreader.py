from abc import ABC, abstractmethod

from chromatopy.model import Measurement, UnitDefinition


class AbstractReader(ABC):
    """
    AbstractReader is an abstract base class that defines the
    interface for reading and processing data from files containing
    measurement data from a single chromatographic experiment.
    Each subclass must implement the read method, returning
    a `Measurement` object.

    Attributes:
        dirpath (str): The path to the measurement directory.
        reaction_times (list[float]): The list of reaction times.
        time_unit (UnitDefinition): The unit of time used in the measurements.
        _file_paths (list[str]): A list of file paths specific to each instance.
    """

    def __init__(
        self, dirpath: str, reaction_times: list[float], time_unit: UnitDefinition
    ):
        self.dirpath = dirpath
        self.reaction_times = reaction_times
        self.time_unit = time_unit
        self._file_paths: list[str] = []

    @abstractmethod
    def read(self) -> list[Measurement]:
        """Abstract method that must be implemented by subclasses."""
        pass
