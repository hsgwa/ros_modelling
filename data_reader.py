from typing import List, Union, Any, Callable, Dict
import numpy as np

class Histogram:
    __normalize = False
    __trim = False

    def __init__(self, raw: Union[np.array]):
        if Histogram.__normalize:
            raw = raw / np.sum(raw)
        self.__raw = np.trim_zeros(raw, "b")

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
        tmp = np.convolve(self.__raw, hist_.raw, mode='full')
        if Histogram.__trim:
            tmp[len(self.__raw)-1] += np.sum(tmp[len(self.__raw):])
            tmp = tmp[:len(self.__raw)]
        else:
            tmp = np.trim_zeros(tmp, "b")
        if Histogram.__normalize:
            tmp = tmp / np.sum(tmp)
        return self.__class__(tmp)

    @property
    def raw(self) -> np.ndarray:
        return self.__raw

class Timeseries:
    def __init__(self, raw: Union[np.array]):
        self.__raw = raw

    @property
    def raw(self) -> np.ndarray:
        return self.__raw


class DataReaderFactory:
    @classmethod
    def create(cls, reader_format, reader_type):
        if reader_format == 'csv' and reader_type == 'histogram':
            return CsvHistogramReader()
        if reader_format == 'csv' and reader_type == 'timeseries':
            return CsvTimeseriesReader()

        print('err: failed to get reader')
        return None

class HistogramReader:
    def get_hist(self, file_path: Union[str]) -> Histogram:
        pass
    def get_timeseries(self, file_path: Union[str]) -> Timeseries:
        return None

class CsvHistogramReader(HistogramReader):
    def get_hist(self, file_path: Union[str]) -> Histogram:
        self.csv_path = file_path
        data = np.loadtxt(self.csv_path, delimiter=',').T
        bin_num = int(data[0][-1])+1
        hist = np.array([0]*bin_num)
        for i in  range(len(data[0])):
            hist_idx = int(data[0][i])
            hist[hist_idx] = int(data[1][i])

        return Histogram(hist)

class TimeseriesReader:
    def get_hist(self, file_path: Union[str]) -> Histogram:
        pass
    def get_timeseries(self, file_path: Union[str]) -> Histogram:
        pass


class CsvTimeseriesReader(TimeseriesReader):
    def get_hist(self, file_path: Union[str]) -> Timeseries:
        data = np.loadtxt(file_path, delimiter=',').T[1]
        bins = int(np.ceil(np.max(data)))+1
        range_max = int(np.ceil(np.max(data)))+1
        hist_raw, _ = np.histogram(data, bins=bins, range=(0, range_max))
        return Histogram(hist_raw)

    def get_timeseries(self, file_path: Union[str]) -> Timeseries:
        data = np.loadtxt(file_path, delimiter=',').T[1]
        data_usec = data
        return Timeseries(data_usec)
