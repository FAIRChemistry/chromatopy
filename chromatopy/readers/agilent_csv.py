from pathlib import Path

import pandas as pd

from chromatopy.model import Chromatogram, Measurement, Peak, UnitDefinition


def assamble_measurements_from_agilent_csv(
    path: str,
    reaction_times: list[float],
    time_unit: UnitDefinition,
    ph: float,
    temperature: float,
    temperature_unit: UnitDefinition,
) -> list[Measurement]:
    """Assembles a list of Measurement instances from Agilent CSV files.
    Args:
        path (str): The path to the directory containing the Agilent CSV files.
        reaction_times (list[float]): List of reaction times. Need to be sorted
            in the same order as the directories in the specified path.
        time_unit (UnitDefinition): The unit of the reaction times.
        temperature (float): The temperature.
        temperature_unit (UnitDefinition): The unit of the temperature.
        ph (float): The pH.

    Raises:
        AssertionError: If the number of reaction times does not match the number of subdirectories
            with a "RESULTS.CSV" file.

    Returns:
        list[Measurement]: List of Measurement instances.
    """

    csv_paths = get_csv_file_paths(path)

    assert len(reaction_times) == len(csv_paths), f"""
    The number of reaction times {len(reaction_times)} does not match the number of
    subdirectories with a "RESULTS.CSV" file {len(csv_paths)}.
    """

    measurements = []
    for path_idx, (csv_path, reaction_time) in enumerate(
        zip(csv_paths, reaction_times)
    ):
        peaks = read_agilent_csv_peaks(csv_path)
        chromatogram = Chromatogram(peaks=peaks)

        measurements.append(
            Measurement(
                id=f"m{path_idx}",
                chromatograms=[chromatogram],
                reaction_time=reaction_time,
                time_unit=time_unit,
                temperature=temperature,
                temperature_unit=temperature_unit,
                ph=ph,
            )
        )

    return measurements


def get_csv_file_paths(dirpath: str) -> list[str]:
    """Traverses the specified directory and return the paths to the RESULTS.CSV files.

    Args:
        dirpath (str): The path to the directory.

    Raises:
        AssertionError: If the number of found *.D directories does not match the number of subdirectories
            with a "RESULTS.CSV" file.
        FileNotFoundError: If no RESULTS.CSV file is found in the specified directory.

    Returns:
        list[str]: List of paths to the RESULTS.CSV files.
    """
    target_paths = []

    path = Path(dirpath)
    dirs = sorted(path.iterdir())
    found_count = 0

    for folder in dirs:
        # Check if the folder is a directory and ends with ".D" and does not start with "."
        if (
            folder.is_dir()
            and folder.name.endswith(".D")
            and not folder.name.startswith(".")
        ):
            for file in folder.iterdir():
                # Check if the file is "RESULTS.CSV" and does not start with "."
                if file.name == "RESULTS.CSV" and not file.name.startswith("."):
                    found_count += 1
                    target_paths.append(str(file.absolute()))

    if found_count == 0:
        raise FileNotFoundError("No RESULTS.CSV file found in the specified directory.")

    return target_paths


def read_agilent_csv_peaks(path: str, skiprows: int = 6) -> list[Peak]:
    """Reads an Agilent CSV file.
    Returns list of dictionaries with keys "R.T.", "Area", and "Height".

    Args:
        path (str): The path to the file.
        skiprows (int, optional): Number of rows to skip. Defaults to 6.

    Returns:
        pd.DataFrame: The data in the file.
    """
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
