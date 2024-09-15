from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from chromatopy.model import Chromatogram, Measurement, Peak
from chromatopy.readers.abstractreader import AbstractReader


class AgilentCSVReader(AbstractReader):
    def model_post_init(self, __context: Any) -> None:
        if not self.reaction_times or not self.time_unit or not self.file_paths:
            logger.debug(
                "Collecting file paths without reaction time and unit parsing."
            )
            self._get_file_paths()

    def read(self) -> list[Measurement]:
        """Reads chromatographic data from the specified Agilent CSV files.

        Returns:
            list[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        csv_paths = self._get_file_paths()

        assert len(self.reaction_times) == len(csv_paths), f"""
        The number of reaction times {len(self.reaction_times)} does not match the number of
        'RESULTS.CSV' files {len(csv_paths)}.
        """

        measurements = []
        for path_idx, (csv_path, reaction_time) in enumerate(
            zip(csv_paths, self.reaction_times)
        ):
            peaks = self._read_peaks_from_csv(csv_path)
            chromatogram = Chromatogram(peaks=peaks)

            measurements.append(
                Measurement(
                    id=f"m{path_idx}",
                    chromatograms=[chromatogram],
                    reaction_time=reaction_time,
                    time_unit=self.time_unit,
                    temperature=self.temperature,
                    temperature_unit=self.temperature_unit,
                    ph=self.ph,
                )
            )

        if not self.silent:
            self.print_success(len(measurements))

        return measurements

    def _get_file_paths(self) -> list[str]:
        """Collects the file paths of the Agilent CSV files."""
        directory = Path(self.dirpath)
        target_paths = []

        if directory.is_dir():
            dirs = sorted(directory.iterdir())
            found_count = 0

            for folder in dirs:
                if (
                    folder.is_dir()
                    and folder.name.endswith(".D")
                    and not folder.name.startswith(".")
                ):
                    for file in folder.iterdir():
                        if file.name == "RESULTS.CSV" and not file.name.startswith("."):
                            found_count += 1
                            target_paths.append(str(file.absolute()))

            if found_count == 0:
                raise FileNotFoundError(
                    f"No 'RESULTS.CSV' file found in '{self.dirpath}'."
                )
        else:
            target_paths = [self.dirpath]

        return sorted(target_paths)

    def _read_peaks_from_csv(self, path: str, skiprows: int = 6) -> list[Peak]:
        """Reads peaks from an Agilent CSV file."""
        peaks = []
        df = pd.read_csv(path, skiprows=skiprows)
        records = df.to_dict(orient="records")

        for record in records:
            peaks.append(
                Peak(
                    retention_time=record["R.T."],
                    area=record["Area"],
                    amplitude=record["Height"],
                    percent_area=record["Pct Total"],
                )
            )

        return peaks
