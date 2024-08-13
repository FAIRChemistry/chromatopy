---
repo: "https://github.com/FAIRChemistry/chromatopy"
prefix: "chromatopy"
---

# Chromatography Data Model

## Objects

### Measurement

- __id__
  - Type: string
  - Description: Unique identifier of the measurement
- __sample_name__
  - Type: string
  - Description: Name of the sample
- chromatograms
  - Type: Chromatogram[]
  - Description: Measured signal
- timestamp
  - Type: string
  - Description: Timestamp of sample injection into the column
- reaction_time
  - Type: float
  - Description: Reaction time when the sample was injected
- injection_volume
  - Type: float
  - Description: Injection volume
- dilution_factor
  - Type: float
  - Description: Dilution factor
- injection_volume_unit
  - Type: UnitDefinition
  - Description: Unit of injection volume

### Chromatogram

- __type__
  - Type: SignalType
  - Description: Type of signal
- peaks
  - Type: Peak[]
  - Description: Peaks in the signal
- signals
  - Type: float[]
  - Description: Signal values
- times
  - Type: float[]
  - Description: Time values of the signal
- time_unit
  - Type: UnitDefinition
  - Description: Unit of time
- processed_signal
  - Type: float[]
  - Description: Processed signal values after baseline correction and deconvolution
- wavelength
  - Type: float
  - Description: Wavelength of the signal in nm

### Peak

- __analyte_id__
  - Type: string
  - Description: ID of the analyte
- __retention_time__
  - Type: float
  - Description: Retention time of the peak in minutes
- __area__
  - Type: float
  - Description: Area of the peak
- timestamp
  - Type: string
  - Description: Timestamp of the peak
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
- height
  - Type: float
  - Description: Height of the peak
- percent_area
  - Type: float
  - Description: Percent area of the peak
- tailing_factor
  - Type: float
  - Description: Tailing factor of the peak
- separation_factor
  - Type: float
  - Description: Separation factor of the peak

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
