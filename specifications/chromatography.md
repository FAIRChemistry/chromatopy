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

## Objects describing the method

### Method

- injection_time
  - Type: float
  - Description: Injection time
- injection_date
  - Type: string
  - Description: Injection date
- injection_volume
  - Type: float
  - Description: Injection volume
- injection_volume_unit
  - Type: Unit
  - Description: Unit of injection volume
- location
  - Type: string
  - Description: Location of sample vial
- oven
  - Type: Oven
  - Description: Settings of the oven
- columns
  - Type: Column
  - Description: Parameters of the columns
  - Multiple: True
- valves
  - Type: Valve
  - Description: Settings of the valves
  - Multiple: True

### Oven

Describes the settings of the oven.

- init_temp
  - Type: float
  - Description: Initial temperature of the oven
- max_temp
  - Type: float
  - Description: Maximum temperature of the oven
- equilibrate_time
  - Type: float
  - Description: Time to equilibrate the oven
- ramps
  - Type: Ramp
  - Description: Thermal protocols of the oven
  - Multiple: True
- post_temp
  - Type: float
  - Description: Temperature after protocol
- post_time
  - Type: float
  - Description: Time after protocol
- run_time
  - Type: float
  - Description: Duration of the run

### Ramp

Describes properties of a temperature ramp.

- temp_rate
  - Type: float
  - Description: Rate of temperature change during the ramp
- final_temp
  - Type: float
  - Description: Final temperature of the ramp
- hold_time
  - Type: float
  - Description: Duration to hold the final temperature before starting the next ramp
- time_unit
  - Type: Unit
  - Description: Unit of time

### Inlet

- mode
  - Type: string
  - Description: Mode of the inlet (Split / Splitless)
- init_temp
  - Type: float
  - Description: Initial temperature
- pressure
  - Type: float
  - Description: Inlet pressure
- pressure_unit
  - Type: Unit
  - Description: Unit of pressure
- split_ratio
  - Type: string
  - Description: Split ratio
  - regex: (d+)(:)(d+)
- split_flow
  - Type: float
  - Description: Split flow
- total_flow
  - Type: float
  - Description: Total flow
- flow_unit
  - Type: Unit
  - Description: Unit of flow
- gas_saver
  - Type: boolean
  - Description: Gas saver mode
- gas_type
  - Type: string
  - Description: Type of gas

### Column

Describes properties of a column and its connections to the inlet and detector.

- name
  - Type: string
  - Description: Name of the column
- type
  - Type: string
  - Description: Type of column
- max_temp
  - Type: float
  - Description: Maximum temperature of the column
- length
  - Type: float
  - Description: Length of the column
- diameter
  - Type: float
  - Description: Diameter of the column
- film_thickness
  - Type: float
  - Description: Film thickness of the column
- flow_mode
  - Type: string
  - Description: Flow mode of the column
- flow_rate
  - Type: float
  - Description: Flow rate of the column
- flow_unit
  - Type: Unit
  - Description: Unit of flow rate
- inlet
  - Type: Inlet
  - Description: Inlet of the column
- detector
  - Type: Detector
  - Description: Outlet of the column, connected to the detector
- outlet_pressure
  - Type: float
  - Description: Outlet pressure of the column

### Detector

Base class for detectors.

- type
  - Type: string
  - Description: Type of detector
- flow_mode
  - Type: string
  - Description: Airflow mode
- makeup_flow
  - Type: float
  - Description: Makeup flow
- makeup_gas
  - Type: string
  - Description: Makeup gas
- flow_unit
  - Type: Unit
  - Description: Unit of flow
- reference_flow
  - Type: float
  - Description: Reference flow

### TCDDetector [_Detector_]

Describes properties of a thermal conductivity detector.

- hydrogen_flow
  - Type: float
  - Description: Hydrogen flow
- air_flow
  - Type: float
  - Description: Airflow
- flame
  - Type: boolean
  - Description: Flame on/off
- electrometer
  - Type: boolean
  - Description: Electrometer on/off
- lit_offset
  - Type: float
  - Description: Lit offset

### FIDDetector [_Detector_]

Describes properties of a flame ionization detector.

- reference_flow
  - Type: float
  - Description: Reference flow
- filament
  - Type: boolean
  - Description: Filament on/off
- negative_polarity
  - Type: boolean
  - Description: Negative polarity on/off

### Valve

- name
  - Type: string
  - Description: Name of the valve
- loop_volume
  - Type: float
  - Description: Loop volume of the valve
- load_time
  - Type: float
  - Description: Load time
- inject_time
  - Type: float
  - Description: Inject time

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
