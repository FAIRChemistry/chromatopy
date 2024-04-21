import re
from datetime import datetime
from pathlib import Path

from chromatopy.readers.abstractreader import AbstractReader


class ChemstationReader(AbstractReader):

    def _paths(self):
        if self._is_directory:
            return [p for p in Path(self.path).rglob("Report.TXT")]
        else:
            return [self.path]

    def read(self):
        paths = [self.read_file(f) for f in self._paths()]

        measurements = []
        for path in self._paths():
            file = self.read_file(path)

            measurements.append(self.parse_measurement(file))

        return measurements

    def read_file(self, path: str) -> str:

        try:
            with open(path, encoding="utf-16") as f:
                return f.readlines()
        except UnicodeError:
            pass

        try:
            with open(path) as f:
                lines = f.readlines()
                return [line.strip() for line in lines]
        except UnicodeError:
            raise UnicodeError()

    def parse_measurement(self, file: str):
        from chromatopy.core import Chromatogram, Measurement, Peak, SignalType

        INJ_VOLUME = re.compile(r"(\d+\s+(µ?[a-zA-Z]?l))")
        TIMESTAMP = re.compile(
            r"\d{1,2}\/\d{1,2}\/\d{2,4} \d{1,2}:\d{2}:\d{2} (?:AM|PM)"
        )
        SIGNAL = re.compile(r"\bSignal\b \d+:")
        PEAK = re.compile(r"^ +\d+")

        measurement = Measurement()

        signal_slices = []
        for line_count, line in enumerate(file):
            if INJ_VOLUME.search(line):
                injection_volume, volume_unit = INJ_VOLUME.search(line)[0].split()
                measurement.injection_volume = float(injection_volume)
                measurement.injection_volume_unit = volume_unit

            if line.startswith("Injection Date"):
                date_str = TIMESTAMP.search(line)[0]
                timestamp = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
                measurement.timestamp = timestamp

            # Identify slices which describe signal blocks
            if SIGNAL.search(line) and file[line_count + 1] == "\n":
                signal_start = line_count
            if line.startswith("Totals :"):
                signal_end = line_count
                signal_slices.append(slice(signal_start, signal_end))

        # Parse peak data for each signal type
        for signal_slice in signal_slices:

            signal = Chromatogram()

            for line in file[signal_slice]:

                if line.startswith("Signal"):
                    signal_type = line.split(":")[1].split()[0]
                    signal_type = re.findall("[A-Za-z]+", signal_type)[0]
                    signal.type = SignalType[signal_type]
                    continue

                if line.startswith("  # "):
                    peak_units = self._get_peak_units(line)
                    continue

                if PEAK.search(line):
                    peak_values = self._get_peak(line)

                    signal.add_to_peaks(**(peak_values | peak_units))

            measurement.chromatograms.append(signal)

        return measurement

    def _get_peak(self, line: str) -> dict:

        attr_slice_dict = {
            "id": (slice(0, 4), str),
            "retention_time": (slice(5, 12), float),
            "type": (slice(13, 17), str),
            "width": (slice(18, 25), float),
            "area": (slice(26, 36), float),
            "height": (slice(37, 47), float),
            "percent_area": (slice(48, 56), float),
        }

        peak = {}
        for key, (attr_slice, attr_type) in attr_slice_dict.items():
            peak[key] = attr_type(line[attr_slice].strip())

        return peak

    def _get_peak_units(self, line: str) -> dict:

        unit_slice_dict = {
            "retention_time_unit": slice(5, 12),
            "width_unit": slice(18, 25),
            "area_unit": slice(26, 36),
            "height_unit": slice(37, 47),
        }

        units = {}
        for key, unit_slice in unit_slice_dict.items():
            units[key] = line[unit_slice].strip().strip("[]")

        return units

    def parse_method(self, file: str):

        SECTION_START = re.compile(r"^(?![\d\s])[\dA-Z\s]+$")

        section_slices = []
        section_started = False
        for line_id, line in enumerate(file):
            if SECTION_START.search(line):
                section_started = True
                section_start = line_id
            if line == "" and section_started:
                secion_end = line_id
                section_slices.append(slice(section_start, secion_end))
                section_started = False

        return section_slices

    def extract_peaks(self):
        raise NotImplementedError()

    def extract_signal(self):
        raise NotImplementedError()


if __name__ == "__main__":
    dir_path = "/Users/max/Documents/training_course/hao"
    cs = ChemstationReader(dir_path)
    paths = cs._paths()
    res = cs.parse_measurement(paths[0])
    print(res)
