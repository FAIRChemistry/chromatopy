from __future__ import annotations

import warnings as _warnings
from typing import Any

from .enzymeml import to_enzymeml
from .handler import Handler
from .molecule import Molecule
from .protein import Protein


# Backward compatibility with deprecation warning
def ChromAnalyzer(*args: Any, **kwargs: Any) -> Handler:
    """
    Deprecated: ChromAnalyzer has been renamed to Handler.
    Please use Handler instead.
    """
    _warnings.warn(
        "ChromAnalyzer is deprecated and will be removed in version 1.0.0. "
        "Use 'Handler' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return Handler(*args, **kwargs)


__all__ = ["Handler", "ChromAnalyzer", "Molecule", "Protein", "to_enzymeml"]

__version__ = "0.4.0"
