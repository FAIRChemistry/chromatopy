# 📖 Read Chromatographic Data

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FAIRChemistry/chromatopy/blob/update-sdrdm/docs/examples/read_data.ipynb)

---

The `chromatopy` library provides a set of reader functions designed to read and process chromatographic data from various file formats. These functions typically read data from a specified directory and return a `ChromAnalyzer` object, which is the central object used in `chromatopy` to manipulate and analyze chromatographic measurements.

## General Syntax
Each of the [supported file formats](../../supported_formats/#supported-formats) has a corresponding reader function, namely `read_asm`, `read_agilent`, `read_chromeleon`, and `read_shimadzu`. Following arguments are common to all reader functions:

__Required Parameters__:
- `path`: The path to the directory containing the chromatographic files.
- `ph`: The pH value of the measurement.
- `temperature`: The temperature of the measurement.

__Optional Parameters__:

- `id`: A unique identifier for the `ChromAnalyzer` object. If not provided, the `path` is used as the ID.
- `name`: The name of the measurement. Defaults to "Chromatographic measurement".
- `reaction_times`: A list of reaction times corresponding to each measurement in the directory. This parameter is optional if the reaction times are embedded in the file names. **For calibration data**, specify this as a list of zeros, with the length equal to the number of measurements.
- `time_unit`: The unit of the time values `second`, `minute`, and `hour`, which can directly be imported from `chromatopy`. This is also optional if the unit is embedded in the file names. **For calibration data**, any time unit can be used, as it does not affect the calibration process.
- `temperature_unit`: The unit of the temperature. The default is Celsius (C).


__Returns__:
The function returns a `ChromAnalyzer` object, which can be used to further analyze and manipulate the chromatographic data within the `chromatopy` framework.

!!! tip "Automatic extraction of reaction time and unit from file names"

    `chromatopy` can automatically extract the reaction time and time unit directly from the file names. This is particularly useful when files are named in a way that includes this information (e.g., `sample_10min.txt`, `a11 3.45 hours.json`, or `B02_35_sec.json`). However, this requires the file names to follow a specific format that `chromatopy` can recognize: It is assumed that the reaction time is the first numerical value which might have a decimal separator, followed by the name of the unit `sec`, `second`, `min`, `minute`, or `hour`. If the file names do not follow this format, you will need to provide the reaction times and time units manually.

### Specification of Reaction Times and Time Units

If the reader function cannot automatically extract this information, you will need to provide it manually:

- **`reaction_times`**: Provide a list of reaction times corresponding to each file in the directory. Make sure that the file names are sorted alphabetically, so the order of reaction times in the list matches the order in which the files are processed.
- **`time_unit`**: Specify the unit of the time values (e.g., `sec`, `minute`, `hour`). Like `reaction_times`, ensure that this information matches the order of files based on how they are sorted.

## Allotrope Simple Model (ASM) Format

The Allotrope Simple Model (ASM) format is the preferred format to be used with `chromatopy`. If not already done, you can batch process your chromatographic data with OpenChrom as [described](../../supported_formats/#spectrum-processing-with-openchrom-from-lablicate) to convert your data to the ASM format.

ASM data is read in with the `read_asm` function. This function reads chromatographic data from a directory containing Allotrope Simple Model (ASM) files. The measurements are assumed to be named alphabetically, allowing sorting by file name.

```python
from chromatopy import ChromAnalyzer

data_dir = "data/asm"

analyzer = ChromAnalyzer.read_asm(
    path=data_dir,
    ph=7.4,
    temperature=25,
)
```
```
✅ Loaded 4 chromatograms.
```

## Other Supported Formats

### Agilent ChemStation

Agilent ChemStation files can be read in with the `read_agilent` function. Please note that this function relies on the existence of either a `RESULTS.CSV` or a `*.TXT` file in the `*.D` directory, which can be generated by the Agilent ChemStation software. Thus, it is recommended to use OpenChrom to convert your data to the ASM format.

Please note, that automatic reaction time and unit detection does not work for `RESULTS.CSV` files. The reaction time and unit must be provided manually.

```python
from chromatopy import ChromAnalyzer

data_dir = "data/agilent_txt"
reaction_times = [0, 10, 20, 40]

analyzer = ChromAnalyzer.read_agilent(
    path=data_dir,
    ph=7.4,
    temperature=25,
)
```
```
✅ Loaded 4 chromatograms.
```

### Chromeleon

Chromeleon files can be read in with the `read_chromeleon` function. Please note that this function relies on the existence of a `*.txt` file in the directory. If applicable use OpenChrom to preproces and convert your files from Thermo Fisher Scientific to the ASM format.

```python
from chromatopy import ChromAnalyzer, minute

data_dir = "data/chromeleon"
reaction_times = [0, 0, 0, 0, 0, 0]

analyzer = ChromAnalyzer.read_chromeleon(
    path=data_dir,
    ph=7.4,
    temperature=25,
    reaction_times=reaction_times,
    time_unit=minute,
)
```
```
✅ Loaded 6 chromatograms.
```

### Shimadzu

Shimadzu `*.txt` files can be read in with the `read_shimadzu` function. This function reads chromatographic data as the previously described functions.  
In this dataset, the corresponding reaction times for each measurement are manually specified and the respective `time_unit` is imported.

```python
from chromatopy import ChromAnalyzer, minute

data_dir = "data/shimadzu"

analyzer = ChromAnalyzer.read_shimadzu(
    path=data_dir,
    ph=7.4,
    temperature=25,
    reaction_times=[0, 5, 10, 15, 20, 25, 30, 35, 40],
    time_unit=minute,
)
```
```
✅ Loaded 9 chromatograms.
```

## Saving the `ChromAnalyzer` Object

It is possible to save the current state of the `ChromAnalyzer` object to a file using the `to_json` method. This method saves the object as a JSON file, which can be loaded back into the `chromatopy` framework using the `from_json` function.

```python
analyzer.to_json("data/instances/shimadzu_analyzer.json")

analyzer = ChromAnalyzer.from_json("data/instances/shimadzu_analyzer.json")
```