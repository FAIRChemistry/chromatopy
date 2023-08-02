import re
from datetime import datetime


LOCATION = re.compile("Location :")
INJ_VOLUME = re.compile("(\d+\s+(µ?[a-zA-Z]?l))")
DATETIME = re.compile(
    "\d{1,2}\/\d{1,2}\/\d{2,4} \d{1,2}:\d{2}:\d{2} (?:AM|PM)")
SIGNAL = re.compile(r"\bSignal\b \d+")


def _read_file(path: str):

    with open(path, encoding="utf-16") as f:
        lines = f.readlines()

        return lines


def _find_singal_locs(lines: list):

    signal_locs = []
    for line_count, line in enumerate(lines):
        if SIGNAL.search(line) and lines[line_count + 1] == "\n":
            print(line)
            signal_locs.append(line_count)

    return signal_locs


def parse_peaks(path: str):

    # peak_mask = [:4]
    # ret_time_mask = [5:12]
    # type_mask = [13:17]

    lines = _read_file(path)

    for line_count, line in enumerate(lines):
        if INJ_VOLUME.search(line):
            inj_volume, volume_unit = INJ_VOLUME.search(line)[0].split()

        if line.startswith("Injection Date"):
            date_str = DATETIME.search(line)[0]
            date_time = datetime.strptime(date_str, "%m/%d/%Y %I:%M:%S %p")
            date = str(date_time.date())
            time = str(date_time.time())

    return date, time
