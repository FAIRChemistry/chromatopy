# 🏔️ Assign Peaks 

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/FAIRChemistry/chromatopy/blob/update-sdrdm/docs/examples/peak_assignment.ipynb)

---

The `ChromAnalyzer` class in the `chromatopy` library provides several methods for adding and defining molecules, that allow later extraction and processing of the data. Information on a molecule is defined in regards of the intend of the measurement. This means that besides a molecule's name, its retention time, also the initial concentration and the respective unit are added for time-course measurements.

Molecules are defined using the `define_molecule` method. It adds a molecule to the list of molecules within the `ChromAnalyzer` object. This method requires several parameters, including the internal identifier, PubChem CID, and retention time, among others.

__Required parameters__:

- `id`: Internal identifier of the molecule, such as `s0`, `ABTS` or `A0_34S`.
- `pubchem_cid`: PubChem CID of the molecule.
- `retention_time`: Retention time for peak annotation in minutes.

__Optional parameters__:

- `init_conc`: Initial concentration of the molecule. Defaults to `None`
- `conc_unit`: Unit of the concentration. Defaults to `None`.
- `name`: Name of the molecule. If not provided, the name is retrieved from the PubChem database. Defaults to `None`.
- `retention_tolerance`: Retention time tolerance for peak annotation in minutes. Defaults to `0.1`.
- `wavelength`: Wavelength of the detector on which the molecule was detected. Defaults to `None`.

__Returns__:

- The method returns a `Molecule` object that is added to the `molecules` list within the `ChromAnalyzer` object.

??? info "How it works"

    Once the molecule is defined, all peaks within the chromatographic data that match the retention time within the specified tolerance are annotated with the molecule's `id`, hence allowing for further analysis and processing of the data. This happens in the background. In the following assignment of a substrate and product molecule of a kinetic measurement is shown.

## Kinetic Measurements

### Define Molecules

Consider the following cascade reaction, where molecules measurable by chromatography are highlighted in purple:

```mermaid
graph LR
  A[<b>n1-triphosphate</b><br>2.5 mM] --> C{<i>MjMAT</i><br>0.05 mM};

  B[<b>y-Hcy</b><br>5 mM] --> C
  style C stroke-width:2px,fill:transparent,stroke:#000
  
  C --> D[<b>n1y</b>]
  style D fill:transparent,stroke:#000,stroke-width:2px;

  D --> E{<i>RnCOMT</i><br>0.05 mM};
  style E stroke-width:2px,fill:transparent,stroke:#000

  DHBAL[<b>DHBAL</b><br>0.3 mM] --> E

  E --> F[<b>O<sup>3</sup>-modified DHBAL</b>] & G[<b><i>S</i>-adenosyl-<i>L</i>-homocysteine analogue</b>]

  style G fill:transparent,stroke:#000,stroke-width:2px;
```


This cascade reaction involves two enzymatic steps. In the first step, the enzyme <span style="font-style: italic;">MjMAT</span> catalyzes the conversion of <span style="font-style: italic;">N<sup>6</sup>-benzyl-ATP</span> (`n1_triphosphate`) and <span style="font-style: italic;">ortho-nitrobenzyl-DL-homocysteine</span> (`y_Hcy`) into an AdoONB analogue (`n1y`). In the second step, the enzyme <span style="font-style: italic;">RnCOMT</span> further processes `n1y` and <span style="font-style: italic;">3,4-dihydroxybenzaldehyde</span> (`DHBAL`) to produce a modified <span style="font-style: italic;">O<sup>3</sup>-DHBAL</span> (`DHBAL_modified`) and an <span style="font-style: italic;">S-adenosyl-L-homocysteine analogue</span>.

The following retention times are known:

| Molecule            | Retention Time [min] |
|---------------------|--------------------------|
| `n1_triphosphate`   | 13.9                     |
| `y_Hcy`             | 15.7                     |
| `DHBAL`             | 12.6                     |
| `DHBAL_modified`    | 23.2           |

The `ChromAnalyzer` allows for the annotation of peaks corresponding to these reactants and products. The following code snippet demonstrates how to define the substrates and products for each recorded chromatogram at reaction time points of 0, 0.5, 2, and 6 hours after the reaction start.

!!! example

    ```python
    from chromatopy import ChromAnalyzer
    from chromatopy.units import mM

    # Read the data
    data_dir = "data/asm"
    cascade_analyzer = ChromAnalyzer.read_asm(
        path=data_dir,
        ph=7.4,
        temperature=25,
    )

    # Define N6-benzyl-ATP
    n1_triphosphate = cascade_analyzer.define_molecule(
        pubchem_cid=127255957,
        id="n1_triphosphate",
        name="N6-benzyl-ATP",
        retention_time=13.9,
        init_conc=2.5,
        conc_unit=mM,
    )

    # Define ortho-nitrobenzyl-DL-homocysteine
    y_Hcy = cascade_analyzer.define_molecule(
        pubchem_cid=-1,
        id="y_Hcy",
        name="ortho-nitrobenzyl-DL-homocysteine",
        retention_time=15.7,
        init_conc=5,
        conc_unit=mM,
    )

    # Define AdoONB analogue
    DHBAL = cascade_analyzer.define_molecule(
        pubchem_cid=8768,
        id="n1y",
        name="DHBAL",
        retention_time=12.6,
        init_conc=0,
        conc_unit=mM,
    )

    DHBAL_modified = cascade_analyzer.define_molecule(
        pubchem_cid=-1,
        id="DHBAL_O3",
        name="DHBAL O3",
        retention_time=23.21,
        init_conc=0,
        conc_unit=mM,
    )
    ```
    ```
    ✅ Loaded 4 chromatograms.
    🎯 Assigned N6-benzyl-ATP to 4 peaks
    🎯 Assigned ortho-nitrobenzyl-DL-homocysteine to 4 peaks
    🎯 Assigned DHBAL to 3 peaks
    🎯 Assigned DHBAL O3 to 3 peaks
    ```

