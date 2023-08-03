import re
import os
from datetime import datetime

from HPLC.core.hplcexperiment import HPLCExperiment
from HPLC.core.measurement import Measurement
from HPLC.core.signal import Signal


def _read_file(path: str):

    with open(path, encoding="utf-16") as f:
        return f.readlines()


def _get_peak(line: str) -> dict:

    attr_slice_dict = {
        "id": (slice(0, 4), int),
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


def _get_peak_units(line: str) -> dict:

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


def parse_measurement(path: str) -> Measurement:

    INJ_VOLUME = re.compile("(\d+\s+(µ?[a-zA-Z]?l))")
    TIMESTAMP = re.compile(
        "\d{1,2}\/\d{1,2}\/\d{2,4} \d{1,2}:\d{2}:\d{2} (?:AM|PM)")
    SIGNAL = re.compile(r"\bSignal\b \d+:")
    PEAK = re.compile("^ +\d+")

    lines = _read_file(path)

    measurement = Measurement()

    signal_slices = []
    for line_count, line in enumerate(lines):
        if INJ_VOLUME.search(line):
            injection_volume, volume_unit = INJ_VOLUME.search(line)[0].split()
            measurement.injection_volume = float(injection_volume)
            measurement.injection_volume_unit = volume_unit

        if line.startswith("Injection Date"):
            date_str = TIMESTAMP.search(line)[0]
            timestamp = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
            measurement.timestamp = timestamp

        # Identify slices which describe signal blocks
        if SIGNAL.search(line) and lines[line_count + 1] == "\n":
            signal_start = line_count
        if line.startswith("Totals :"):
            signal_end = line_count
            signal_slices.append(slice(signal_start, signal_end))

    # Parse peak data for each signal type
    for signal_slice in signal_slices:

        signal = Signal()
        for line in lines[signal_slice]:

            if line.startswith("Signal"):
                signal_type = line.split(":")[1].split()[0]
                signal_type = re.findall("[A-Za-z]+", signal_type)[0]
                signal.type = signal_type.lower()
                continue

            if line.startswith("  # "):
                peak_units = _get_peak_units(line)
                continue

            if PEAK.search(line):
                peak_values = _get_peak(line)

                signal.add_to_peaks(**(peak_values | peak_units))

        measurement.signals.append(signal)

    return measurement


def parse_experiment(path: str) -> HPLCExperiment:

    peak_file_name = "Report.TXT"

    experiment = HPLCExperiment()

    for dir in sorted(os.listdir(path)):
        if dir.endswith(".D"):
            measurement_path = os.path.join(path, dir)
            for file in os.listdir(measurement_path):
                if file == peak_file_name:
                    measurement = parse_measurement(
                        os.path.join(measurement_path, file))

                    experiment.measurements.append(measurement)

    return experiment
