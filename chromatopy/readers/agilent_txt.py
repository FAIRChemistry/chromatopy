import re
from pathlib import Path

from chromatopy.model import Chromatogram, Measurement, SignalType, UnitDefinition
from chromatopy.readers.abstractreader import AbstractReader
from chromatopy.units import ul


class AgilentTXTReader(AbstractReader):
    def __init__(
        self,
        dirpath: str,
        reaction_times: list[float],
        time_unit: UnitDefinition,
        ph: float,
        temperature: float,
        temperature_unit: UnitDefinition,
    ):
        super().__init__(
            dirpath,
            reaction_times,
            time_unit,
            ph,
            temperature,
            temperature_unit,
        )
        self.file_paths = self._get_file_paths()

    def read(self) -> list[Measurement]:
        """Reads chromatographic data from the specified files.

        Returns:
            list[Measurement]: A list of Measurement objects representing the chromatographic data.
        """
        assert len(self.file_paths) == len(self.reaction_times), f"""
        The number of reaction times {len(self.reaction_times)} does not match the number of
        'Report.TXT' files {len(self.file_paths)}.
        """
        measurements = []
        for file, reaction_time in zip(self.file_paths, self.reaction_times):
            file_content = self._read_file(file)
            measurement = self._parse_measurement(
                file_content, reaction_time, self.time_unit
            )
            measurements.append(measurement)

        return measurements

    def _get_file_paths(self) -> list[str]:
        """Collects the file paths of the Agilent TXT files."""
        directory = Path(self.dirpath)
        if directory.is_dir():
            file_paths = [str(p) for p in directory.rglob("Report.TXT")]
        else:
            file_paths = [self.dirpath]

        try:
            assert file_paths, f"No 'Report.TXT' files found in '{self.dirpath}'."
        except AssertionError:
            raise FileNotFoundError(f"No 'Report.TXT' files found in '{self.dirpath}'.")

        return file_paths

    def _read_file(self, path: str) -> list[str]:
        """Reads the content of a file with different encodings."""
        try:
            with open(path, encoding="utf-16") as file:
                return [line.strip() for line in file.readlines()]
        except UnicodeError:
            pass

        try:
            with open(path, encoding="utf-8") as file:
                return [line.strip() for line in file.readlines()]
        except UnicodeError:
            raise UnicodeError(
                f"Failed to read the file '{path}' with available encodings."
            )

    def _parse_measurement(
        self, file_content: list[str], reaction_time: float, time_unit: UnitDefinition
    ) -> Measurement:
        """Parses the file content into a Measurement object."""
        measurement = Measurement(
            id=file_content[0], reaction_time=reaction_time, time_unit=time_unit
        )
        signal_slices = self._identify_signal_slices(file_content)

        for line in file_content:
            self._extract_injection_volume(line, measurement)

        for signal_slice in signal_slices:
            signal = self._parse_signal(file_content[signal_slice])
            measurement.chromatograms.append(signal)

        return measurement

    def _identify_signal_slices(self, file_content: list[str]) -> list[slice]:
        """Identifies the slices that contain signal blocks."""
        signal_slices = []
        signal_start = None

        for line_count, line in enumerate(file_content):
            if (
                re.search(r"\bSignal\b \d+:", line)
                and file_content[line_count + 1] == ""
            ):
                signal_start = line_count
            if line.startswith("Totals :") and signal_start is not None:
                signal_end = line_count
                signal_slices.append(slice(signal_start, signal_end))
                signal_start = None

        return signal_slices

    def _extract_injection_volume(self, line: str, measurement: Measurement):
        """Extracts the injection volume from a line of text."""
        match = re.search(r"(\d+\s+(µ?[a-zA-Z]?l))", line)
        if match:
            injection_volume, _ = match[0].split()
            measurement.injection_volume = float(injection_volume)
            measurement.injection_volume_unit = ul

    def _parse_signal(self, signal_content: list[str]) -> Chromatogram:
        """Parses a signal block into a Chromatogram object."""
        signal = Chromatogram()

        for line in signal_content:
            if line.startswith("Signal"):
                signal_type = re.search(r"\bSignal\b \d+: (\w+)", line).group(1)
                signal.type = SignalType.FID
            elif line.startswith("  # "):
                peak_units = self._extract_peak_units(line)
            elif re.match(r"^\s*\d+", line):
                peak_values = self._extract_peak(line)
                signal.add_to_peaks(**peak_values)

        return signal

    def _extract_peak(self, line: str) -> dict:
        """Extracts peak information from a line of text."""

        columns = line.split()

        if len(columns) == 8:
            # Combine the 2nd and 3rd columns for the 'type' field
            peak_type = f"{columns[2]} {columns[3]}"
            return {
                "id": int(columns[0]),
                "retention_time": float(columns[1]),
                "type": peak_type,
                "width": float(columns[4]),
                "area": float(columns[5]),
                "height": float(columns[6]),
                "area_percent": float(columns[7]),
            }
        else:
            return {
                "id": int(columns[0]),
                "retention_time": float(columns[1]),
                "type": columns[2],
                "width": float(columns[3]),
                "area": float(columns[4]),
                "height": float(columns[5]),
                "area_percent": float(columns[6]),
            }

    def _extract_peak_units(self, line: str) -> dict:
        """Extracts the units of the peak data."""
        unit_slice_dict = {
            "retention_time_unit": slice(5, 12),
            "width_unit": slice(18, 25),
            "area_unit": slice(26, 36),
            "height_unit": slice(37, 47),
        }

        return {
            key: line[unit_slice].strip("[]")
            for key, unit_slice in unit_slice_dict.items()
        }


if __name__ == "__main__":
    dir_path = "/Users/max/Documents/training_course/hao"
    from chromatopy.units import C, min

    reaction_times = [0.0] * 49
    reader = AgilentTXTReader(dir_path, reaction_times, min, 7.0, 25.0, C)
    measurements = reader.read()
    for measurement in measurements:
        print(measurement)
