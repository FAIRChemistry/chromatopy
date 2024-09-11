# Data Preparation

## 📂 Data organization

`chromatopy` strives to simplify the data import and processing of chromatographic data. The tool focuses on efficient handling of time-course reaction data, allowing to combine the measured data with data on reaction conditions, concentration calculations and export to the EnzymeML format.  

For this purpose, `chromatopy` requires a specific organization of the measurement data of a time-course or calibration series. The scope of one analysis run is therefore eighter a single chemical sample which is measured over time or a calibration series with multiple samples for different concentrations. 

### Time-course data

- All data files of a time-course series should be stored within a single folder.
- The files within a folder should be named in a way that allows alphabetical sorting to represent the chronological or logical order of the data. E.g. naming time-course data by reaction time or calibration data by concentration. Otherwise, data will be assigned to wrong concentration or time points.

!!! Tip
    Name your files including the corresponding reaction time e.g. `B002_12_h.txt` or `A034.2_5.67min.json` Then the files will be extracted in the correct order and with the correct time unit. In the latter case, the reaction time is `5.67` `min` and alphabetic naming is not necessary. Note that the reaction time unit should be consistent across all files.

### Calibration data

- The set of calibration data files should be stored within a single folder.
- The files need to be named in an alphabetically sortable way to represent the logical order of the data. E.g. naming calibration data by ascending concentration values `abts_001uM.json` `abts_050uM.json` `abts_300uM.json`.
- For calibration data the corresponding concentration cannot be extracted from the file name.

## 🔧 Supported Formats

