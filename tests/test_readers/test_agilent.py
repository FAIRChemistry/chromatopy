import numpy as np
import pytest

from chromatopy.tools.analyzer import ChromAnalyzer
from chromatopy.units import min


def test_initialize_from_agilent_txt():
    path = "tests/test_readers/data/agilent_txt"
    reaction_times = np.arange(0, 49, 1).tolist()

    ana = ChromAnalyzer.read_agilent(
        path=path,
        reaction_times=reaction_times,
        time_unit=min,
        ph=7.4,
        temperature=25.0,
    )

    assert len(ana.measurements) == 49
    assert ana.measurements[0].chromatograms[0].peaks[0].area == pytest.approx(45713.7)


def test_initialize_from_agilent_csv():
    path = "tests/test_readers/data/agilent_csv"
    reaction_times = np.arange(0, 17, 1).tolist()

    ana = ChromAnalyzer.read_agilent(
        path=path,
        reaction_times=reaction_times,
        time_unit=min,
        ph=7.4,
        temperature=25.0,
    )

    assert len(ana.measurements) == 17
    assert ana.measurements[0].chromatograms[0].peaks[0].area == pytest.approx(
        13751453.0
    )