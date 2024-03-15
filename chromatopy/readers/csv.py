import os
from datetime import datetime

from chromatopy.readers.abstractreader import AbstractReader


class CSVReader(AbstractReader):

    def read(self):
        raise NotImplementedError

    def read_file(self):
        raise NotImplementedError()

    def extract_peaks(self):
        raise NotImplementedError()

    def extract_signal(self):
        raise NotImplementedError()
