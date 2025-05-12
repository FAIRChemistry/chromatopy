# Define Molecules

Molecules in *chromatopy* represent the chemical species of interest which are associated with a characteristic retention time. When a molecule is defined, the following parameters are required:

- **`id`**: A unique, internal identifier (e.g., `"atp"` or `"s1"`).
- **`name`**: The name of the molecule.
- **`pubchem_cid`**: A unique chemical identifier from the PubChem database.

The following parameters are optional:  

- **`retention_time`**: The expected retention time in minutes that allows *chromatopy* to automatically register relevant peaks.
- **`init_conc`**: The initial concentration of the molecule at retention time `t=0`.
- **`conc_unit`**: The unit of the initial concentration.
- **`retention_tolerance`**: The tolerance for the retention time in minutes. Defaults to 0.2 minutes.
- **`wavelength`**: The wavelength at which the molecule was detected in nanometers.

!!! info "Specifying the initial concentration and concentration unit"

    The initial concentration and its unit are optional. However, if the chromatographic data is converted into an EnzymeML document, both must be specified; otherwise, the conversion will fail due to missing concentration values.


Once the molecule is defined, peaks of all chromatograms are assigned to the molecule that is at the defined retention time including a tolerance. By default the tolerance is set to 0.2 minutes. The `retention_tolerance` parameter can be specified to accommodate for shifts in the retention time.

## Create a Molecule

The `ChromAnalyzer` class provides two primary methods for defining molecules, and adding them to the `ChromAnalyzer` object:

- **`define_molecule`**  
  This method creates a new molecule object and adds it to the analyzer's internal list. If a retention time is provided, the method automatically assigns the molecule’s ID to peaks with matching retention time within a specified tolerance. The retention time tolerance defaults to 0.2 minutes.

- **`add_molecule`**  
  This method allows to add an already instantiated `Molecule` object to the analyzer. It also offers the flexibility to update properties such as the initial concentration or retention tolerance. The retention time tolerance defaults to 0.2 minutes.

!!! example "Create a Molecule via the `ChromAnalyzer` class"

    In this example a time-course series of chromatograms is read and a molecule is defined. The molecule is automatically added to the `ChromAnalyzer` object and the molecule is returned.

    ```python
    from chromatopy import ChromAnalyzer

    # Read chromatographic data
    analyzer = ChromAnalyzer.read_thermo(
        path="data/thermo",
        ph=7.4,
        temperature=25.0,
        mode="timecourse",
        values=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        unit="min",
    )

    # Define a molecule with a retention time
    ATP = analyzer.define_molecule(
        id="ATP",
        pubchem_cid=5957,
        name="ATP",
        retention_time=5.64,
        init_conc=1.0,
        conc_unit="mmol / l",
    )
    ```
    ```
    Loaded 8 chromatograms.
    🎯 Assigned ATP to 8 peaks
    ```

Besides creating a molecule via the `ChromAnalyzer` class, it is also possible to create a molecule via the `Molecule` class. In this case the molecule is not added to the `ChromAnalyzer` object and the molecule object is returned.

!!! example "Create a Molecule"

    ```python
    from chromatopy import Molecule

    ADP = Molecule(
        id="ADP",
        pubchem_cid=7058055,
        name="ADP",
        retention_time=1.7,
    )
    ```

## Add a Molecule

Using the `add_molecule` method, an existing molecule can be added to the `ChromAnalyzer` object. In this process the `init_conc` and `conc_unit` parameters can be updated.

!!! example "Add a Molecule"

    Here the previously created molecule is added to the `ChromAnalyzer` object, and the initial concentration is updated.

    ```python
    analyzer.add_molecule(ADP, init_conc=4.5, conc_unit="mmol / l")
    ```
    ```
    🎯 Assigned ADP to 8 peaks
    ```