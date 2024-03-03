from abc import ABC, abstractmethod
import os


class AbstractReader(ABC):
    """
    AbstractReader is an abstract base class that defines the interface for reading and processing
    data from a file or directory.

    Attributes:
        path (str): The path to the file or directory.
        _is_directory (bool): Indicates whether the path is a directory or not.

    Methods:
        __init__(self, path: str): Initializes the AbstractReader object with the specified path.
        _validate_path(self): Validates the path to ensure it exists and is either a file or directory.
        _paths(self): Returns a list of paths to be processed based on the type of the input path.
        read(self): Abstract method to read the data from the file or directory.
        read_file(self): Abstract method to read the data from a single file.
        extract_peaks(self): Abstract method to extract peaks from the data.
        extract_signal(self): Abstract method to extract the signal from the data.
    """

    def __init__(self, path: str):
        self.path = path
        self._is_directory: bool = os.path.isdir(path)
        self._validate_path()

    def _validate_path(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Path '{self.path}' does not exist.")
        if self._is_directory and not os.path.isdir(self.path):
            raise NotADirectoryError(f"Path '{self.path}' is not a directory.")
        if not self._is_directory and not os.path.isfile(self.path):
            raise FileNotFoundError(f"Path '{self.path}' is not a file.")

    def _paths(self):
        if self._is_directory:
            return [os.path.join(self.path, f) for f in os.listdir(self.path)]
        else:
            return [self.path]

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def read_file(self):
        pass

    @abstractmethod
    def extract_peaks(self):
        pass

    @abstractmethod
    def extract_signal(self):
        pass
