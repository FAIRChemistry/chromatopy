from .abstractreader import AbstractReader


class ChemStationReader(AbstractReader):

    def read(self):
        raise NotImplementedError

    def read_file(self):
        raise NotImplementedError()

    def extract_peaks(self):
        raise NotImplementedError()

    def extract_signal(self):
        raise NotImplementedError()
