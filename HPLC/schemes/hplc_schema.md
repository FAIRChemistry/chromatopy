```mermaid
classDiagram
    Detector <-- TCDDetector
    Detector <-- FIDDetector
    HPLCExperiment *-- Method
    HPLCExperiment *-- Signal
    Method *-- Oven
    Method *-- Column
    Method *-- Valve
    Oven *-- Ramp
    Column *-- Inlet
    Column *-- Detector
    Signal *-- SignalType
    Signal *-- Peak
    
    class HPLCExperiment {
        +Method[0..*] methods
        +Signal[0..*] signals
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
    
    class SignalType {
        << Enumeration >>
        +FID
        +TCD
    }
    
```