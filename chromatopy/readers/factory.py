from .abstractreader import AbstractReader


class ChromReaderFactory:
    @staticmethod
    def create_reader(path: str) -> AbstractReader:
        """Creates a reader object based on the signature of the file.

        Args:
            path (str): The path to the file.

        Raises:
            ValueError: If the signature of the file is not matched to
            any supported format.

        Returns:
            AbstractReader: A reader object for the specified file.
        """
        if ChromReaderFactory.get_file_signature(path) == "shimadzu":
            from .shimadzu import ShimadzuReader

            return ShimadzuReader()
        else:
            raise ValueError(f"Unsupported file format: {path}")

    @staticmethod
    def get_file_signature(path: str) -> str:
        """Returns the signature of the file based on the first few lines.

        Args:
            path (str): The path to the file.

        Returns:
            str: The signature of the file.

        """
        signatures = {"shimadzu": "[Header]"}

        with open(path, "r") as file:
            lines = [file.readline() for _ in range(5)]

            for key, signature in signatures.items():
                if any(signature in line for line in lines):
                    return key
