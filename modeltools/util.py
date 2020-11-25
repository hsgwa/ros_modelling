
class Util():
    @classmethod
    def flatten(cls, x):
        import itertools
        return list(itertools.chain.from_iterable(x))
    @classmethod
    def ext(cls, path):
        import os
        _, ext = os.path.splitext(path)
        return ext[1:]
