import pandas as pd

from chromatopy.core import Chromatogram, Measurement


def read_chromeleon_file(path: str):
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

    content_dict["Raw Data"] = transpose_data(content_dict["Raw Data"])

    return content_dict


def map_measurement(content: dict) -> Measurement:
    chromatogram = Chromatogram(
        wavelength=int(content["Signal Parameter Information"][1][1].split(" ")[0]),
        times=content["Raw Data"]["time"],
        signals=content["Raw Data"]["value"],
        time_unit="min",
    )

    return Measurement(
        id=content["Sample Information"][2][1],
        chromatograms=[chromatogram],
        injection_volume=float(content["Sample Information"][13][1].replace(",", ".")),
        injection_volume_unit="µL",
        signal_parameter_information=content["Signal Parameter Information"],
        dilution_factor=float(content["Sample Information"][14][1].replace(",", ".")),
    )


def transpose_data(data: list) -> pd.DataFrame:
    data = data
    df = pd.DataFrame(data[1:], columns=["time", "step", "value"])

    df["time"] = df["time"].str.replace(",", ".").astype(float)
    df["step"] = df["step"].str.replace(",", ".").astype(float)
    df["value"] = df["value"].str.replace(",", ".").astype(float)

    return df


if __name__ == "__main__":
    dir_path = "/Users/max/Documents/jan-niklas/MjNK/Standards"
    file_path = (
        "/Users/max/Documents/jan-niklas/MjNK/Standards/Adenosine Stadards_ 0.5 mM.txt"
    )

    import matplotlib.pyplot as plt

    content = read_chromeleon_file(file_path)
    print(content.keys())
    print(content["Raw Data"][0:3])

    measurement = map_measurement(content)

    print(measurement)

    plt.scatter(
        measurement.chromatograms[0].times, measurement.chromatograms[0].signals
    )
    plt.show()