To verify the correct assignment of molecules to their respective peaks, use the `visualize_all` method and setting `assigned_only=True`, ensuring that only the peaks are annotated correctly. If not, and the peaks are for instance shifting, the `retention_tolerance` can be  increased during peak definition to allow for a wider retention time range of be annotated to one molecule.

!!! example

    ```python
    cascade_analyzer.visualize_all(assigned_only=True, dark_mode=True)
    ```

    ```plotly
    ```

### Define Proteins

The `ChromAnalyzer` class also allows to define information on the used catalysts, such as UniProt ID, name, intial concentration and unit along other parameters. In the following example the protein `MjMAT` is added to the `cascade_analyzer` object.

__Required parameters__:
- `id`: Internal identifier of the protein, such as `p0`, `MyProt1`, or `Protein_X`.
- `name`: Name of the protein.
- `init_conc`: Initial concentration of the protein in the sample.
- `conc_unit`: Unit of the concentration, for example, `mM` or `µM`.

__Optional parameters__:
- `sequence`: Amino acid sequence of the protein. This parameter is optional and can be omitted if the sequence is not available. Defaults to `None`.
- `organism`: Name of the organism from which the protein is derived. This is also optional and defaults to `None` if not provided.
- `organism_tax_id`: NCBI taxonomy ID of the organism. This is an optional parameter and can be omitted if the taxonomy ID is not known. Defaults to `None`.
- `constant`: A boolean flag indicating whether the protein concentration is constant throughout the experiment. If set to `True`, the concentration is assumed to remain constant. This parameter defaults to `True`.

!!! example

    ```python
    cascade_analyzer.define_protein(
        id="MjMAT",
        name="MjMAT",
        init_conc=0.05,
        conc_unit=mM,
    )
    ```


## Calibration measurements

### External Standard

#### Linear Model

Besides kinetic data, the `ChromAnalyzer` can also be used to analyze calibration measurements and create standards for the quantification of molecules. 
The `add_standard` method adds fits a linear regression to the peaks which are assigned to a molecule and the provided concentrations.

__Required parameters__:
- `molecule`: The molecule for which the standard curve is being generated. This should be an instance of a molecule previously defined in the system.
- `concs`: A list of concentrations at which the standard molecule is measured. For example, `[0.5, 1, 1.5, 2, 2.5, 3]` represents six different concentrations. The order of the concentrations should match the alphabetical order of the imported chromatograms.
- `conc_unit`: The unit of concentration for the specified concentrations.

__Optional parameters__:
- `visualize`: A boolean parameter that, if set to `True`, generates a plot of the standard curve for visualization. This is useful for confirming the accuracy of the calibration process.

??? info "How it works"
    Upon calling the `add_standard` method, the provided concentrations (`concs`) of the `molecule` are used to generate a standard curve through linear regression. The linear relationship between the concentration of $\text{Ana}$ and its peak area is defined by the equation:

    $$
    A_{\text{Ana}} = a \times C_{\text{Ana}}
    $$

    Where:

    - **$A_{\text{Ana}}$**: Peak area of $\text{Ana}$.
    - **$C_{\text{Ana}}$**: Concentration of $\text{Ana}$.
    - **$a$**: Slope of the calibration curve, representing the sensitivity or response factor of $\text{Ana}$.

    The linear model including information on the valid calibration range is stored in the `standarad` attribute of the `Molecule` object and can later be used for quantification of the molecule from time-course measurements.

