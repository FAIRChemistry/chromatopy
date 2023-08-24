# HPLC data model

## Objects

### HPLCExperiment

- method
    - Type: Method
    - Description: Description of the HPLC method
- molecules
    - Type: Molecule
    - Description: Molecule which can be assigned to a peak. 
- measurements
    - Type: Measurement
    - Description: Measured signals
    - Multiple: True

### Molecule

- name
    - Type: string
    - Description: Molecule name
- inchi
    - Type: string
    - Description: Inchi code of the molecule
- molecular_weight
    - Type: float
    - Description: Molar weight of the molecule in g/mol
- retention_time
    - Type: float
    - Description: Approximated retention time of the molecule
- times
    - Type: datetime
    - Multiple: True
    - Description: Time points when the molecule concentration was measured
- peaks
    - Type: Peak
    - Multiple: True
    - Description: All peaks of the dataset which are within the same retention time interval
- concentrations
    - Type: float
    - Multiple: True
    - Description: Concentration of the molecule
- standard
    - Type: Standard
    - Description: Standard, describing the signal to concentration relationship
- role
    - Type: Role
    - Description: Role of the molecule in the experiment

### Standard

- concentration
    - Type: float
    - Multiple: True
    - Description: Concentration 
- signal
    - Type: float
    - Multiple: True
    - Description: Signal corresponding to concentration 
- concentration_unit
    - Type: string
    - Description: Concentration 

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
    - Type: string
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

Describes settings of the oven.

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
    - Type: string
    - Description: Unit of time

### Inlet

- mode
    - Type: string
    - Description: Mode of the inlet (Split/Splitless)
- init_temp
    - Type: float
    - Description: Initial temperature
- pressure
    - Type: float
    - Description: Inlet pressure
- pressure_unit
    - Type: string
    - Description: Unit of pressure
- split_ratio
    - Type: string
    - Description: Split ratio
    - regex: (\d+)(:)(\d+)
- split_flow
    - Type: float
    - Description: Split flow
- total_flow
    - Type: float
    - Description: Total flow
- flow_unit
    - Type: string
    - Description: Unit of flow
- gas_saver
    - Type: boolean
    - Description: Gas saver mode
- gas_type
    - Type: string
    - Description: Type of gas

### Column

Descibes properties of a column and its connections to the inlet and detector.

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
    - Type: string
    - Description: Unit of flow rate
- inlet
    - Type: Inlet
    - Description: Inlet of the column
- detector
    - Type: Detector
    - Description: Outlet of the column, connected to detector
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
    - Description: Air flow mode
- makeup_flow
    - Type: float
    - Description: Makeup flow
- makeup_gas
    - Type: string
    - Description: Makeup gas
- flow_unit
    - Type: string
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
    - Description: Air flow
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

### Measurement

- signals
    - Type: Signal
    - Description: Measured signal
    - Multiple: True
- timestamp
    - Type: datetime
    - Description: Timestamp of sample injection into the column
- injection_volume
    - Type: float
    - Description: Injection volume
- injection_volume_unit
    - Type: string
    - Description: Unit of injection volume

### Signal

- peaks
    - Type: Peak
    - Description: Peaks in the signal
    - Multiple: True
- type
    - Type: SignalType
    - Description: Type of signal 

### Peak

- retention_time
    - Type: float
    - Description: Retention time of the peak
- retention_time_unit
    - Type: string
    - Description: Unit of retention time
- type
    - Type: string
    - Description: Type of peak (baseline-baseline / baseline-valey / ...)
- width
    - Type: float
    - Description: Width of the peak
- width_unit
    - Type: string
    - Description: Unit of width
- area
    - Type: float
    - Description: Area of the peak
- area_unit
    - Type: string
    - Description: Unit of area
- height
    - Type: float
    - Description: Height of the peak
- height_unit
    - Type: string
    - Description: Unit of height
- percent_area
    - Type: float
    - Description: Percent area of the peak

## Enumerations

### SignalType

```python
fid = "fid"
tcd = "tcd"
```

## Enumerations

### Role

```python
ANALYTE = "analyte"
INTERNAL_STANDARD = "internal_standard"
```