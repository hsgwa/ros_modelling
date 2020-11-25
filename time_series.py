
class Timeseries:
    def __init__(self, raw: Union[np.array]):
        self.__raw = raw

    @property
    def raw(self) -> np.ndarray:
        return self.__raw


class TimeseriesReader:
    def read(self, file_path: Union[str]) -> Histogram:
        pass




class TimeseriesReaderFactory:
    @classmethod
    def create(cls, reader_type):
        if reader_type == 'csv':
            return CsvHistogramReader()
        return None


class CsvTimeseriesReader(TimeseriesReader):
    def read(self, file_path: Union[str]) -> Timeseries:
        self.csv_path = file_path
        data = np.loadtxt(self.csv_path, delimiter=',')
        def to_sec(x): return x[0] + x[1]*1e-9
        data_sec = [to_sec(_) for _ in data]
        return Timeseries(data_sec)
