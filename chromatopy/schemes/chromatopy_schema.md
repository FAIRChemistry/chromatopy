```mermaid
classDiagram
    Detector <-- TCDDetector
    Detector <-- FIDDetector
    ChromatigraphicExperiment *-- Molecule
    ChromatigraphicExperiment *-- Measurement
    ChromatigraphicExperiment *-- Method
    Molecule *-- Role
    Molecule *-- Peak
    Molecule *-- Standard
    Measurement *-- Signal
    Signal *-- SignalType
    Signal *-- Peak
    Method *-- Oven
    Method *-- Column
    Method *-- Valve
    Oven *-- Ramp
    Column *-- Inlet
    Column *-- Detector
    
    class ChromatigraphicExperiment {
        +Method method
        +Molecule molecules
        +Measurement[0..*] measurements
    }
    
    class Molecule {
        +string name
        +string inchi
        +float molecular_weight
        +float retention_time
        +Peak[0..*] peaks
        +float[0..*] concentrations
        +Standard standard
        +Role role
    }
    
    class Measurement {
        +Signal[0..*] signals
        +datetime timestamp
        +float injection_volume
        +string injection_volume_unit
    }
    
    class Signal {
        +Peak[0..*] peaks
        +SignalType type
    }
    
    class Peak {
        +float retention_time
        +string retention_time_unit
        +string type
        +float width
        +string width_unit
        +float area
        +string area_unit
        +float height
        +string height_unit
        +float percent_area
    }
    
    class Standard {
        +float factor
    }
    
    class Method {
        +float injection_time
        +string injection_date
        +float injection_volume
        +string injection_volume_unit
        +string location
        +Oven oven
        +Column[0..*] columns
        +Valve[0..*] valves
    }
    
    class Oven {
        +float init_temp
        +float max_temp
        +float equilibrate_time
        +Ramp[0..*] ramps
        +float post_temp
        +float post_time
        +float run_time
    }
    
    class Ramp {
        +float temp_rate
        +float final_temp
        +float hold_time
        +string time_unit
    }
    
    class Inlet {
        +string mode
        +float init_temp
        +float pressure
        +string pressure_unit
        +string split_ratio
        +float split_flow
        +float total_flow
        +string flow_unit
        +boolean gas_saver
        +string gas_type
    }
    
    class Column {
        +string name
        +string type
        +float max_temp
        +float length
        +float diameter
        +float film_thickness
        +string flow_mode
        +float flow_rate
        +string flow_unit
        +Inlet inlet
        +Detector detector
        +float outlet_pressure
    }
    
    class Detector {
        +string type
        +string flow_mode
        +float makeup_flow
        +string makeup_gas
        +string flow_unit
        +float reference_flow
    }
    
    class TCDDetector {
        +float hydrogen_flow
        +float air_flow
        +boolean flame
        +boolean electrometer
        +float lit_offset
    }
    
    class FIDDetector {
        +float reference_flow
        +boolean filament
        +boolean negative_polarity
    }
    
    class Valve {
        +string name
        +float loop_volume
        +float load_time
        +float inject_time
    }
    
    class SignalType {
        << Enumeration >>
        +fid
        +tcd
    }
    
    class Role {
        << Enumeration >>
        +ANALYTE
        +INTERNAL_STANDARD
    }
    
```