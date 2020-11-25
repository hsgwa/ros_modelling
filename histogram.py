from typing import List, Union, Any, Callable, Dict
import numpy as np

class Histogram:
    __normalize = False
    __trim = False

    def __init__(self, raw: Union[np.array]):
        if Histogram.__normalize:
            raw = raw / np.sum(raw)
        self.__raw = raw

    @classmethod
    def normalize(cls, use):
        cls.__normalize = use

    @classmethod
    def get_normalize(cls):
        return cls.__normalize

    @classmethod
    def trim(cls, use):
        cls.__trim = use

    @classmethod
    def sum(cls, histgrams):
        hist = Histogram(histgrams[0].raw)
        for histgram in histgrams[1:]:
            hist = hist + histgram
        return hist

    def __add__(self, hist_):
        # todo : length validation
        tmp = np.convolve(self.__raw, hist_.raw, mode='full')
        if Histogram.__trim:
            tmp[len(self.__raw)-1] += np.sum(tmp[len(self.__raw):])  # オーバーした分
            tmp = tmp[:len(self.__raw)]
        else:
            tmp = np.trim_zeros(tmp, "b")
        if Histogram.__normalize:
            tmp = tmp / np.sum(tmp)
        return self.__class__(tmp)

    @property
    def raw(self) -> np.ndarray:
        return self.__raw

class HistogramReader:
    def read(self, file_path: Union[str]) -> Histogram:
        pass

class HistogramReaderFactory:
    @classmethod
    def create(cls, reader_type):
        if reader_type == 'csv':
            return CsvHistogramReader()

        return None

class CsvHistogramReader(HistogramReader):
    def read(self, file_path: Union[str]) -> Histogram:
        self.csv_path = file_path
        data = np.loadtxt(self.csv_path, delimiter=',')
        return Histogram(data.T[1])

