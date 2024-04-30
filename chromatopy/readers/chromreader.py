from pathlib import Path
from typing import List

from chromatopy.readers.factory import ChromReaderFactory

from ..core import Measurement


class ChromReader:
    @staticmethod
    def read(posix_path: str) -> List[Measurement]:
        """Reads the chromatographic data from the specified file or directory.

        Args:
            path (str): The path to the file or directory containing the chromatographic data.

        Raises:
            FileNotFoundError: If the specified file or directory does not exist.

        Returns:
            List[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        posix_path = Path(posix_path)

        if posix_path.is_dir():
            return ChromReader.read_directory(posix_path)
        elif posix_path.is_file():
            return [ChromReader.read_file(posix_path)]
        else:
            raise FileNotFoundError(f"Could not find file or directory: {posix_path}")

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
    def read_directory(dir_path: Path) -> List[Measurement]:
        """Reads the chromatographic data from the specified directory.

        Args:
            dir_path (str): Path to the directory containing the chromatographic data.

        Returns:
            List[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        if dir_path.is_file():
            return [
                ChromReaderFactory.create_reader(file_path).read()
                for file_path in sorted(dir_path).iterdir()
            ]
        elif dir_path.is_dir():
            return [
                ChromReaderFactory.create_reader(file_path).read()
                for file_path in sorted(dir_path.iterdir())
            ]
