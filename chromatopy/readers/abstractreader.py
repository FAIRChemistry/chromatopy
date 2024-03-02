from abc import ABC, abstractmethod
from io import StringIO
import os
import pathlib
from typing import Optional
import re

import pandas as pd


class AbstractReader(ABC):

    def __init__(self, path: str):
        self.path = path
        self._is_directory: bool = os.path.isdir(path)

    def _paths(self):
        if self._is_directory:
            return [os.path.join(self.path, f) for f in os.listdir(self.path)]
        else:
            return [self.path]

    @abstractmethod
    def read(self):
        raise NotImplementedError()

    @abstractmethod
    def extract_peaks(self):
        raise NotImplementedError()

    @abstractmethod
    def extract_signal(self):
        raise NotImplementedError()


class CSVReader(AbstractReader):

    def read_csv(self):
        data = pd.read_csv(self.path, header=None)
        return data

    def extract_peaks(self):
        pass

    def extract_signal(self):
        pass


class ChemStationReader(AbstractReader):

    def read(self):
        pass


class ShimadzuReader(AbstractReader):
    re_sections = re.compile(r"\[(.*)\]")

    def _paths(self):
        if self._is_directory:
            return [
                os.path.join(self.path, f)
                for f in os.listdir(self.path)
                if f.endswith(".txt")
            ]
        else:
            return [self.path]

    def read(self):
        """
        Reads the contents of one or multiple files and returns them as a list of strings.

        Returns:
            A list of strings, where each string represents the contents of a file.
        """
        file_contents = []
        for path in self._paths():
            try:
                file_contents.append(
                    pathlib.Path(path).read_text(encoding="ISO-8859-1")
                )
            except IOError as e:
                print(f"Error reading file: {path}")
                raise e

        sections = [self._parse_sections(content) for content in file_contents]

        peak_tables = [self.get_peak_table(section) for section in sections]
        peaks = [self._map_peak_table(table) for table in peak_tables]

        return peaks

    def extract_peaks(self):
        pass

    def extract_signal(self):
        pass

    def _parse_sections(self, file_content: str) -> dict:
        """Parse a Shimadzu ASCII-export file into sections."""

        # Split file into sections using section header pattern
        section_splits = re.split(self.re_sections, file_content)
        if len(section_splits[0]) != 0:
            raise IOError("The file should start with a section header")

        section_names = section_splits[1::2]
        section_contents = [content for content in section_splits[2::2]]

        return dict(zip(section_names, section_contents))

    def parse_meta(self, sections: dict, section_name: str, nrows: int) -> dict:
        """Parse the metadata in a section as keys-values."""
        meta_table = pd.read_table(
            StringIO(sections[section_name]), nrows=nrows, header=None
        )
        meta = {row[0]: row[1] for _, row in meta_table.iterrows()}

        return meta

    def parse_table(
        self, sections: dict, section_name: str, skiprows: int = 1
    ) -> Optional[pd.DataFrame]:
        """Parse the data in a section as a table."""
        table_str = sections[section_name]

        # Count number of non-empty lines
        num_lines = len([le for le in re.split("[\r\n]+", table_str) if len(le)])

        if num_lines <= 1:
            return None

        return pd.read_table(StringIO(table_str), header=1, skiprows=skiprows, sep=",")

    def _map_peak_table(self, table: pd.DataFrame) -> dict:
        retention_time_col = "R.Time"
        height_col = "Height"
        area_col = "Area"
        peak_start_col = "I.Time"
        peak_end_col = "F.Time"

        return table.apply(
            lambda row: {
                "retention_time": row[retention_time_col],
                "retention_time_unit": "min",
                "height": row[height_col],
                "area": row[area_col],
                "width": row[peak_end_col] - row[peak_start_col],
                "width_unit": "min",
            },
            axis=1,
        ).tolist()

    def get_peak_table(
        self, sections: dict, detector: str = "A-Ch1"
    ) -> Optional[pd.DataFrame]:
        section_name = f"Peak Table(Detector {detector})"
        table = self.parse_table(sections, section_name, skiprows=1)

        return table

    def get_compound_table(
        self, sections: dict, detector: str = "A"
    ) -> Optional[pd.DataFrame]:
        section_name = f"Compound Results(Detector {detector})"
        meta = self.parse_meta(sections, section_name, 1)
        table = self.parse_table(sections, section_name, skiprows=1)

        assert (
            table is None or int(meta["# of IDs"]) == table.shape[0]
        ), "Declared number of compounds and table size differ"

        return table

    def get_chromatogram_table(
        self, sections: dict, detector: str = "A", channel: int = 1
    ) -> Optional[pd.DataFrame]:
        section_name = f"LC Chromatogram(Detector {detector}-Ch{channel})"

        meta = self.parse_meta(sections, section_name, 6)
        table = self.parse_table(sections, section_name, skiprows=6)

        # Convert intensity values into what they are supposed to be
        table["Value (mV)"] = table["Intensity"] * float(meta["Intensity Multiplier"])

        assert (
            meta["Intensity Units"] == "mV"
        ), f"Assumed intensity units in mV but got {meta['Intensity Units']}"
        assert (
            int(meta["# of Points"]) == table.shape[0]
        ), "Declared number of points and table size differ"

        return table

    def get_header(self, sections: dict) -> dict:
        return self.parse_meta(sections, "Header", nrows=None)

    def get_file_information(self, sections: dict) -> dict:
        return self.parse_meta(sections, "File Information", nrows=None)

    def get_original_files(self, sections: dict) -> dict:
        return self.parse_meta(sections, "Original Files", nrows=None)

    def get_sample_information(self, sections: dict) -> dict:
        return self.parse_meta(sections, "Sample Information", nrows=None)
