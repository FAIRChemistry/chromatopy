import pathlib
import re
from datetime import datetime
from io import StringIO
from typing import Dict, List

import pandas as pd

from chromatopy.core import Measurement, Peak, SignalType
from chromatopy.readers.abstractreader import AbstractReader


class ShimadzuReader(AbstractReader):
    SECTION_PATTERN = re.compile(r"\[(.*)\]")

    def __init__(self, path: str):
        super().__init__(path)
        self._detector_id: str = None
        self._channel_ids: List[str] = None

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
            id=str(self.path),
            timestamp=timestamp,
            injection_volume=injection_volume,
            dilution_factor=dilution_factor,
            injection_volume_unit="µL",
        )

        for channel_id in self._channel_ids:
            for section_key, section in sections.items():
                if channel_id not in section_key:
                    continue

                section = section.strip()

                # Extract peak table
                if "Peak Table" in section_key:
                    peak_list = self.add_peaks(section)
                    if not peak_list:
                        continue

                    peaks = [Peak(**peak) for peak in peak_list]
                    # add timestamp from measurement to peaks
                    for peak in peaks:
                        peak.timestamp = timestamp

                # Extract measurement data
                if "Chromatogram" in section_key:
                    meta_section, section = re.split(r"(?=R\.Time)", section)

                    chromatogram_meta = self.get_section_dict(meta_section)

                    chromatogram_df = self.parse_chromatogram(section)

                    measurement.add_to_chromatograms(
                        wavelength=int(chromatogram_meta["Wavelength(nm)"]),
                        type=SignalType.UV,
                        signals=chromatogram_df["Intensity"].tolist(),
                        times=chromatogram_df["R.Time (min)"].tolist(),
                        peaks=peaks,
                    )

        return measurement

    def parse_chromatogram(self, table_string: str) -> pd.DataFrame:
        """Parse the data in a section as a table."""

        lines = table_string.split("\n")
        header = lines[0]
        data = lines[1:]

        if not header.count(",") == data[0].count(","):
            data = "\n".join(data)
            pattern = r"(\b\d+),(\d+\b)"
            data = re.sub(pattern, r"\1.\2", data)
        else:
            data = "\n".join(data)

        table = pd.read_csv(StringIO(header + "\n" + data), sep=",", header=0)

        return table

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

        try:
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

        except pd.errors.ParserError:
            pattern = r"(\b\d+),(\d+\b)"
            section = re.sub(pattern, r"\1.\2", section)

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

    def preprocess_decimal_delimiters(self, data_str):
        pattern = r"(\d),(\d{3}\b)"

        return re.sub(pattern, r"\1.\2", data_str)

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
        except KeyError as e:
            raise e
            return []

    def add_peaks(self, section: str) -> List[dict]:
        try:
            meta, section = re.split(r"(?=Peak#)", section)
        except ValueError:
            return []  # No peaks in the section

        data_lines = section.split("\n")
        header = data_lines[0]
        data = data_lines[1:]
        seperators_header = header.count(",")
        seperators_data = data[0].count(",")
        if seperators_header != seperators_data:
            data = "\n".join(data)
            data = self.preprocess_decimal_delimiters(data)
        else:
            data = "\n".join(data)

        section = header + "\n" + data
        table = pd.read_csv(StringIO(section), sep=",", header=0)
        peaks = self._map_peak_table(table)

        return peaks

    def _get_available_detectors(self, sections: Dict[str, str]) -> None:
        detector_info = self.get_section_dict(sections.get("Configuration"))
        detector_id = detector_info.get("Detector ID")
        n_channels = int(detector_info.get("# of Channels"))
        channel_ids = [f"Ch{i}" for i in range(1, n_channels + 1)]

        self._detector_id = detector_id
        self._channel_ids = channel_ids


if __name__ == "__main__":
    path_new = "/Users/max/Documents/GitHub/shimadzu-example/data/sah/sah konst soph 1.78 mM 5-5.txt"

    path_old = (
        "/Users/max/Documents/GitHub/shimadzu-example/data/calibration/bazdarac 0.7.txt"
    )
    reader_old = ShimadzuReader(path_new).read()
    print(reader_old)

    reader_new = ShimadzuReader(path_old).read()
    print(reader_new)
