import pandas as pd

from chromatopy.model import Chromatogram, Measurement, Peak
from chromatopy.readers.abstractreader import AbstractReader


class AgilentCSVReader(AbstractReader):
    def read(self) -> list[Measurement]:
        """Reads chromatographic data from the specified Agilent CSV files.

        Returns:
            list[Measurement]: A list of Measurement objects representing the chromatographic data.
        """

        assert len(self.reaction_times) == len(self.file_paths), f"""
        The number of reaction times {len(self.reaction_times)} does not match the number of
        'RESULTS.CSV' files {len(self.file_paths)}.
        """

        measurements = []
        for path_idx, (csv_path, reaction_time) in enumerate(
            zip(self.file_paths, self.reaction_times)
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
