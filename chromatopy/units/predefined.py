import warnings

warnings.warn(
    "Importing units from `predefined.units` is discouraged. "
    "Use strings like 'mmol / l', 's', etc. instead.",
    UserWarning,
    stacklevel=3,
)

# Molarity
M = "mol / l"
mM = "mmol / l"
uM = "umol / l"
nM = "nmol / l"

# Mass Concentration
g_L = "g / l"
mg_L = "mg / l"
ug_L = "ug / l"

# Substance
mol = "mol"
mmol = "mmol"
umol = "umol"
nmol = "nmol"

# Mass
gram = "g"
g = "g"
mg = "mg"
ug = "ug"
ng = "ng"
kg = "kg"

# Volume
litre = "l"
l = "l"  # noqa: E741
ml = "ml"
ul = "ul"
nl = "nl"


# Time
second = "s"
s = "s"
minute = "min"
hour = "hour"
h = "hour"
day = "day"
d = "day"

# Temperature
kelvin = "K"
K = "K"
celsius = "Celsius"
C = "Celsius"
