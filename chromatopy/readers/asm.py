import json
from pathlib import Path
from typing import Any

from loguru import logger

from chromatopy.model import Chromatogram, Measurement, Peak
from chromatopy.readers.abstractreader import AbstractReader


class ASMReader(AbstractReader):
    def model_post_init(self, __context: Any) -> None:
        if not self.reaction_times or not self.time_unit or not self.file_paths:
            logger.debug(
                "Collecting file paths without reaction time and unit parsing."
            )
            self._get_file_paths()

    def read(self) -> list[Measurement]:
        """Reads the chromatographic data from the specified files.

        Returns:
            list[Measurement]: A list of Measurement objects representing the chromatographic data.
        """

        measurements = []
        for file, reaction_time in zip(self.file_paths, self.reaction_times):
            content = self._read_asm_file(file)
            measurement = self._map_measurement(content, reaction_time, file)
            measurements.append(measurement)

        return measurements

    def _get_file_paths(self):
        """Collects the file paths from the directory."""

        files = []
        directory = Path(self.dirpath)

        # check if directory exists
        assert directory.exists(), f"Directory '{self.dirpath}' does not exist."
        assert directory.is_dir(), f"'{self.dirpath}' is not a directory."
        assert any(
            directory.rglob("*.json")
        ), f"No .json files found in '{self.dirpath}'."

        for file_path in directory.iterdir():
            if file_path.name.startswith(".") or not file_path.name.endswith(".json"):
                continue

            files.append(str(file_path.absolute()))

        assert (
            len(files) == len(self.reaction_times)
        ), f"Number of files ({len(files)}) does not match the number of reaction times ({len(self.reaction_times)})."

        self.file_paths = sorted(files)

    def _read_asm_file(self, file_path: str) -> dict:
        with open(file_path, "r") as file:
            content = json.load(file)

        return content

    def _map_measurement(
        self,
        content: dict,
        reaction_time: float,
        path: str,
    ):
        doc = content["liquid chromatography aggregate document"][
            "liquid chromatography document"
        ]
        if len(doc) > 1:
            logger.warning(
                f"More than one chromatogram found in file '{path}'. Using the first chromatogram only."
            )

        sample_document = doc[0]["sample document"]
        name = sample_document.get("written name")
        sample_id = sample_document.get("sample identifier")
        if not sample_id and name:
            sample_id = name

        meas_document = doc[0]["measurement document"]
        peak_list = meas_document["peak list"]["peak"]
        signal = meas_document["chromatogram data cube"]["data"]["measures"][0]
        time = meas_document["chromatogram data cube"]["data"]["dimensions"][0]
        time_unit = meas_document["chromatogram data cube"]["cube-structure"][
            "dimensions"
        ][0]["unit"]

        if time_unit == "s":
            # to min
            time = [t / 60 for t in time]
        elif time_unit == "min":
            pass
        else:
            raise ValueError(f"Unit '{time_unit}' not recognized")

        peaks = [self.map_peaks(peak) for peak in peak_list]

        chrom = Chromatogram(
            peaks=peaks,
            signals=signal,
            times=time,
        )

        return Measurement(
            id=sample_id,
            sample_name=name,
            reaction_time=reaction_time,
            time_unit=self.time_unit,
            temperature=self.temperature,
            temperature_unit=self.temperature_unit,
            ph=self.ph,
            chromatograms=[chrom],
        )

    def map_peaks(self, peak_dict: dict) -> Peak:
        area = peak_dict["peak area"]
        if area["unit"] == "mAU.s":
            area["value"] *= 60
        elif area["unit"] == "mAU.min":
            pass
        else:
            raise ValueError(f"Unit '{area['unit']}' not recognized")

        width = peak_dict["peak width at half height"]
        if width["unit"] == "s":
            width["value"] /= 60
        elif width["unit"] == "min":
            pass
        else:
            raise ValueError(f"Unit '{width['unit']}' not recognized")

        retention_time = peak_dict["retention time"]
        if retention_time["unit"] == "s":
            retention_time["value"] /= 60
        elif retention_time["unit"] == "min":
            pass
        else:
            raise ValueError(f"Unit '{retention_time['unit']}' not recognized")

        peak_start = peak_dict["peak start"]
        if peak_start["unit"] == "s":
            peak_start["value"] /= 60
        elif peak_start["unit"] == "min":
            pass
        else:
            raise ValueError(f"Unit '{peak_start['unit']}' not recognized")

        peak_end = peak_dict["peak end"]
        if peak_end["unit"] == "s":
            peak_end["value"] /= 60
        elif peak_end["unit"] == "min":
            pass
        else:
            raise ValueError(f"Unit '{peak_end['unit']}' not recognized")

        return Peak(
            retention_time=peak_dict["retention time"]["value"],
            area=peak_dict["peak area"]["value"],
            amplitude=peak_dict["peak height"]["value"],
            width=peak_dict["peak width at half height"]["value"],
            skew=peak_dict["chromatographic peak asymmetry factor"],
            percent_area=peak_dict["relative peak area"]["value"],
            peak_start=peak_dict["peak start"]["value"],
            peak_end=peak_dict["peak end"]["value"],
        )


if __name__ == "__main__":
    from chromatopy.units import C
    from chromatopy.units.predefined import minute

    reader = ASMReader(
        dirpath="/Users/max/Documents/GitHub/chromatopy/docs/examples/data/asm",
        reaction_times=[],
        time_unit=minute,
        ph=7.4,
        temperature=37,
        temperature_unit=C,
    )
    measurements = reader.read()
    print(reader.reaction_times)
    print(reader.time_unit.base_units)
    print(reader.file_paths)