!!! example

    ```python
    from chromatopy import ChromAnalyzer

    calib_analyzer = ChromAnalyzer.from_json("data/instances/adenosine_analyzer.json")

    # Define adenosine
    adenosine = calib_analyzer.define_molecule(
        pubchem_cid=60961,
        id="ADE",
        name="adenosine",
        retention_time=10.9,
        retention_tolerance=0.5,
    )

    # create a standard curve
    concs = [0.5, 1, 1.5, 2, 2.5, 3]

    standard = calib_analyzer.add_standard(
        molecule=adenosine,
        concs=concs,
        conc_unit=mM,
        visualize=True,
    )
    ```
    ```
    🎯 Assigned adenosine to 6 peaks
    ✅ Models have been successfully fitted.
    ```



    | **Model Name** | **AIC** | **R squared** | **RMSD**  | **Equation** | **Relative Parameter Standard Errors** |
    |:--------------:|:-------:|:------------:|:---------:|:------------:|:----------------------------------------:|
    | linear         | 84      | 0.9997       | 918.2705  | ADE * a      | a: 0.3%                                 |

    ```plotly
    {
        "data": [
            {
                "customdata": [
                    "adenosine standard"
                ],
                "marker": {
                    "color": "#000000"
                },
                "mode": "markers",
                "name": "adenosine",
                "visible": true,
                "x": [
                    0.5,
                    1.0,
                    1.5,
                    2.0,
                    2.5,
                    3.0
                ],
                "y": [
                    34221.52533999663,
                    63792.860674890384,
                    97798.69806281955,
                    129562.76503983978,
                    163134.2329051491,
                    195257.53514179704
                ],
                "type": "scatter",
                "xaxis": "x",
                "yaxis": "y",
                "hovertemplate": "Signal: %{y:.2f}"
            },
            {
                "customdata": [
                    "linear model"
                ],
                "marker": {
                    "color": "#636EFA"
                },
                "mode": "lines",
                "name": "linear model",
                "visible": false,
                "x": [
                    0.0,
                    0.030303030303030304,
                    0.06060606060606061,
                    0.09090909090909091,
                    0.12121212121212122,
                    0.15151515151515152,
                    0.18181818181818182,
                    0.21212121212121213,
                    0.24242424242424243,
                    0.2727272727272727,
                    0.30303030303030304,
                    0.33333333333333337,
                    0.36363636363636365,
                    0.3939393939393939,
                    0.42424242424242425,
                    0.4545454545454546,
                    0.48484848484848486,
                    0.5151515151515151,
                    0.5454545454545454,
                    0.5757575757575758,
                    0.6060606060606061,
                    0.6363636363636364,
                    0.6666666666666667,
                    0.696969696969697,
                    0.7272727272727273,
                    0.7575757575757576,
                    0.7878787878787878,
                    0.8181818181818182,
                    0.8484848484848485,
                    0.8787878787878788,
                    0.9090909090909092,
                    0.9393939393939394,
                    0.9696969696969697,
                    1.0,
                    1.0303030303030303,
                    1.0606060606060606,
                    1.0909090909090908,
                    1.1212121212121213,
                    1.1515151515151516,
                    1.1818181818181819,
                    1.2121212121212122,
                    1.2424242424242424,
                    1.2727272727272727,
                    1.303030303030303,
                    1.3333333333333335,
                    1.3636363636363638,
                    1.393939393939394,
                    1.4242424242424243,
                    1.4545454545454546,
                    1.4848484848484849,
                    1.5151515151515151,
                    1.5454545454545454,
                    1.5757575757575757,
                    1.6060606060606062,
                    1.6363636363636365,
                    1.6666666666666667,
                    1.696969696969697,
                    1.7272727272727273,
                    1.7575757575757576,
                    1.7878787878787878,
                    1.8181818181818183,
                    1.8484848484848486,
                    1.878787878787879,
                    1.9090909090909092,
                    1.9393939393939394,
                    1.9696969696969697,
                    2.0,
                    2.0303030303030303,
                    2.0606060606060606,
                    2.090909090909091,
                    2.121212121212121,
                    2.1515151515151514,
                    2.1818181818181817,
                    2.2121212121212124,
                    2.2424242424242427,
                    2.272727272727273,
                    2.303030303030303,
                    2.3333333333333335,
                    2.3636363636363638,
                    2.393939393939394,
                    2.4242424242424243,
                    2.4545454545454546,
                    2.484848484848485,
                    2.515151515151515,
                    2.5454545454545454,
                    2.5757575757575757,
                    2.606060606060606,
                    2.6363636363636362,
                    2.666666666666667,
                    2.6969696969696972,
                    2.7272727272727275,
                    2.757575757575758,
                    2.787878787878788,
                    2.8181818181818183,
                    2.8484848484848486,
                    2.878787878787879,
                    2.909090909090909,
                    2.9393939393939394,
                    2.9696969696969697,
                    3.0
                ],
                "y": [
                    0.0,
                    1971.8087089005212,
                    3943.6174178010424,
                    5915.426126701564,
                    7887.234835602085,
                    9859.043544502607,
                    11830.852253403127,
                    13802.66096230365,
                    15774.46967120417,
                    17746.27838010469,
                    19718.087089005214,
                    21689.895797905734,
                    23661.704506806254,
                    25633.513215706775,
                    27605.3219246073,
                    29577.13063350782,
                    31548.93934240834,
                    33520.74805130886,
                    35492.55676020938,
                    37464.36546910991,
                    39436.17417801043,
                    41407.98288691094,
                    43379.79159581147,
                    45351.60030471199,
                    47323.40901361251,
                    49295.21772251303,
                    51267.02643141355,
                    53238.83514031408,
                    55210.6438492146,
                    57182.45255811511,
                    59154.26126701564,
                    61126.06997591616,
                    63097.87868481668,
                    65069.6873937172,
                    67041.49610261772,
                    69013.30481151823,
                    70985.11352041876,
                    72956.92222931929,
                    74928.73093821981,
                    76900.53964712033,
                    78872.34835602086,
                    80844.15706492137,
                    82815.96577382188,
                    84787.77448272241,
                    86759.58319162294,
                    88731.39190052346,
                    90703.20060942398,
                    92675.0093183245,
                    94646.81802722502,
                    96618.62673612554,
                    98590.43544502606,
                    100562.24415392657,
                    102534.0528628271,
                    104505.86157172763,
                    106477.67028062815,
                    108449.47898952867,
                    110421.2876984292,
                    112393.09640732971,
                    114364.90511623022,
                    116336.71382513075,
                    118308.52253403128,
                    120280.3312429318,
                    122252.13995183232,
                    124223.94866073284,
                    126195.75736963336,
                    128167.56607853388,
                    130139.3747874344,
                    132111.1834963349,
                    134082.99220523544,
                    136054.80091413597,
                    138026.60962303646,
                    139998.418331937,
                    141970.22704083752,
                    143942.03574973808,
                    145913.84445863857,
                    147885.6531675391,
                    149857.46187643963,
                    151829.27058534013,
                    153801.07929424066,
                    155772.88800314118,
                    157744.6967120417,
                    159716.5054209422,
                    161688.31412984274,
                    163660.12283874326,
                    165631.93154764376,
                    167603.7402565443,
                    169575.54896544482,
                    171547.35767434535,
                    173519.16638324587,
                    175490.9750921464,
                    177462.78380104693,
                    179434.59250994743,
                    181406.40121884795,
                    183378.20992774848,
                    185350.018636649,
                    187321.8273455495,
                    189293.63605445003,
                    191265.44476335056,
                    193237.2534722511,
                    195209.0621811516
                ],
                "type": "scatter",
                "xaxis": "x",
                "yaxis": "y",
                "hovertemplate": "Signal: %{y:.2f}"
            },
            {
                "customdata": [
                    "linear model"
                ],
                "hoverinfo": "skip",
                "marker": {
                    "color": "#636EFA"
                },
                "mode": "markers",
                "name": "Residuals",
                "visible": false,
                "x": [
                    0.5,
                    1.0,
                    1.5,
                    2.0,
                    2.5,
                    3.0
                ],
                "y": [
                    -1686.681643138032,
                    1276.8267188268146,
                    -194.16697224375093,
                    576.6097475946153,
                    -460.0144208561105,
                    -48.47296064544935
                ],
                "type": "scatter",
                "xaxis": "x2",
                "yaxis": "y2",
                "hovertemplate": "Signal: %{y:.2f}"
            },
            {
                "customdata": [
                    "linear model"
                ],
                "line": {
                    "color": "grey",
                    "dash": "dash",
                    "width": 2
                },
                "showlegend": false,
                "visible": true,
                "x": [
                    0.5,
                    1.0,
                    1.5,
                    2.0,
                    2.5,
                    3.0
                ],
                "y": [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0
                ],
                "type": "scatter",
                "xaxis": "x2",
                "yaxis": "y2",
                "hovertemplate": "Signal: %{y:.2f}"
            }
        ],
        "layout": {
            "template": {
                "data": {
                    "barpolar": [
                        {
                            "marker": {
                                "line": {
                                    "color": "white",
                                    "width": 0.5
                                },
                                "pattern": {
                                    "fillmode": "overlay",
                                    "size": 10,
                                    "solidity": 0.2
                                }
                            },
                            "type": "barpolar"
                        }
                    ],
                    "bar": [
                        {
                            "error_x": {
                                "color": "rgb(36,36,36)"
                            },
                            "error_y": {
                                "color": "rgb(36,36,36)"
                            },
                            "marker": {
                                "line": {
                                    "color": "white",
                                    "width": 0.5
                                },
                                "pattern": {
                                    "fillmode": "overlay",
                                    "size": 10,
                                    "solidity": 0.2
                                }
                            },
                            "type": "bar"
                        }
                    ],
                    "carpet": [
                        {
                            "aaxis": {
                                "endlinecolor": "rgb(36,36,36)",
                                "gridcolor": "white",
                                "linecolor": "white",
                                "minorgridcolor": "white",
                                "startlinecolor": "rgb(36,36,36)"
                            },
                            "baxis": {
                                "endlinecolor": "rgb(36,36,36)",
                                "gridcolor": "white",
                                "linecolor": "white",
                                "minorgridcolor": "white",
                                "startlinecolor": "rgb(36,36,36)"
                            },
                            "type": "carpet"
                        }
                    ],
                    "choropleth": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "type": "choropleth"
                        }
                    ],
                    "contourcarpet": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "type": "contourcarpet"
                        }
                    ],
                    "contour": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "colorscale": [
                                [
                                    0.0,
                                    "#440154"
                                ],
                                [
                                    0.1111111111111111,
                                    "#482878"
                                ],
                                [
                                    0.2222222222222222,
                                    "#3e4989"
                                ],
                                [
                                    0.3333333333333333,
                                    "#31688e"
                                ],
                                [
                                    0.4444444444444444,
                                    "#26828e"
                                ],
                                [
                                    0.5555555555555556,
                                    "#1f9e89"
                                ],
                                [
                                    0.6666666666666666,
                                    "#35b779"
                                ],
                                [
                                    0.7777777777777778,
                                    "#6ece58"
                                ],
                                [
                                    0.8888888888888888,
                                    "#b5de2b"
                                ],
                                [
                                    1.0,
                                    "#fde725"
                                ]
                            ],
                            "type": "contour"
                        }
                    ],
                    "heatmapgl": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "colorscale": [
                                [
                                    0.0,
                                    "#440154"
                                ],
                                [
                                    0.1111111111111111,
                                    "#482878"
                                ],
                                [
                                    0.2222222222222222,
                                    "#3e4989"
                                ],
                                [
                                    0.3333333333333333,
                                    "#31688e"
                                ],
                                [
                                    0.4444444444444444,
                                    "#26828e"
                                ],
                                [
                                    0.5555555555555556,
                                    "#1f9e89"
                                ],
                                [
                                    0.6666666666666666,
                                    "#35b779"
                                ],
                                [
                                    0.7777777777777778,
                                    "#6ece58"
                                ],
                                [
                                    0.8888888888888888,
                                    "#b5de2b"
                                ],
                                [
                                    1.0,
                                    "#fde725"
                                ]
                            ],
                            "type": "heatmapgl"
                        }
                    ],
                    "heatmap": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "colorscale": [
                                [
                                    0.0,
                                    "#440154"
                                ],
                                [
                                    0.1111111111111111,
                                    "#482878"
                                ],
                                [
                                    0.2222222222222222,
                                    "#3e4989"
                                ],
                                [
                                    0.3333333333333333,
                                    "#31688e"
                                ],
                                [
                                    0.4444444444444444,
                                    "#26828e"
                                ],
                                [
                                    0.5555555555555556,
                                    "#1f9e89"
                                ],
                                [
                                    0.6666666666666666,
                                    "#35b779"
                                ],
                                [
                                    0.7777777777777778,
                                    "#6ece58"
                                ],
                                [
                                    0.8888888888888888,
                                    "#b5de2b"
                                ],
                                [
                                    1.0,
                                    "#fde725"
                                ]
                            ],
                            "type": "heatmap"
                        }
                    ],
                    "histogram2dcontour": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "colorscale": [
                                [
                                    0.0,
                                    "#440154"
                                ],
                                [
                                    0.1111111111111111,
                                    "#482878"
                                ],
                                [
                                    0.2222222222222222,
                                    "#3e4989"
                                ],
                                [
                                    0.3333333333333333,
                                    "#31688e"
                                ],
                                [
                                    0.4444444444444444,
                                    "#26828e"
                                ],
                                [
                                    0.5555555555555556,
                                    "#1f9e89"
                                ],
                                [
                                    0.6666666666666666,
                                    "#35b779"
                                ],
                                [
                                    0.7777777777777778,
                                    "#6ece58"
                                ],
                                [
                                    0.8888888888888888,
                                    "#b5de2b"
                                ],
                                [
                                    1.0,
                                    "#fde725"
                                ]
                            ],
                            "type": "histogram2dcontour"
                        }
                    ],
                    "histogram2d": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "colorscale": [
                                [
                                    0.0,
                                    "#440154"
                                ],
                                [
                                    0.1111111111111111,
                                    "#482878"
                                ],
                                [
                                    0.2222222222222222,
                                    "#3e4989"
                                ],
                                [
                                    0.3333333333333333,
                                    "#31688e"
                                ],
                                [
                                    0.4444444444444444,
                                    "#26828e"
                                ],
                                [
                                    0.5555555555555556,
                                    "#1f9e89"
                                ],
                                [
                                    0.6666666666666666,
                                    "#35b779"
                                ],
                                [
                                    0.7777777777777778,
                                    "#6ece58"
                                ],
                                [
                                    0.8888888888888888,
                                    "#b5de2b"
                                ],
                                [
                                    1.0,
                                    "#fde725"
                                ]
                            ],
                            "type": "histogram2d"
                        }
                    ],
                    "histogram": [
                        {
                            "marker": {
                                "line": {
                                    "color": "white",
                                    "width": 0.6
                                }
                            },
                            "type": "histogram"
                        }
                    ],
                    "mesh3d": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "type": "mesh3d"
                        }
                    ],
                    "parcoords": [
                        {
                            "line": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "parcoords"
                        }
                    ],
                    "pie": [
                        {
                            "automargin": true,
                            "type": "pie"
                        }
                    ],
                    "scatter3d": [
                        {
                            "line": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scatter3d"
                        }
                    ],
                    "scattercarpet": [
                        {
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scattercarpet"
                        }
                    ],
                    "scattergeo": [
                        {
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scattergeo"
                        }
                    ],
                    "scattergl": [
                        {
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scattergl"
                        }
                    ],
                    "scattermapbox": [
                        {
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scattermapbox"
                        }
                    ],
                    "scatterpolargl": [
                        {
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scatterpolargl"
                        }
                    ],
                    "scatterpolar": [
                        {
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scatterpolar"
                        }
                    ],
                    "scatter": [
                        {
                            "fillpattern": {
                                "fillmode": "overlay",
                                "size": 10,
                                "solidity": 0.2
                            },
                            "type": "scatter"
                        }
                    ],
                    "scatterternary": [
                        {
                            "marker": {
                                "colorbar": {
                                    "outlinewidth": 1,
                                    "tickcolor": "rgb(36,36,36)",
                                    "ticks": "outside"
                                }
                            },
                            "type": "scatterternary"
                        }
                    ],
                    "surface": [
                        {
                            "colorbar": {
                                "outlinewidth": 1,
                                "tickcolor": "rgb(36,36,36)",
                                "ticks": "outside"
                            },
                            "colorscale": [
                                [
                                    0.0,
                                    "#440154"
                                ],
                                [
                                    0.1111111111111111,
                                    "#482878"
                                ],
                                [
                                    0.2222222222222222,
                                    "#3e4989"
                                ],
                                [
                                    0.3333333333333333,
                                    "#31688e"
                                ],
                                [
                                    0.4444444444444444,
                                    "#26828e"
                                ],
                                [
                                    0.5555555555555556,
                                    "#1f9e89"
                                ],
                                [
                                    0.6666666666666666,
                                    "#35b779"
                                ],
                                [
                                    0.7777777777777778,
                                    "#6ece58"
                                ],
                                [
                                    0.8888888888888888,
                                    "#b5de2b"
                                ],
                                [
                                    1.0,
                                    "#fde725"
                                ]
                            ],
                            "type": "surface"
                        }
                    ],
                    "table": [
                        {
                            "cells": {
                                "fill": {
                                    "color": "rgb(237,237,237)"
                                },
                                "line": {
                                    "color": "white"
                                }
                            },
                            "header": {
                                "fill": {
                                    "color": "rgb(217,217,217)"
                                },
                                "line": {
                                    "color": "white"
                                }
                            },
                            "type": "table"
                        }
                    ]
                },
                "layout": {
                    "annotationdefaults": {
                        "arrowhead": 0,
                        "arrowwidth": 1
                    },
                    "autotypenumbers": "strict",
                    "coloraxis": {
                        "colorbar": {
                            "outlinewidth": 1,
                            "tickcolor": "rgb(36,36,36)",
                            "ticks": "outside"
                        }
                    },
                    "colorscale": {
                        "diverging": [
                            [
                                0.0,
                                "rgb(103,0,31)"
                            ],
                            [
                                0.1,
                                "rgb(178,24,43)"
                            ],
                            [
                                0.2,
                                "rgb(214,96,77)"
                            ],
                            [
                                0.3,
                                "rgb(244,165,130)"
                            ],
                            [
                                0.4,
                                "rgb(253,219,199)"
                            ],
                            [
                                0.5,
                                "rgb(247,247,247)"
                            ],
                            [
                                0.6,
                                "rgb(209,229,240)"
                            ],
                            [
                                0.7,
                                "rgb(146,197,222)"
                            ],
                            [
                                0.8,
                                "rgb(67,147,195)"
                            ],
                            [
                                0.9,
                                "rgb(33,102,172)"
                            ],
                            [
                                1.0,
                                "rgb(5,48,97)"
                            ]
                        ],
                        "sequential": [
                            [
                                0.0,
                                "#440154"
                            ],
                            [
                                0.1111111111111111,
                                "#482878"
                            ],
                            [
                                0.2222222222222222,
                                "#3e4989"
                            ],
                            [
                                0.3333333333333333,
                                "#31688e"
                            ],
                            [
                                0.4444444444444444,
                                "#26828e"
                            ],
                            [
                                0.5555555555555556,
                                "#1f9e89"
                            ],
                            [
                                0.6666666666666666,
                                "#35b779"
                            ],
                            [
                                0.7777777777777778,
                                "#6ece58"
                            ],
                            [
                                0.8888888888888888,
                                "#b5de2b"
                            ],
                            [
                                1.0,
                                "#fde725"
                            ]
                        ],
                        "sequentialminus": [
                            [
                                0.0,
                                "#440154"
                            ],
                            [
                                0.1111111111111111,
                                "#482878"
                            ],
                            [
                                0.2222222222222222,
                                "#3e4989"
                            ],
                            [
                                0.3333333333333333,
                                "#31688e"
                            ],
                            [
                                0.4444444444444444,
                                "#26828e"
                            ],
                            [
                                0.5555555555555556,
                                "#1f9e89"
                            ],
                            [
                                0.6666666666666666,
                                "#35b779"
                            ],
                            [
                                0.7777777777777778,
                                "#6ece58"
                            ],
                            [
                                0.8888888888888888,
                                "#b5de2b"
                            ],
                            [
                                1.0,
                                "#fde725"
                            ]
                        ]
                    },
                    "colorway": [
                        "#1F77B4",
                        "#FF7F0E",
                        "#2CA02C",
                        "#D62728",
                        "#9467BD",
                        "#8C564B",
                        "#E377C2",
                        "#7F7F7F",
                        "#BCBD22",
                        "#17BECF"
                    ],
                    "font": {
                        "color": "rgb(36,36,36)"
                    },
                    "geo": {
                        "bgcolor": "white",
                        "lakecolor": "white",
                        "landcolor": "white",
                        "showlakes": true,
                        "showland": true,
                        "subunitcolor": "white"
                    },
                    "hoverlabel": {
                        "align": "left"
                    },
                    "hovermode": "closest",
                    "mapbox": {
                        "style": "light"
                    },
                    "paper_bgcolor": "white",
                    "plot_bgcolor": "white",
                    "polar": {
                        "angularaxis": {
                            "gridcolor": "rgb(232,232,232)",
                            "linecolor": "rgb(36,36,36)",
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside"
                        },
                        "bgcolor": "white",
                        "radialaxis": {
                            "gridcolor": "rgb(232,232,232)",
                            "linecolor": "rgb(36,36,36)",
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside"
                        }
                    },
                    "scene": {
                        "xaxis": {
                            "backgroundcolor": "white",
                            "gridcolor": "rgb(232,232,232)",
                            "gridwidth": 2,
                            "linecolor": "rgb(36,36,36)",
                            "showbackground": true,
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside",
                            "zeroline": false,
                            "zerolinecolor": "rgb(36,36,36)"
                        },
                        "yaxis": {
                            "backgroundcolor": "white",
                            "gridcolor": "rgb(232,232,232)",
                            "gridwidth": 2,
                            "linecolor": "rgb(36,36,36)",
                            "showbackground": true,
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside",
                            "zeroline": false,
                            "zerolinecolor": "rgb(36,36,36)"
                        },
                        "zaxis": {
                            "backgroundcolor": "white",
                            "gridcolor": "rgb(232,232,232)",
                            "gridwidth": 2,
                            "linecolor": "rgb(36,36,36)",
                            "showbackground": true,
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside",
                            "zeroline": false,
                            "zerolinecolor": "rgb(36,36,36)"
                        }
                    },
                    "shapedefaults": {
                        "fillcolor": "black",
                        "line": {
                            "width": 0
                        },
                        "opacity": 0.3
                    },
                    "ternary": {
                        "aaxis": {
                            "gridcolor": "rgb(232,232,232)",
                            "linecolor": "rgb(36,36,36)",
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside"
                        },
                        "baxis": {
                            "gridcolor": "rgb(232,232,232)",
                            "linecolor": "rgb(36,36,36)",
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside"
                        },
                        "bgcolor": "white",
                        "caxis": {
                            "gridcolor": "rgb(232,232,232)",
                            "linecolor": "rgb(36,36,36)",
                            "showgrid": false,
                            "showline": true,
                            "ticks": "outside"
                        }
                    },
                    "title": {
                        "x": 0.05
                    },
                    "xaxis": {
                        "automargin": true,
                        "gridcolor": "rgb(232,232,232)",
                        "linecolor": "rgb(36,36,36)",
                        "showgrid": false,
                        "showline": true,
                        "ticks": "outside",
                        "title": {
                            "standoff": 15
                        },
                        "zeroline": false,
                        "zerolinecolor": "rgb(36,36,36)"
                    },
                    "yaxis": {
                        "automargin": true,
                        "gridcolor": "rgb(232,232,232)",
                        "linecolor": "rgb(36,36,36)",
                        "showgrid": false,
                        "showline": true,
                        "ticks": "outside",
                        "title": {
                            "standoff": 15
                        },
                        "zeroline": false,
                        "zerolinecolor": "rgb(36,36,36)"
                    }
                }
            },
            "xaxis": {
                "anchor": "y",
                "domain": [
                    0.0,
                    0.425
                ]
            },
            "yaxis": {
                "anchor": "x",
                "domain": [
                    0.0,
                    1.0
                ],
                "title": {
                    "text": "adenosine (a.u.)"
                }
            },
            "xaxis2": {
                "anchor": "y2",
                "domain": [
                    0.575,
                    1.0
                ]
            },
            "yaxis2": {
                "anchor": "x2",
                "domain": [
                    0.0,
                    1.0
                ],
                "title": {
                    "text": "Residuals adenosine (a.u.)"
                }
            },
            "annotations": [
                {
                    "font": {
                        "size": 16
                    },
                    "showarrow": false,
                    "text": "Standard",
                    "x": 0.2125,
                    "xanchor": "center",
                    "xref": "paper",
                    "y": 1.0,
                    "yanchor": "bottom",
                    "yref": "paper"
                },
                {
                    "font": {
                        "size": 16
                    },
                    "showarrow": false,
                    "text": "Model Residuals",
                    "x": 0.7875,
                    "xanchor": "center",
                    "xref": "paper",
                    "y": 1.0,
                    "yanchor": "bottom",
                    "yref": "paper"
                },
                {
                    "font": {
                        "size": 16
                    },
                    "showarrow": false,
                    "text": "adenosine \u002f mMole \u002f Litre",
                    "x": 0.5,
                    "xanchor": "center",
                    "xref": "paper",
                    "y": 0,
                    "yanchor": "top",
                    "yref": "paper",
                    "yshift": -30
                }
            ],
            "margin": {
                "l": 20,
                "r": 20,
                "t": 100,
                "b": 60
            },
            "updatemenus": [
                {
                    "active": 0,
                    "buttons": [
                        {
                            "args": [
                                {
                                    "visible": [
                                        true,
                                        false,
                                        false,
                                        false
                                    ]
                                }
                            ],
                            "label": "adenosine standard",
                            "method": "update"
                        },
                        {
                            "args": [
                                {
                                    "visible": [
                                        true,
                                        true,
                                        true,
                                        true
                                    ],
                                    "title": "linear model"
                                }
                            ],
                            "label": "linear model",
                            "method": "update"
                        },
                        {
                            "args": [
                                {
                                    "visible": [
                                        true,
                                        true,
                                        true,
                                        true
                                    ]
                                }
                            ],
                            "label": "all",
                            "method": "update"
                        }
                    ],
                    "direction": "right",
                    "type": "buttons",
                    "x": 0,
                    "xanchor": "left",
                    "y": 1.2,
                    "yanchor": "top"
                }
            ]
        }
    }
    ```

