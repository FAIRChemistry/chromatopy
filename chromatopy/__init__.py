import importlib as _il
import importlib.abc as _abc
import importlib.util as _iu
import sys as _sys
import warnings as _w

_w.warn(
    "Package 'chromatopy' was renamed to 'chromhandler'; use 'chromhandler' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export top-level API
_new = _il.import_module("chromhandler")
from chromhandler import *  # noqa: F401,F403

__all__ = getattr(_new, "__all__", [n for n in dir(_new) if not n.startswith("_")])
__version__ = getattr(_new, "__version__", None)


class _AliasFinder(_abc.MetaPathFinder, _abc.Loader):
    _alias = __name__ + "."
    _target = "chromhandler."

    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(self._alias):
            real = self._target + fullname[len(self._alias) :]
            spec = _iu.find_spec(real)
            if spec:
                return _iu.spec_from_loader(fullname, self, origin=spec.origin)
        return None

    def create_module(self, spec):
        return None  # default

    def exec_module(self, module):
        real = self._target + module.__name__[len(self._alias) :]
        real_mod = _il.import_module(real)
        _sys.modules[module.__name__] = real_mod


# Ensure aliasing for 'chromatopy.*' submodules
_sys.meta_path.insert(0, _AliasFinder())
