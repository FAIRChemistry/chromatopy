---
repo: "https://github.com/FAIRChemistry/chromatopy"
prefix: "chromatopy"
---

# Chromatography Data Model

## Objects

### Measurement

- __id__
  - Type: string
  - Description: Unique identifier of the measurement.
- __reaction_time__
  - Type: float
  - Description: Reaction time when the sample was injected.
- __time_unit__
  - Type: UnitDefinition
  - Description: Unit of time.
- __chromatograms__
  - Type: Chromatogram[]
  - Description: Measured chromatogram and peaks.
- temperature
  - Type: float
  - Description: Temperature of the measurement.
- temperature_unit
  - Type: UnitDefinition
  - Description: Unit of temperature.
- ph
  - Type: float
  - Description: pH of the measurement.
- sample_name
  - Type: string
  - Description: Name of the sample.
- timestamp
  - Type: string
  - Description: Timestamp of sample injection into the column.
- injection_volume
  - Type: float
  - Description: Injection volume.
- dilution_factor
  - Type: float
  - Description: Dilution factor.
- injection_volume_unit
  - Type: UnitDefinition
  - Description: Unit of injection volume.

### Chromatogram

- type
  - Type: SignalType
  - Description: Type of signal.
- peaks
  - Type: Peak[]
  - Description: Peaks in the signal.
- signals
  - Type: float[]
  - Description: Signal values.
- times
  - Type: float[]
  - Description: Time values of the signal in minutes.
- processed_signal
  - Type: float[]
  - Description: Processed signal values after signal processing.
- wavelength
  - Type: float
  - Description: Wavelength of the signal in nm.

### Peak

- __retention_time__
  - Type: float
  - Description: Retention time of the peak in minutes.
- __area__
  - Type: float
  - Description: Area of the peak.
- molecule_id
  - Type: string
  - Description: Identifier of the molecule.
- type
  - Type: string
  - Description: Type of peak (baseline-baseline / baseline-valley / ...)
- peak_start
  - Type: float
  - Description: Start retention time of the peak
- peak_end
  - Type: float
  - Description: End retention time of the peak.
- width
  - Type: float
  - Description: Width of the peak.
- height
  - Type: float
  - Description: Height of the peak.
- percent_area
  - Type: float
  - Description: Percent area of the peak.
- tailing_factor
  - Type: float
  - Description: Tailing factor of the peak.
- separation_factor
  - Type: float
  - Description: Separation factor of the peak.

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
