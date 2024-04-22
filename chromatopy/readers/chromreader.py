from pathlib import Path
from typing import List

from chromatopy.readers.factory import ChromReaderFactory

from ..core import Measurement


class ChromReader:
    @staticmethod
    def read(path: str) -> List[Measurement]:
        """Reads the chromatographic data from the specified file or directory.

        Args:
            path (str): The path to the file or directory containing the chromatographic data.

        Raises:
            FileNotFoundError: If the specified file or directory does not exist.

        Returns:
            List[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        path = Path(path)

        if path.is_dir():
            return ChromReader.read_directory(path)
        elif path.is_file():
            return [ChromReader.read_file(path)]
        else:
            raise FileNotFoundError(f"Could not find file or directory: {path}")

    @staticmethod
    def read_file(file_path: str) -> Measurement:
        """Reads the chromatographic data from the specified file.

        Args:
            file_path (str): Path to the file containing the chromatographic data.

        Returns:
            Measurement: A Measurement object representing the chromatographic data.
        """
        return ChromReaderFactory.create_reader(file_path).read()

    @staticmethod
    def read_directory(dir_path: str) -> List[Measurement]:
        """Reads the chromatographic data from the specified directory.

        Args:
            dir_path (str): Path to the directory containing the chromatographic data.

        Returns:
            List[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        return [
            ChromReaderFactory.create_reader(file_path).read()
            for file_path in sorted(Path(dir_path).iterdir())
        ]
