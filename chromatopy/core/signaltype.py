from enum import Enum


class SignalType(Enum):

    UV = "uv/visible absorbance detector"
    FLD = "fluorescence detector"
    FID = "flame ionization detector"
    TCD = "thermal conductivity detector"
    RID = "refractive index detector"
    ELSD = "evaporative light scattering detector"
    MS = "mass spectrometry"
    DAD = "diode array detector"
