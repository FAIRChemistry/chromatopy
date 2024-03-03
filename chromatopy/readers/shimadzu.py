from typing import Optional
import os
import re
import pathlib
from datetime import datetime
from io import StringIO
import pandas as pd

from chromatopy.readers.abstractreader import AbstractReader


class ShimadzuReader(AbstractReader):
    RE_SECTION = re.compile(r"\[(.*)\]")

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
        return [self.read_file(f) for f in self._paths()]

    def read_file(self, path: str):
        """
        Reads the contents of one or multiple files and returns them as a list of strings.

        Returns:
            A list of strings, where each string represents the contents of a file.
        """
        content = pathlib.Path(path).read_text(encoding="ISO-8859-1")
        sections = self._parse_sections(content)

        measurement_dict = self._map_measurement(sections)
        peak_dict = self.extract_peaks(sections)
        chromatogram_dict = self.extract_signal(sections)
        chromatogram_dict["peaks"] = peak_dict
        measurement_dict["chromatograms"] = [chromatogram_dict]

        return measurement_dict

    def _map_measurement(self, sections: dict) -> dict:
        header = self.get_header(sections)
        timestamp = datetime.strptime(
            f"{header['Output Date'].rstrip('.')} {header['Output Time']}",
            "%d.%m.%Y %H:%M:%S",
        )
        sample_info = self.get_sample_information(sections)
        dilution_factor = sample_info.get("Dilution Factor", 1)
        injection_volume = sample_info.get("Injection Volume", None)
        try:
            injection_volume = float(injection_volume) / float(dilution_factor)
        except TypeError:
            raise ValueError("Injection volume not found in sample information")

        return {
            "timestamp": timestamp,
            "injection_volume": injection_volume,
            "injection_volume_unit": "µL",
            "type": "UV",
        }

    def extract_peaks(self, sections: dict):
        table = self.get_peak_table(sections)
        return self._map_peak_table(table)

    def extract_signal(self, sections) -> dict:
        table = self.get_chromatogram_table(sections)
        return self._map_chromatogram_table(table)

    def _parse_sections(self, file_content: str) -> dict:
        """Parse a Shimadzu ASCII-export file into sections."""

        # Split file into sections using section header pattern
        section_splits = re.split(self.RE_SECTION, file_content)
        if len(section_splits[0]) != 0:
            raise IOError("The file should start with a section header")

        section_names = section_splits[1::2]
        section_contents = [content for content in section_splits[2::2]]

        return dict(zip(section_names, section_contents))

    def parse_meta(self, sections: dict, section_name: str, nrows: int) -> dict:
        """Parse the metadata in a section as keys-values."""

        meta_table = (
            pd.read_table(
                StringIO(sections[section_name]),
                nrows=nrows,
                header=None,
                sep=",",
            )
            .set_index(0)[1]
            .to_dict()
        )

        return meta_table

    def parse_table(
        self, sections: dict, section_name: str, skiprows: int = 1
    ) -> Optional[pd.DataFrame]:
        """Parse the data in a section as a table."""
        table_str = sections[section_name]

        # Count number of non-empty lines
        num_lines = len(table_str.splitlines())

        if num_lines <= 1:
            return None

        return pd.read_table(StringIO(table_str), header=1, skiprows=skiprows, sep=",")

    def _map_peak_table(self, table: pd.DataFrame) -> dict:
        retention_time_col = "R.Time"
        height_col = "Height"
        area_col = "Area"
        peak_start_col = "I.Time"
        peak_end_col = "F.Time"
        tailing_col = "Tailing"
        separation_col = "Sep.Factor"
        peak_start_col = "I.Time"
        peak_end_col = "F.Time"

        return table.apply(
            lambda row: {
                "retention_time": row[retention_time_col],
                "retention_time_unit": "min",
                "peak_start": row[peak_start_col],
                "peak_end": row[peak_end_col],
                "height": row[height_col],
                "area": row[area_col],
                "width": row[peak_end_col] - row[peak_start_col],
                "width_unit": "min",
                "tailing_factor": row[tailing_col],
                "separation_factor": row[separation_col],
            },
            axis=1,
        ).tolist()

    def _map_chromatogram_table(self, table: pd.DataFrame) -> dict:
        """
        Maps the chromatogram table to a dictionary format.

        Args:
            table (pd.DataFrame): The chromatogram table.

        Returns:
            dict: The mapped chromatogram dictionary.
        """
        return {
            "retention_times": table["R.Time (min)"].tolist(),
            "signals": table["Value (mV)"].tolist(),
            "time_unit": "min",
        }

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
        table = self.parse_table(sections, section_name, skiprows=7)

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