The standard in now registered to the `adenosine` molecule. And can be added to another `ChromAnalyzer` object to quantify the adenosine concentration in the kinetic measurements.

### Add molecule with a standard to another `ChromAnalyzer`

Once a standard is defined, it can be transferred to another `ChromAnalyzer` object for subsequent quantification of the same molecule. This is carried out using the `add_molecule` method. During this process, the initial concentration and its unit can be adjusted to fit the reaction conditions of the `ChromAnalyzer` with time-course measurements.

!!! example

    ```python
    from chromatopy import ChromAnalyzer
    from chromatopy.units import mM

    data_path = "data/instances/time_course_adenosine.json"
    time_course_analyzer = ChromAnalyzer.from_json(data_path)

    # add adenosine with standard to the time course analyzer
    time_course_analyzer.add_molecule(
        molecule=adenosine,
        init_conc=0,
        conc_unit=mM,
        retention_tolerance=0.5,
    )
    ```
    ```
    🎯 Assigned adenosine to 3 peaks
    ```

### Internal Standard

The `define_internal_standard` method is used to designate a specific molecule as the internal standard within the `ChromAnalyzer` object. This internal standard is essential for accurate concentration calculations during chromatographic analysis. The method requires several parameters, including the molecule's identifier, PubChem CID, and retention time.

