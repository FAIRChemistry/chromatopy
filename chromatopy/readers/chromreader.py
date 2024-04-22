import os
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
            e: _description_

        Returns:
            List[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        try:
            if os.path.isdir(path):
                return ChromReader.read_directory(path)
            else:
                return [ChromReader.read_file(path)]

        except Exception as e:
            raise e

    @staticmethod
    def read_file(self, file_path: str) -> Measurement:
        """Reads the chromatographic data from the specified file.

        Args:
            file_path (str): Path to the file containing the chromatographic data.

        Returns:
            Measurement: A Measurement object representing the chromatographic data.
        """
        return ChromReaderFactory.create_reader(file_path).read()

    @staticmethod
    def read_directory(self, dir_path: str) -> List[Measurement]:
        """Reads the chromatographic data from the specified directory.

        Args:
            dir_path (str): Path to the directory containing the chromatographic data.

        Returns:
            List[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        return [
            ChromReaderFactory.create_reader(file_path).read()
            for file_path in os.listdir(dir_path)
        ]
