# Read Chromatographic Data

The `chromatopy` library provides a set of reader functions designed to read and process chromatographic data from various vendor-specific file formats. These functions load data from a specified directory and return a `ChromAnalyzer` object, which serves as the core component in `chromatopy` for handling chromatographic time-course data and calibration measurements.

Each of the [supported file formats](../../supported_formats/#supported-formats) has a corresponding reader function, namely `read_asm`, `read_agilent`, `read_agilent_rdl`, `read_chromeleon`, and `read_shimadzu`. Following arguments are common to all reader functions:

__Required Parameters__:  

- `path`: The path to the directory containing the chromatographic files.
- `ph`: The pH value of the measurement.
- `temperature`: The temperature of the measurement.
- `mode`: The mode of the measurement, either `calibration` or `timecourse`.

__Optional Parameters__:  

- `id`: A unique identifier for the `ChromAnalyzer` object. If not provided, the `path` is used as the ID.
- `name`: The name of the measurement. Defaults to "Chromatographic measurement".
- `values`: A list of reaction times corresponding to each file in the directory for timecourse measurements or concentrations for calibration measurements. If not provided, the reaction times are extracted from the file names if possible.
- `time_unit`: The unit of the time values `nM`, `uM`, `mM`, `M`, `second`, `minute`, and `hour`, which can directly be imported from `chromatopy`. This is also optional if the unit is embedded in the file names.
- `temperature_unit`: The unit of the temperature. The default is Celsius (C).

__Returns__:  

- `ChromAnalyzer` object, containing chromatographic measurements, molecules, and proteins.

??? tip "Automatic extraction of reaction time and unit from file names"

    The reader methods can automatically extract the reaction time and time unit or cocentration values and concentration unit directly from the file names. This is particularly useful when files are named in a way that includes this information (e.g., `sample_10min.txt`, `a11 3.45 hours.json`, or `B02_35_sec.json`). However, this requires the file names to follow a specific format that `chromatopy` can recognize: It is assumed that the reaction time is the first numerical value which might have a decimal separator, followed by the name of the unit `sec`, `second`, `min`, `minute`, or `hour`. For concentration values, the first numerical value is assumed to be the concentration, followed by the name of the unit `mM`, `uM`, `nM`. If the file names do not follow this format, values and units need to be provided manually.

    If the reader function cannot automatically extract the reaction time and time unit or concentration values and concentration unit from the file names, you will need to provide it manually


!!! example "Read Chromatographic Data"
    === "Allotrope Simple Model (ASM) Format"

        The Allotrope Simple Model (ASM) format is the preferred format to be used with `chromatopy`. If not already done, you can batch process your chromatographic data with OpenChrom as [described](../../supported_formats/#spectrum-processing-with-openchrom-from-lablicate) to convert your data to the ASM format.

        ASM data is read in with the `read_asm` function. This function reads chromatographic data from a directory containing Allotrope Simple Model (ASM) files. The measurements are assumed to be named alphabetically, allowing sorting by file name.

        ```python
        from chromatopy import ChromAnalyzer

        data_dir = "data/asm"

        analyzer = ChromAnalyzer.read_asm(
            path=data_dir, ph=7.4, temperature=25, mode="timecourse"
        )
        ```
        ```
        Loaded 4 chromatograms.
        ```

    === "Agilent"

        Agilent files can be read in with the `read_agilent` function. Please note that this function relies on the existence of either a `RESULTS.CSV` or a `*.TXT` file in the `*.D` directory, which can be generated by the Agilent ChemStation software. Thus, it is recommended to use OpenChrom to convert your data to the ASM format.



        ```python
        from chromatopy import ChromAnalyzer

        data_dir = "data/agilent_txt"
        reaction_times = [0, 10, 20, 40]

        analyzer = ChromAnalyzer.read_agilent(
            path=data_dir,
            ph=7.4,
            temperature=25,
            values=reaction_times,
            unit="min",
            mode="timecourse",
        )
        ```
        ```
        Loaded 4 chromatograms.
        ```

    === "Agilent RDL"

        The `read_agilent` function also reads rdl formatted *.txt files.

        ```python
        from chromatopy import ChromAnalyzer

        data_dir = "data/agilent_rdl"

        analyzer = ChromAnalyzer.read_agilent(
            path=data_dir,
            ph=7.4,
            temperature=25,
            mode="timecourse",
        )
        ```
        ```
        Loaded 2 chromatograms.
        ```

    === "Chromeleon"

        Chromeleon files can be read in with the `read_chromeleon` function. Please note that this function relies on the existence of a `*.txt` file in the directory. If applicable use OpenChrom to preproces and convert your files from Thermo Fisher Scientific to the ASM format.

        ```python
        from chromatopy import ChromAnalyzer

        data_dir = "data/chromeleon"

        analyzer = ChromAnalyzer.read_chromeleon(
            path=data_dir,
            ph=7.4,
            temperature=25,
            mode="calibration",
        )
        ```
        ```
        Loaded 6 chromatograms.
        ```

    === "Shimadzu"

        Shimadzu `*.txt` files can be read in with the `read_shimadzu` function. This function reads chromatographic data as the previously described functions.  
        In this dataset, the corresponding reaction times for each measurement are manually specified and the respective `time_unit` is imported.

        ```python
        from chromatopy import ChromAnalyzer

        data_dir = "data/shimadzu"

        analyzer = ChromAnalyzer.read_shimadzu(
            path=data_dir,
            ph=7.4,
            temperature=25,
            values=[0, 5, 10, 15, 20, 25, 30, 35, 40],
            unit="min",
            mode="timecourse",
        )
        ```
        ```
        Loaded 9 chromatograms.
        ```

    === "Thermo Scientific"

        Thermo Scientific `*.TX0` files can be read in with the `read_thermo` function. This function reads chromatographic data from files that use comma as decimal separator.

        ```python
        from chromatopy import ChromAnalyzer

        data_dir = "data/thermo"

        analyzer = ChromAnalyzer.read_thermo(
            path=data_dir,
            values=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
            unit="min",
            ph=7.4,
            temperature=25.0,
            temperature_unit="C",
            silent=True,
            mode="timecourse",
        )
        ```
        ```
        Loaded 8 chromatograms.
        ```

The readers will take care of the following:

- Handle decimal comma format (e.g., "0,038" becomes 0.038)
- Extract metadata like sample name and acquisition time
- Parse peak information including retention time, area, height, and percent area
- Sort files alphabetically to match with the provided time values

## Saving the `ChromAnalyzer` Object

It is possible to save the current state of the `ChromAnalyzer` object to a file using the `to_json` method. This method saves the object as a JSON file, which can be loaded back into the `chromatopy` framework using the `from_json` function.

```python
analyzer.to_json("data/instances/shimadzu_analyzer.json")

analyzer = ChromAnalyzer.from_json("data/instances/shimadzu_analyzer.json")
```
