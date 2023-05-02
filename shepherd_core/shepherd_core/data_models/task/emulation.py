from datetime import datetime
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import confloat
from pydantic import root_validator

from shepherd_core.data_models.testbed import Testbed

from ..base.shepherd import ShpModel
from ..content.virtual_source import VirtualSource
from ..experiment.experiment import Experiment
from ..experiment.observer_features import GpioActuation
from ..experiment.observer_features import GpioTracing
from ..experiment.observer_features import PowerTracing
from ..experiment.observer_features import SystemLogging
from ..testbed.cape import TargetPort


class Compression(str, Enum):
    lzf = "lzf"  # not native hdf5
    gzip1 = 1  # higher compr & load


compressions_allowed: list = [None, "lzf", 1]  # TODO: is it still needed?


class EmulationTask(ShpModel):
    """Configuration for the Observer in Emulation-Mode"""

    # General config
    input_path: Path
    output_path: Optional[Path]
    # ⤷ output_path:
    #   - providing a directory -> file is named emu_timestamp.h5
    #   - for a complete path the filename is not changed except it exists and
    #     overwrite is disabled -> emu#num.h5
    force_overwrite: bool = False
    output_compression: Optional[Compression] = Compression.lzf
    # ⤷ should be 1 (level 1 gzip), lzf, or None (order of recommendation)

    time_start: Optional[datetime] = None  # = ASAP
    duration: Optional[timedelta] = None  # = till EOF

    # emulation-specific
    use_cal_default: bool = False
    # ⤷ do not load calibration from EEPROM

    enable_io: bool = False
    # ⤷ pre-req for sampling gpio
    io_port: TargetPort = TargetPort.A
    # ⤷ either Port A or B
    pwr_port: TargetPort = TargetPort.A
    # ⤷ that one will be current monitored (main), the other is aux
    voltage_aux: confloat(ge=0, le=5) = 0
    # ⤷ aux_voltage options:
    #   - None to disable (0 V),
    #   - 0-4.5 for specific const Voltage,
    #   - "mid" will output intermediate voltage (vsource storage cap),
    #   - true or "main" to mirror main target voltage

    verbose: bool = False

    # sub-elements, could be partly moved to emulation
    virtual_source: VirtualSource = VirtualSource(name="neutral")  # {"name": "neutral"}

    power_tracing: PowerTracing = PowerTracing()
    gpio_tracing: GpioTracing = GpioTracing()
    gpio_actuation: Optional[GpioActuation]
    sys_logging: SystemLogging = SystemLogging()

    @root_validator(pre=False)
    def post_validation(cls, values: dict) -> dict:
        # TODO: limit paths
        has_start = values["time_start"] is not None
        if has_start and values["time_start"] < datetime.utcnow():
            raise ValueError("Start-Time for Emulation can't be in the past.")
        return values

    @classmethod
    def from_xp(cls, xp: Experiment, tb: Testbed, tgt_id: int):
        # TODO
        pass


# TODO: herdConfig
#  - store if path is remote (read & write)
#   -> so files need to be fetched or have a local path
