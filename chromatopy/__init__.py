import importlib
import sys
import warnings

warnings.warn(
    "'chromatopy' is deprecated; switch to 'chromhandler'. "
    "This alias disappears in v1.0.",
    DeprecationWarning,
    stacklevel=2,
)

_target = importlib.import_module("chromhandler")

# Expose the real module under the old name
sys.modules[__name__] = _target
# If you want `from chromatopy import foo` to work:
globals().update(_target.__dict__)
