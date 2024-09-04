import re
from pathlib import Path

import pandas as pd

from chromatopy.model import Chromatogram, Measurement, UnitDefinition
from chromatopy.readers.abstractreader import AbstractReader
from chromatopy.units import h, min, ul


class ChromeleonReader(AbstractReader):
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
        self._get_file_paths()

    def read(self) -> list[Measurement]:
        """Reads the chromatographic data from the specified files.

        Returns:
            list[Measurement]: A list of Measurement objects representing the chromatographic data.
        """

        measurements = []
        for file, reaction_time in zip(self.file_paths, self.reaction_times):
            content = self._read_chromeleon_file(file)
            measurement = self._map_measurement(content, reaction_time, self.time_unit)
            measurements.append(measurement)

        return measurements

    def _read_chromeleon_file(self, file_path: str) -> dict:
        """Reads and processes the content of a Chromeleon file."""

        with open(file_path, "r", encoding="ISO-8859-1") as file:
            content = file.read()

        content = content.split("\n\n")
        content = [section.lstrip() for section in content if len(section) > 0]

        content_dict = {}
        for section in content[1:]:
            section = section.split("\n")
            section_name = section[0][:-1]
            section_content = [line.split("\t") for line in section[1:]]
            for line_id, line in enumerate(section_content):
                section_content[line_id] = [value for value in line if value]

            content_dict[section_name] = section_content

        content_dict["Raw Data"] = self._transpose_data(content_dict["Raw Data"])

        return content_dict

    def _map_measurement(
        self, content: dict, reaction_time: float, time_unit: UnitDefinition
    ) -> Measurement:
        """Maps the parsed content to a Measurement object."""

        chromatogram = Chromatogram(
            wavelength=int(content["Signal Parameter Information"][1][1].split(" ")[0]),
            times=content["Raw Data"]["time"],
            signals=content["Raw Data"]["value"],
        )

        # reaction_time, unit = self._extract_reaction_time(file_name)

        print(content["Sample Information"][2][1])

        return Measurement(
            id=content["Sample Information"][2][1],
            chromatograms=[chromatogram],
            injection_volume=float(
                content["Sample Information"][13][1].replace(",", ".")
            ),
            injection_volume_unit=ul,
            dilution_factor=float(
                content["Sample Information"][14][1].replace(",", ".")
            ),
            reaction_time=reaction_time,
            time_unit=time_unit,
        )

    def _extract_reaction_time(self, file_name: str) -> tuple[float, UnitDefinition]:
        """Extracts reaction time and unit from the file name."""

        pattern = r"\b(\d+(?:\.\d+)?)\s*(h|min)\b"
        matches = re.findall(pattern, file_name)

        if len(matches) == 0:
            return None, None

        reaction_time, unit_str = matches[0]

        if unit_str == "h":
            unit = h
        elif unit_str == "min":
            unit = min
        else:
            raise ValueError(f"Unit '{unit_str}' not recognized")

        return float(reaction_time), unit

    def _transpose_data(self, data: list) -> pd.DataFrame:
        """Transposes the raw data from the file into a DataFrame."""

        df = pd.DataFrame(data[1:], columns=["time", "step", "value"])

        df["time"] = df["time"].str.replace(",", ".").astype(float)
        df["step"] = df["step"].str.replace(",", ".").astype(float)
        df["value"] = df["value"].str.replace(",", ".").astype(float)

        return df

    def _get_file_paths(self):
        """Collects the file paths from the directory."""

        files = []
        directory = Path(self.dirpath)

        # check if directory exists
        assert directory.exists(), f"Directory '{self.dirpath}' does not exist."
        assert directory.is_dir(), f"'{self.dirpath}' is not a directory."
        assert any(
            directory.rglob("*.txt")
        ), f"No .txt files found in '{self.dirpath}'."

        for file_path in directory.rglob("*.txt"):
            if file_path.name.startswith("."):
                continue

            files.append(str(file_path.absolute()))

        assert (
            len(files) == len(self.reaction_times)
        ), f"Number of files ({len(files)}) does not match the number of reaction times ({len(self.reaction_times)})."

        self.file_paths = sorted(files)


if __name__ == "__main__":
    from chromatopy.units.predefined import min

    dir_path = "/Users/max/Documents/jan-niklas/MjNK/adenosine_std"
    reaction_times = [0, 1, 2, 3, 4, 5.0]

    reader = ChromeleonReader(
        dir_path, reaction_times, min, ph=7.4, temperature=25.0, temperature_unit=min
    )
    measurements = reader.read()

    # print(measurements)