__Required parameters__:

- `id`: Internal identifier of the internal standard molecule, such as `s0`, `ABTS`, or `IS_01`.
- `pubchem_cid`: PubChem CID of the internal standard molecule.
- `name`: Name of the internal standard molecule.
- `init_conc`: Initial concentration of the internal standard in the sample.
- `conc_unit`: Unit of the concentration, for example, `mM` or `µM`.
- `retention_time`: Retention time of the internal standard in the chromatogram, measured in minutes.

__Optional parameters__:

- `retention_tolerance`: Retention time tolerance for peak annotation in minutes. This parameter helps account for slight variations in retention time during analysis. Defaults to `0.1`.
- `wavelength`: Wavelength at which the internal standard is detected by the HPLC detector. This is optional and defaults to `None` if not specified.

??? info "Quantification Using Internal Standard (IS) Ratios"

    When quantifying an analyte $\text{Ana}$ using an internal standard $\text{IS}$, the concentration of $\text{Ana}$ at a later time point can be calculated by comparing the change in the ratio of their respective peak areas over time. The initial known concentrations and peak areas at time $\text{t=0}$ establish a baseline for this calculation.

    The initial peak ratio is defined as:

    $$
    R_0 = \frac{A_{\text{Ana}_\text{t=0}}}{A_{\text{IS}_\text{t=0}}}
    $$

    The concentration of $\text{Ana}$ at time \( $\text{t=n}$ \) can be calculated using the following formula:

    $$
    C_{\text{Ana}_\text{t=n}} = C_{\text{Ana}_\text{t=0}} \times \frac{\left(\frac{A_{\text{Ana}_\text{t=n}}}{A_{\text{IS}_\text{t=n}}}\right)}{R_0}
    $$

    Where:

    - **$R_0$**: The baseline ratio of the peak area of $\text{Ana}$ to $\text{IS}$ at time \( t=0 \).
    - **$C_{\text{Ana}_\text{t=0}}$**: Initial concentration of $\text{Ana}$ at reaction time \( t=0 \).
    - **$A_{\text{Ana}_\text{t=0}}$**: Peak area of $\text{Ana}$ at reaction time \( t=0 \).
    - **$A_{\text{IS}_\text{t=0}}$**: Peak area of the Internal Standard ($\text{IS}$) at reaction time \( t=0 \).
    - **$C_{\text{Ana}_\text{t=n}}$**: Concentration of $\text{Ana}$ at time \( t=n \).
    - **$A_{\text{Ana}_\text{t=n}}$**: Peak area of $\text{Ana}$ at time \( t=n \).
    - **$A_{\text{IS}_\text{t=n}}$**: Peak area of the Internal Standard ($\text{IS}$) at time \( t=n \).

    This approach allows the initial concentration of $\text{Ana}$ to be adjusted according to the changes in the ratio of peak areas between the analyte and the internal standard over time, allowing quantification of $\text{Ana}$.

