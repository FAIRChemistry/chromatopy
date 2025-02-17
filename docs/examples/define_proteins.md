
# Proteins

Proteins are not important for the chromatographic analysis, but they can be defined and added to the `ChromAnalyzer` object as a convenience feature. This allows to include them in the EnzymeML conversion process.

## Create a Protein

Proteins are not directly related to the measured chromatograms, but they can be defined in the same fashion as molecules. This allows to include them in the EnzymeML conversion process.

The `ChromAnalyzer` class provides two primary methods for defining proteins, and adding them to the `ChromAnalyzer` object:

- **`define_protein`**  
  This method creates a new protein object and adds it to the analyzer's internal list.

- **`add_protein`**  
  This method allows to add an already instantiated `Protein` object to the analyzer.

!!! example "Create a Protein via the `ChromAnalyzer` class"

    ```python
    my_protein = analyzer.define_protein(
        id="U12345",
        name="Protein",
    )
    ``` 

Proteins can also be created via the `Protein` class.

!!! example "Create a Protein"

    ```python
    from chromatopy import Protein

    my_protein = Protein(
        id="U12345",
        name="Protein",
    )
    ``` 

## Add a Protein

Proteins can be added to the `ChromAnalyzer` object using the `add_protein` method.

!!! example "Add a Protein"

    ```python
    analyzer.add_protein(my_protein)
    ```
