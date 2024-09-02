import unittest

import pytest

from chromatopy.readers.shimadzu import ShimadzuReader
from chromatopy.units import min

DIR_PATH = "tests/test_readers/data/shimadzu"


@pytest.mark.readers
class TestShimadzuReader(unittest.TestCase):
    # can read a single file and return a dictionary
    def test_read_shimadzu(self):
        reader = ShimadzuReader(
            dirpath=DIR_PATH,
            reaction_times=[0] * 9,
            time_unit=min,
            ph=7.4,
            temperature=25.0,
            temperature_unit="C",
        )

        measurements = reader.read()

        assert len(measurements) == 9
        assert measurements[0].chromatograms[0].peaks[0].area == pytest.approx(1278.0)
