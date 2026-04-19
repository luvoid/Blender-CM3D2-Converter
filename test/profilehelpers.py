import cProfile
import pstats
from pathlib import Path
from types import FunctionType

import profile

import cm3d2converter  # If not imported, call stack is missing

from .blenderunittest import BlenderTestCase

from cProfile import Profile
from line_profiler import LineProfiler as _LineProfiler

from typing import TYPE_CHECKING


class LineProfile(_LineProfiler):    
    if TYPE_CHECKING:
        def enable(self):
            pass
        def disable(self):
            pass


class ProfileTest_OLD:
    out_dir = Path(__file__).parent / 'output'
    static_profiler = None
    static_runner = None
    
    def __init__(self, name):
        self.profiler = cProfile.Profile()
        self._out_path = (self.out_dir / name).with_suffix('.prof')
        
    @property
    def profiler(self) -> cProfile.Profile:
        return self.__class__.static_profiler
    
    @profiler.setter
    def profiler(self, value):
        cls = self.__class__
        if self._is_static_runner and value is None:
            cls.static_runner = None
            cls.static_profiler = None
        elif cls.static_runner is None:
            cls.static_profiler = value
    
    @property
    def _is_static_runner(self):
        return self.__class__.static_runner is self
    
    def __enter__(self):
        self.profiler.enable()
    
    def __exit__(self, *exc_info):
        if not self._is_static_runner:
            return
        
        self.profiler.disable()
        
        stats = pstats.Stats(self.profiler)
        stats.sort_stats(pstats.SortKey.CUMULATIVE)
        stats.dump_stats(self._out_path)
        
        self.profiler = None


class ProfileLog(cProfile.Profile):
    out_dir = Path(__file__).parent / 'output'

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._out_path = (self.out_dir / filename).with_suffix('.prof')
        
    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._out_path = (self.out_dir / filename).with_suffix('.prof')

    def __exit__(self, *exc_info):
        super().__exit__(*exc_info)
        
        stats = pstats.Stats(self)
        stats.sort_stats(pstats.SortKey.CUMULATIVE)
        stats.dump_stats(self._out_path)


def dump_test_stats(test_case: BlenderTestCase, *profs):
    out_dir = Path(test_case.output_dir)
    out_path = (out_dir / test_case._testMethodName).with_suffix('.prof')
    line_out_path = out_path.with_suffix('.lprof')
    
    stats = pstats.Stats()
    for prof in profs:
        if isinstance(prof, LineProfile):
            prof.dump_stats(str(line_out_path))
        else:
            substats = pstats.Stats(prof)
        stats.add(substats)
    
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.dump_stats(out_path)