The following example shows how an internal standard molecule is added to the `cascade_analyzer` from the example above:

!!! example

    ```python
    from chromatopy import ChromAnalyzer
    from chromatopy.units import M

    path = "data/instances/analyzer_is.json"

    # Read the data
    analyzer_is = ChromAnalyzer.from_json(path=path)


    # add molecules
    analyzer_is.define_molecule(
        id="mal",
        name="maleimide",
        pubchem_cid=10935,
        init_conc=0.656,
        conc_unit=M,
        retention_time=6.05,
    )

    # define internal standard
    analyzer_is.define_internal_standard(
        id="std",
        name="internal standard",
        pubchem_cid=-1,
        init_conc=1.0,
        conc_unit=M,
        retention_time=6.3,
        retention_tolerance=0.05,
    )
    ```
    ```
    🎯 Assigned maleimide to 17 peaks
    🎯 Assigned internal standard to 17 peaks
    ```

## Convert Data

Time-course measurements can be converted into the EnzymeML format by using the `to_enzymeml` method. In this process, for all assigned molecules the corresponding peaks are extracted and reorganized as time-course data. If internal oder external standards are defined and `caluculate_concentrations` is set to `True`, the concentrations are calculated for the respective peaks. In the following examples, all previously defined datasets are converted into the EnzymeML format and the time-course data is visualized.

