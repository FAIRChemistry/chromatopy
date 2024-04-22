import pathlib
import re
from datetime import datetime
from io import StringIO
from typing import Dict, List, Optional

import pandas as pd

from chromatopy.core import Measurement, SignalType
from chromatopy.core.peak import Peak
from chromatopy.readers.abstractreader import AbstractReader


class ShimadzuReader(AbstractReader):
    SECTION_PATTERN = re.compile(r"\[(.*)\]")

    def __init__(self, path: str):
        super().__init__(path)
        self._detectors: List[str] = []

    def read(self) -> Measurement:
        """Reads the chromatographic data from the specified file.

        Returns:
            Measurement: A Measurement object representing the chromatographic data.
        """
        content = self.open_file(self.path)

        sections = self.create_sections(content)
        self._get_available_detectors(sections)

        info_section = sections.get("File Information")
        acqisition_date = self.get_section_dict(info_section).get("Generated")
        timestamp = datetime.strptime(acqisition_date, "%d.%m.%Y. %H:%M:%S")

        sample_section = sections.get("Sample Information")
        sample_dict = self.get_section_dict(sample_section)
        dilution_factor = sample_dict.get("Dilution Factor", 1)
        injection_volume = sample_dict.get("Injection Volume")

        measurement = Measurement(
            timestamp=timestamp,
            injection_volume=injection_volume,
            dilution_factor=dilution_factor,
            injection_volume_unit="µL",
        )

        for detector in self._detectors:
            for key, section in sections.items():
                if detector not in key:
                    continue

                # Extract peak table
                if "Peak Table" in key:
                    peak_list = self.add_peaks(section)
                    if not peak_list:
                        continue

                    peaks = [Peak(**peak) for peak in peak_list]

                # Extract measurement data
                if "LC Chromatogram" in key:
                    chromatogram_meta = self.get_section_dict(section, nrows=7)
                    chromatogram_df = self.parse_table(section, skiprows=7)

                    measurement.add_to_chromatograms(
                        wavelength=int(chromatogram_meta["Wavelength(nm)"]),
                        type=SignalType.UV,
                        signals=chromatogram_df["Intensity"].tolist(),
                        times=chromatogram_df["R.Time (min)"].tolist(),
                        peaks=peaks,
                    )

        return measurement

    def open_file(self, path: str) -> str:
        return pathlib.Path(path).read_text(encoding="ISO-8859-1")

    def create_sections(self, file_content: str) -> dict:
        """Parse a Shimadzu ASCII-export file into sections."""

        # Split file into sections using section header pattern
        section_splits = re.split(self.SECTION_PATTERN, file_content)
        if len(section_splits[0]) != 0:
            raise IOError("The file should start with a section header")

        section_names = section_splits[1::2]
        section_contents = [content for content in section_splits[2::2]]

        return dict(zip(section_names, section_contents))

    def get_section_dict(self, section: str, nrows: int = None) -> dict:
        """Parse the metadata in a section as keys-values."""

        meta_table = (
            pd.read_table(
                StringIO(section),
                nrows=nrows,
                header=None,
                sep=",",
            )
            .set_index(0)[1]
            .to_dict()
        )

        return meta_table

    def parse_table(self, section: str, skiprows: int = 1) -> Optional[pd.DataFrame]:
        """Parse the data in a section as a table."""

        first_line = section.split("\n")[1]
        num_peaks = int(first_line.split(",")[1])

        if num_peaks < 1:
            return None

        return pd.read_table(StringIO(section), header=1, skiprows=skiprows, sep=",")

    def _map_peak_table(self, table: pd.DataFrame) -> dict:
        try:
            return table.apply(
                lambda row: {
                    "retention_time": row["R.Time"],
                    "retention_time_unit": "min",
                    "peak_start": row["I.Time"],
                    "peak_end": row["F.Time"],
                    "height": row["Height"],
                    "area": row["Area"],
                    "width": row["F.Time"] - row["I.Time"],
                    "width_unit": "min",
                    "tailing_factor": row["Tailing"],
                    "separation_factor": row["Sep.Factor"],
                },
                axis=1,
            ).tolist()
        except KeyError:
            return []

    def add_peaks(self, section: str) -> List[dict]:
        table = self.parse_table(section, skiprows=1)
        peaks = self._map_peak_table(table)

        return peaks

    def _get_available_detectors(self, sections: Dict[str, str]) -> None:
        for key in sections.keys():
            if "LC Chromatogram" in key:
                self._detectors.append(key.split("-")[0].split("(")[1])
