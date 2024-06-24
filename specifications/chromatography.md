# Chromatography Data Model

## Objects

### Measurement

- chromatograms
  - Type: Chromatogram
  - Description: Measured signal
  - Multiple: True
- timestamp
  - Type: datetime
  - Description: Timestamp of sample injection into the column
- reaction_time
  - Type: float
  - Description: Reaction time
- time_unit
  - Type: Unit
  - Description: Unit of time
- injection_volume
  - Type: float
  - Description: Injection volume
- dilution_factor
  - Type: float
  - Description: Dilution factor
- injection_volume_unit
  - Type: Unit
  - Description: Unit of injection volume
- reaction_time
  - Type: float
  - Description: Reaction time

### Chromatogram

- peaks
  - Type: Peak
  - Description: Peaks in the signal
  - Multiple: True
- signals
  - Type: float
  - Description: Signal values
  - Multiple: True
- times
  - Type: float
  - Description: Time values of the signal
  - Multiple: True
- time_unit
  - Type: Unit
  - Description: Unit of time
- processed_signal
  - Type: float
  - Description: Processed signal values after baseline correction and deconvolution
  - Multiple: True
- wavelength
  - Type: float
  - Description: Wavelength of the signal in nm
- type
  - Type: SignalType
  - Description: Type of signal

### Peak

- analyte_id
  - Type: str
  - Description: ID of the analyte
- retention_time
  - Type: float
  - Description: Retention time of the peak
- timestamp
  - Type: datetime
  - Description: Timestamp of the peak
- retention_time_unit
  - Type: Unit
  - Description: Unit of retention time
- type
  - Type: string
  - Description: Type of peak (baseline-baseline / baseline-valley / ...)
- peak_start
  - Type: float
  - Description: Start retention time of the peak
- peak_end
  - Type: float
  - Description: End retention time of the peak
- width
  - Type: float
  - Description: Width of the peak
- width_unit
  - Type: Unit
  - Description: Unit of width
- area
  - Type: float
  - Description: Area of the peak
- area_unit
  - Type: Unit
  - Description: Unit of area
- height
  - Type: float
  - Description: Height of the peak
- height_unit
  - Type: Unit
  - Description: Unit of height
- percent_area
  - Type: float
  - Description: Percent area of the peak
- tailing_factor
  - Type: float
  - Description: Tailing factor of the peak
- separation_factor
  - Type: float
  - Description: Separation factor of the peak

### Standard

- analyte_id
  - Type: str
  - Description: ID of the analyte
- factor
  - Type: float
  - Description: Factor to convert the signal to concentration
- intercept
  - Type: float
  - Description: Intercept of the standard curve
- r_squared
  - Type: float
  - Description: R squared value of the standard curve

## Enumerations

### SignalType

```python
UV = "uv/visible absorbance detector"
FLD = "fluorescence detector"
FID = "flame ionization detector"
TCD = "thermal conductivity detector"
RID = "refractive index detector"
ELSD = "evaporative light scattering detector"
MS = "mass spectrometry"
DAD = "diode array detector"
```

### Role

```python
ANALYTE = "analyte"
STANDARD = "standard"
```
