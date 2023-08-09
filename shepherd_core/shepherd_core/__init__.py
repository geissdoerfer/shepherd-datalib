"""
shepherd.core
~~~~~
Provides classes for storing and retrieving sampled IV data to/from
HDF5 files.

"""
from .data_models.base.calibration import Calc_t
from .data_models.base.calibration import CalibrationCape
from .data_models.base.calibration import CalibrationEmulator
from .data_models.base.calibration import CalibrationHarvester
from .data_models.base.calibration import CalibrationPair
from .data_models.base.calibration import CalibrationSeries
from .data_models.task import Compression
from .inventory import Inventory
from .logger import get_verbose_level
from .logger import logger
from .logger import set_verbose_level
from .reader import BaseReader
from .testbed_client.client import TestbedClient
from .testbed_client.client import tb_client
from .writer import BaseWriter

__version__ = "2023.8.3"

__all__ = [
    "BaseReader",
    "BaseWriter",
    "get_verbose_level",
    "set_verbose_level",
    "logger",
    "CalibrationCape",
    "CalibrationSeries",
    "CalibrationEmulator",
    "CalibrationHarvester",
    "CalibrationPair",
    "Calc_t",
    "Compression",
    "TestbedClient",
    "tb_client",  # using this (instead of the Class) is the cleaner, but less pythonic way
    "Inventory",
]