Most output data from chromatographic devices is vendor-specific and proprietary. However, [OpenChrom](https://lablicate.com/platform/openchrom), an open-source software that is free for academic use, provides the tools to convert proprietary data from almost all vendors into a vendor-neutral and machine-readable format, specifically the Allotrope Simple Model (ASM). A complete list of supported formats for pre-processing with OpenChrom can be found [here](https://www.openchrom.net/).
 

Peak detection and integration with subsequent export to the ASM format is the recommended way to prepare data for subsequent processing with `chromatopy`. For information on how to batch process chromatographic data with OpenChrom, please refer to the section [Spectrum Processing with OpenChrom](#spectrum-processing-with-openchrom-from-lablicate).

### Allotrope Simple Model

!!! info
    The Allotrope Simple Model (ASM) is a JSON-based and vendor-independent format for analytical data. It is designed to store raw and processed data as well as metadata.

The ASM format is the preferred format for data import. It can be exported from OpenChrom and contains the measured signal and data of all peaks which were processed by OpenChrom. The format is supported by `chromatopy` and can be imported directly.

### Vendor specific formats

As an alternative to the ASM format, `chromatopy` supports the import of chromatographic data from various vendors.  Samples of all supported formats are provided below.

??? example "File Examples"

    === "Agilent REPORT.TXT"

        ```
        Data File C:\CHEM32\1\DATA\H 2023-07-24 21-36-55\001F0104.D
        Sample Name: DFA-708-01
        Instrument 1 7/24/2023 10:34:06 PM Group

        =====================================================================
        Acq. Operator   : Group                           Seq. Line :   1
        Acq. Instrument : Instrument 1                    Location : Vial 1
        Injection Date  : 7/24/2023 10:22:05 PM                Inj :   4
                                                        Inj Volume : 1000 µl
        Sequence File   : C:\Chem32\1\DATA\07-24 21-36-55\H.S
        Method          : C:\CHEM32\1\DATA\07-24 21-36-55\H.M (
                        Sequence Method)
        Last changed    : 7/24/2023 4:35:09 PM
        =====================================================================
                                Area Percent Report                         
        =====================================================================

        Sorted By             :      Signal
        Multiplier            :      1.0000
        Dilution              :      1.0000
        Use Multiplier & Dilution Factor with ISTDs


        Signal 1: FID1 A, 

        Peak RetTime Type  Width     Area      Height     Area  
        #   [min]        [min]   [pA*s]      [pA]         %
        ----|-------|----|-------|----------|----------|--------|
        1   2.828 BB    0.0857 1.95364e4  3417.83057 99.52651
        2   4.059 BB    0.0745   92.94276   18.85831  0.47349
        Totals :                  1.96294e4  3436.68888


        Signal 2: TCD2 B, 

        Peak RetTime Type  Width     Area      Height     Area  
        #   [min]        [min]  [25 uV*s]   [25 uV]       %
        ----|-------|----|-------|----------|----------|--------|
        1   2.832 BB    0.0841 1090.67725  195.31581 1.000e2 
        Totals :                  1090.67725  195.31581

        =====================================================================
                                Summed Peaks Report                         
        =====================================================================

        Signal 1: FID1 A, 
        Signal 2: TCD2 B, 
        =====================================================================
                            Final Summed Peaks Report                      
        =====================================================================

        Signal 1: FID1 A, 
        Signal 2: TCD2 B, 
                                *** End of Report ***
        ```

    === "Agilent RESULTS.CSV"

        ```
        [contents]
        count=1
        Name=,D:\MassHunter\GCMS\RAU-R505-0.D
        1=,INT TIC: RAU-R505-0.D\data.ms
        [INT TIC: RAU-R505-0.D\data.ms]
        Time=,Thu Jun 06 17:25:48 2024
        Header=,"Peak","R.T.","First","Max","Last","PK  TY","Height","Area","Pct Max","Pct Total"
        1=,  1,  6.056,  856, 860, 880,"  M ",1366398, 13751453,100.00, 63.328
        2=,  2,  6.302,  899, 903, 909,"  M ",1063632,  7963360, 57.91, 36.672
        ```

    === "Shimadzu *.TXT"

        ```
        [Header]
        Application Name,LCsolution
        Version,1.25
        Data File Name,C:\LabSolutions\0.lcd
        Output Date,12.12.2023.
        Output Time,11:18:30

        [File Information]
        Type,Data File
        Generated,21.2.2012. 13:16:32
        Generated by,Admin
        Modified,21.2.2012. 13:33:38
        Modified by,Admin

        [Sample Information]
        Operator Name,Admin
        Acquired,21.2.2012. 13:16:57
        Sample Type,0:Unknown
        Level,0
        Sample Name,0
        Sample ID,
        ISTD Amount 1,1
        ISTD Amount 2,1
        ISTD Amount 3,1
        ISTD Amount 4,1
        ISTD Amount 5,1
        ISTD Amount 6,1
        ISTD Amount 7,1
        ISTD Amount 8,1
        ISTD Amount 9,1
        ISTD Amount 10,1
        ISTD Amount 11,1
        ISTD Amount 12,1
        ISTD Amount 13,1
        ISTD Amount 14,1
        ISTD Amount 15,1
        ISTD Amount 16,1
        ISTD Amount 17,1
        ISTD Amount 18,1
        ISTD Amount 19,1
        ISTD Amount 20,1
        ISTD Amount 21,1
        ISTD Amount 22,1
        ISTD Amount 23,1
        ISTD Amount 24,1
        ISTD Amount 25,1
        ISTD Amount 26,1
        ISTD Amount 27,1
        ISTD Amount 28,1
        ISTD Amount 29,1
        ISTD Amount 30,1
        ISTD Amount 31,1
        ISTD Amount 32,1
        Sample Amount,1
        Dilution Factor,1
        Vial#,1
        Injection Volume,20

        [Original Files]
        Data File,C:\LabSolutions
        Method File,C:\LabSolutions
        Batch File,C:\LabSolutions
        Report Format File,C:\LabSolutions
        Tuning File,

        [File Description]


        [Configuration]
        # of Detectors,2
        Detector ID,Detector A,AD2
        Detector Name,Detector A,AD2
        # of Channels,1,1

        [Peak Table(Detector A-Ch1)]
        # of Peaks,14
        Peak#,R.Time,I.Time,F.Time,Area,Height,A/H,Conc.,Mark,ID#,Name,k',Plate #,Plate Ht.,Tailing,Resolution,Sep.Factor,Conc. %,Norm Conc.
        1,0.143,0.017,0.342,1278,107,11.9230,0.0000,   ,,,0.000,4,41558.735,1.160,0.000,0.000,0.0000,0.0000
        2,2.677,2.600,2.842,7633,868,8.7930,0.0000,   ,,,17.675,2267,66.156,1.540,9.621,0.000,0.0000,0.0000
        3,3.113,2.867,3.492,74069,3235,22.8950,0.0000,   ,,,20.715,284,528.740,0.000,0.904,1.172,0.0000,0.0000
        4,3.674,3.492,4.225,62448,1896,32.9390,0.0000, V ,,,24.632,195,767.696,0.000,0.627,1.189,0.0000,0.0000
        5,4.541,4.225,4.858,61821,2075,29.7890,0.0000, V ,,,30.681,11,13168.368,0.000,0.270,1.246,0.0000,0.0000
        6,5.264,4.858,6.025,591150,23289,25.3830,0.0000, V ,,,35.719,1559,96.223,0.000,0.244,1.164,0.0000,0.0000
        7,6.234,6.025,6.417,69898,3040,22.9950,0.0000, V ,,,42.488,8,18539.786,0.000,0.209,1.189,0.0000,0.0000
        8,6.570,6.417,6.708,51229,2962,17.2940,0.0000, V ,,,44.832,6,27270.488,0.000,0.034,1.055,0.0000,0.0000
        9,7.099,6.708,7.442,271461,9085,29.8790,0.0000, V ,,,48.524,1106,135.634,0.000,0.088,1.082,0.0000,0.0000
        10,8.063,7.442,8.950,2838883,74297,38.2100,0.0000, V ,1,RT8.063,55.243,1156,129.804,0.000,1.069,1.138,0.0000,0.0000
        11,9.083,8.950,10.367,458569,7811,58.7060,0.0000, V ,,,62.362,26,5780.190,0.000,0.253,1.129,0.0000,0.0000
        12,10.392,10.367,11.067,150804,3848,39.1900,0.0000, V ,,,71.492,1,157400.235,0.000,0.053,1.146,0.0000,0.0000
        13,11.391,11.067,12.442,273652,3881,70.5040,0.0000, V ,,,78.463,96,1566.775,0.000,0.042,1.098,0.0000,0.0000
        14,12.567,12.442,14.967,184099,2616,70.3870,0.0000, V ,,,86.664,13,11724.488,0.000,0.126,1.105,0.0000,0.0000

        [Peak Table(AD2)]
        # of Peaks,0

        [Peak Table(PDA-Ch1)]
        # of Peaks,0

        [Compound Results(Detector A)]
        # of IDs,1
        ID#,Name,R.Time,Area,Height,Conc.,Curve,3rd,2nd,1st,Constant,Conc. %,Norm Conc.
        1,RT8.063,8.063,2838883,74297,0.0000,Linear,0.0,0.0,0.0,0.0,0.0000,0.0000

        [Compound Results(AD2)]
        # of IDs,0

        [Compound Results(PDA)]
        # of IDs,0

        [Group Results(Detector A)]
        # of Groups,0

        [Group Results(AD2)]
        # of Groups,0

        [Group Results(PDA)]
        # of Groups,0

        [LC Chromatogram(Detector A-Ch1)]
        Interval(msec),500
        # of Points,1801
        Start Time(min),0.000
        End Time(min),15.000
        Intensity Units,mV
        Intensity Multiplier,0.001
        Wavelength(nm),215
        R.Time (min),Intensity
        0.00000,-132
        0.00833,-132
        0.01667,-52
        0.02500,3
        0.03333,8
        ...
        ```

    === "Thermo Fisher Scientific *.TXT"

        ```
        Filepath	C:¥Chromel¥data¥HPLC¥2_Data¥UV_VIS_1.CHL¥20.acd
        Channel	UV_VIS_1

        Sample Information:
        Datasource	BCI
        Sequence	HPLC¥2_Data
        Sample	A 1,0 mM
        Sample Number	31
        Sample Position	RD3
        Sample ID	20
        Comment	
        QNT method	20211221
        PGM file	20230109
        Type	standard
        Status	finished
        Date	02.02.2023
        Time	16:12:23
        Injection Volume (ｵl)	10,00
        Dilution Factor	1,000000
        Amount	1,000000
        Weight	1,000000

        Raw Data Header Information:
        Time Min. (min)	0,000
        Time Max. (min)	44,000
        Raw-Time Min. (min)	0,000
        Raw-Time Max. (min)	44,000
        Data Points	26401
        Detector	VWD3000.dll
        Preferred Read Mode	Unknown
        Write Mode	Unknown
        Data System	Chromeleon
        Version High	06
        Version Low	80
        Build No.	3160
        File Format Version	11
        Generation Type	8
        File ID	239054205
        File Status	16
        GUID	8ce9b975
        Signal Factor	0,000010
        Signal Dimension	mAU
        Signal Unit	Absorbance
        Signal Min.	-2,8254
        Signal Max.	576,766300
        Channel Name	UV_VIS_1
        Driver Name	VWD-3x00(RS) Detector
        Min. Step	10
        Max. Step	10
        Average Step	10

        Signal Parameter Information:
        Signal Info	WVL:254 nm
        Wavelength	254 nm

        Raw Data:
        Time(min)	Step(sec)	Value(mAU)
        0,000000	0,00	0,125090	
        0,001667	0,10	0,125010	
        0,003333	0,10	0,124540	
        0,005000	0,10	0,124710	
        0,006667	0,10	0,123320	
        0,008333	0,10	0,123160	
        ...
        ```

## 🌈 Spectrum Processing with OpenChrom (from Lablicate)

!!! info
    [OpenChrome](https://lablicate.com/platform/openchrom) is tailored for data analysis purposes including processing, visualization and reporting. The implemented batch-processing allows high-throughput evaluation. It can be used for targeted and non-targeted chromatography. A continuously growing portfolio of processing and analysis procedures is provided. Extensions are welcome, as OpenChrom is developed open source and uses a flexible approach, which allows others to implement their own methods, algorithms, filters, detectors, integrators or processors.

Since OpenChrom offers a convenient way to batch-process and export chromatographic data, it is the recommended tool for peak processing prior to data import with chromatopy. 
The following steps showcase how to batch process chromatographic data with OpenChrom, including baseline correction, peak detection and integration, and export to the Allotrope Simple Model (ASM) format. For further information, please refer to the [official documentation of OpenChrom](https://lablicate.com/marketplace/extensions/handbook), which is freely available for academic use.

### Batch processing

If not already done, download and setup OpenChrom as described in the [installation section](installation.md#openchrome-from-lablicate){ data-preview }

1. Open OpenChrom and navigate to `Chromatogram` > `Batch Process`.

2. A new window will open, where you need to specify a new _Project_. Afterwards, a name for the _Batch Process_ can be defined.

3. Now the _Chromatogram Batch Process_ mode needs to be defined. Depending on you data, one of the following modes can be selected. The processing might fail if the wrong mode is selected.
    - `WSD`: Wavelength Spectrum Data
    - `MSD`: Mass Spectrum Data
    - `CSD`
    - `VSD`

4. Now a _Batch Job_ window is opened. The window is divided into the left side, where files can be added, and the right side, where the processing steps can be defined.

5. Add the files you want to process by clicking on the :material-plus: icon in the bottom of the left side. The files can be selected from the file system.
![Batch process steps](pics/select_data.png)

6. Add proccessing steps by clicking on the :material-plus: icon in the bottom of the right side. The following steps are recommended for peak processing and can be added with default parameters:
    - `Baseline Detector` > `SNIP`
    - `Peak Detector` > `First Derivative`
    - `Peak Integrator` > `Peak Integrator Trapezoid`
    - `Chromatogram Export` > `ASM ... (*.json)` then define the output folder.

7. Run the batch process by clicking on the _Execute_ :material-play: icon in the top right corner.
![Batch process steps](pics/batch_setup.png)

8. After the processing is finished, the data can be imported with chromatopy.