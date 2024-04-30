from abc import ABC, abstractmethod

from chromatopy.core.measurement import Measurement


class AbstractReader(ABC):
    """
    AbstractReader is an abstract base class that defines the
    interface for reading and processing data from a file containing
    measurement data from a single chromatographic experiment.
    Each abstract reader class must implement the read method, returning
    a `Measurement` object.

    Attributes:
        path (str): The path to the measurement file.
    """

    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def read(self) -> Measurement:
        pass
