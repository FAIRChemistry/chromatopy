import pytest

from chromatopy.readers.thermo_txt import ThermoTX0Reader
from chromatopy.units import C, minute


@pytest.fixture
def thermo_reader() -> ThermoTX0Reader:
    reader = ThermoTX0Reader(
        dirpath="docs/examples/data/thermo",
        values=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
        unit=minute,
        ph=7.4,
        temperature=25.0,
        temperature_unit=C,
        silent=True,
        mode="timecourse",
    )
    return reader


def test_read_thermo(thermo_reader: ThermoTX0Reader) -> None:
    measurements = thermo_reader.read()
    assert len(measurements) == 8
    assert measurements[0].data.value == 0.0
    assert measurements[-1].data.value == 7.0

    # Test first measurement's first peak
    first_peak = measurements[0].chromatograms[0].peaks[0]
    assert first_peak.retention_time == pytest.approx(0.038, rel=1e-3)
    assert first_peak.area == pytest.approx(257.10, rel=1e-3)
    assert first_peak.amplitude == pytest.approx(696.06, rel=1e-3)
    assert first_peak.percent_area == pytest.approx(0.00, rel=1e-3)

    # Test metadata
    assert measurements[0].temperature == 25.0
    assert measurements[0].temperature_unit == C
    assert measurements[0].ph == 7.4