### Cascade Reaction

!!! example

    ```python
    from chromatopy.tools.utility import visualize_enzymeml

    cascade_enzymeml = cascade_analyzer.to_enzymeml(
        name="MjMAT cascade",
        calculate_concentration=False,
    )

    visualize_enzymeml(cascade_enzymeml)
    ```
    ![Cascade reaction](plots/cascade_enzymeml.png)

### Adenosine buildup after 24 hours

!!! example

    ```python
    adenosine_enzymeml = time_course_analyzer.to_enzymeml(
        name="adenosine time course",
        calculate_concentration=True,
    )


    visualize_enzymeml(adenosine_enzymeml)
    ```
    ![Adenosine buildup after 24 hours](plots/adenosine_enzymeml.png)

### Maleimide catalysis with internal standard

!!! example

    ```python
    adenosine_enzymeml = time_course_analyzer.to_enzymeml(
        name="adenosine time course",
        calculate_concentration=True,
    )


    visualize_enzymeml(adenosine_enzymeml)
    ```
    ![Maleimide catalysis](plots/is_enzymeml.png)


## Peak detection and integration

In all previous examples, the peaks were already integrated by OpenChrom or other chromatographic software. It is also possible to use the `ChromAnalyzer` to detect and integrate peaks in chromatograms using the [`hplc-py`](https://cremerlab.github.io/hplc-py/index.html) library. Depending on the chromatographic data, the method showed to be unreliable and fails from time to time. Therefore, it is recommended to use the [batch processing with OpenChrom](../../supported_formats/#batch-processing)

The following code shows how the integrated peak processing is done:

!!! example

    ```python
    calib_analyzer.process_chromatograms(
        prominence=0.03,
    )   
    ```