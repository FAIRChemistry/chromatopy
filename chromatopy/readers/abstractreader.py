from abc import ABC, abstractmethod
from io import StringIO
from typing import TextIO, Optional
import re

import pandas as pd


class AbstractReader(ABC):

    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def read_directory(self):
        pass

    @abstractmethod
    def extract_peaks(self):
        pass

    @abstractmethod
    def extract_signal(self):
        pass


class CSVReader(AbstractReader):

    def read_csv(self):
        data = pd.read_csv(self.path, header=None)
        return data

    def read_directory(self, path: str):
        pass

    def extract_peaks(self):
        pass

    def extract_signal(self):
        pass


class ChemStationReader(AbstractReader):

    def read(self):
        pass


class ShimadzuReader(AbstractReader):
    re_sections = re.compile(r"\[(.*)\]")

    def read(self):
        pass

    def read_directory(self, path: str):
        pass

    def parse_sections(self) -> dict:
        """Parse a Shimadzu ASCII-export file into sections."""
        with open(self.path, "r", encoding="ISO-8859-1") as f:
            fulltext = f.read()

        # Split file into sections using section header pattern
        split = self.re_sections.split(fulltext)
        assert len(split[0]) == 0, "the file should start with a section header"

        section_names = [split[i] for i in range(1, len(split), 2)]
        section_contents = [split[i] for i in range(2, len(split), 2)]

        sections = {
            name: content for name, content in zip(section_names, section_contents)
        }
        return sections

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
        num_lines = len([l for l in re.split("[\r\n]+", table_str) if len(l)])

        if num_lines <= 1:
            return None

        return pd.read_table(StringIO(table_str), header=1, skiprows=skiprows)

    def get_peak_table(
        self, sections: dict, detector: str = "A"
    ) -> Optional[pd.DataFrame]:
        section_name = f"Peak Table(Detector {detector})"
        meta = self.parse_meta(sections, section_name, 1)
        table = self.parse_table(sections, section_name, skiprows=1)

        assert (
            table is None or int(meta["# of Peaks"]) == table.shape[0]
        ), "Declared number of peaks and table size differ"

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
