import struct
from typing import Callable
from typing import Generator
from typing import TypeVar
from typing import Union

import numpy as np
from numpy.typing import NDArray
from pydantic import PositiveFloat

from ...calibration_hw_def import adc_current_to_raw
from ...calibration_hw_def import adc_voltage_to_raw
from ...calibration_hw_def import dac_voltage_to_raw
from .shepherd import ShpModel

# TODO: port over TESTs

T_calc = TypeVar("T_calc", NDArray[np.float64], float)


def dict_generator(indict, pre=None) -> Generator[list, None, None]:
    pre = pre[:] if pre else []
    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                yield from dict_generator(value, pre + [key])
            elif isinstance(value, Union[list, tuple]):
                for v in value:
                    yield from dict_generator(v, pre + [key])
            else:
                yield pre + [key, value]
    else:
        yield pre + [indict]


class CalibrationPair(ShpModel):
    """SI-value [SI-Unit] = raw-value * gain + offset"""

    gain: PositiveFloat
    offset: float = 0

    def raw_to_si(self, values_raw: T_calc) -> T_calc:
        """Helper to convert between physical units and raw unsigned integers"""
        values_si = values_raw * self.gain + self.offset
        if isinstance(values_si, np.ndarray):
            values_si[values_si < 0.0] = 0.0
            # if pyright still complains, cast with .astype(float)
        else:
            values_si = float(max(values_si, 0.0))
        return values_si

    def si_to_raw(self, values_si: T_calc) -> T_calc:
        """Helper to convert between physical units and raw unsigned integers"""
        values_raw = (values_si - self.offset) / self.gain
        if isinstance(values_raw, np.ndarray):
            values_raw[values_raw < 0.0] = 0.0
        else:
            values_raw = max(values_raw, 0.0)
        return values_raw

    @classmethod
    def from_fn(cls, fn: Callable):
        offset = fn(0)
        gain_inv = fn(1.0) - offset
        return cls(
            gain=1.0 / float(gain_inv),
            offset=-float(offset) / gain_inv,
        )


class CalibrationSeries(ShpModel):
    voltage: CalibrationPair = CalibrationPair(gain=3 * 1e-9)
    # ⤷ default allows 0 - 12 V in 3 nV-Steps
    current: CalibrationPair = CalibrationPair(gain=250 * 1e-12)
    # ⤷ default allows 0 - 1 A in 250 pA - Steps
    time: CalibrationPair = CalibrationPair(gain=1e-9)
    # ⤷ default allows nanoseconds


class CalibrationHarvester(ShpModel):
    dac_V_Hrv: CalibrationPair = CalibrationPair.from_fn(dac_voltage_to_raw)
    dac_V_Sim: CalibrationPair = CalibrationPair.from_fn(dac_voltage_to_raw)
    adc_V_Sense: CalibrationPair = CalibrationPair.from_fn(adc_voltage_to_raw)
    adc_C_Hrv: CalibrationPair = CalibrationPair.from_fn(adc_current_to_raw)

    def export_for_sysfs(self) -> dict:
        """
        [scaling according to commons.h]
        # ADC-C is handled in nA (nano-ampere), gain is shifted by 8 bit
        # ADC-V is handled in uV (micro-volt), gain is shifted by 8 bit
        # DAC-V is handled in uV (micro-volt), gain is shifted by 20 bit
        """
        cal_set = {
            "adc_current_gain": round(1e9 * (2**8) * self.adc_C_Hrv.gain),
            "adc_current_offset": round(1e9 * (2**0) * self.adc_C_Hrv.offset),
            "adc_voltage_gain": round(1e6 * (2**8) * self.adc_V_Sense.gain),
            "adc_voltage_offset": round(1e6 * (2**0) * self.adc_V_Sense.offset),
            "dac_voltage_gain": round((2**20) / (1e6 * self.dac_V_Hrv.gain)),
            "dac_voltage_offset": round(1e6 * (2**0) * self.dac_V_Hrv.offset),
        }
        for key, value in cal_set.items():
            if (("gain" in key) and not (0 <= value < 2**32)) or (
                ("offset" in key) and not (-(2**31) <= value < 2**31)
            ):
                raise ValueError(f"Value ({key}={value}) exceeds uint32-container")
        return cal_set


class CalibrationEmulator(ShpModel):
    dac_V_Main: CalibrationPair = CalibrationPair.from_fn(dac_voltage_to_raw)
    dac_V_Aux: CalibrationPair = CalibrationPair.from_fn(dac_voltage_to_raw)
    adc_C_A: CalibrationPair = CalibrationPair.from_fn(adc_current_to_raw)
    adc_C_B: CalibrationPair = CalibrationPair.from_fn(adc_current_to_raw)

    def export_for_sysfs(self) -> dict:
        """
        [scaling according to commons.h]
        # ADC-C is handled in nA (nano-ampere), gain is shifted by 8 bit
        # ADC-V is handled in uV (micro-volt), gain is shifted by 8 bit
        # DAC-V is handled in uV (micro-volt), gain is shifted by 20 bit
        """
        cal_set = {
            "adc_current_gain": round(1e9 * (2**8) * self.adc_C_A.gain),
            "adc_current_offset": round(1e9 * (2**0) * self.adc_C_A.offset),
            "adc_voltage_gain": round(1e6 * (2**8) * self.adc_C_B.gain),
            "adc_voltage_offset": round(1e6 * (2**0) * self.adc_C_B.offset),
            "dac_voltage_gain": round((2**20) / (1e6 * self.dac_V_Main.gain)),
            "dac_voltage_offset": round(1e6 * (2**0) * self.dac_V_Main.offset),
        }
        for key, value in cal_set.items():
            if (("gain" in key) and not (0 <= value < 2**32)) or (
                ("offset" in key) and not (-(2**31) <= value < 2**31)
            ):
                raise ValueError(f"Value ({key}={value}) exceeds uint32-container")
        return cal_set


class CalibrationCape(ShpModel):
    """Represents calibration data of shepherd cape.
    Defines the format of calibration data and provides convenient functions
    to read and write calibration data.

    YAML: .to_file() and .from_file() already in ShpModel
    """

    harvester: CalibrationHarvester = CalibrationHarvester()
    emulator: CalibrationEmulator = CalibrationEmulator()

    #
    @classmethod
    def from_bytestr(cls, data: bytes):
        """Instantiates calibration data based on byte string.
        This is mainly used to deserialize data read from an EEPROM memory.

        Args:
            data: Byte string containing calibration data.
        Returns:
            CalibrationCape object with extracted calibration data.
        """
        dv = cls().dict()
        lw = list(dict_generator(dv))
        values = struct.unpack(">" + len(lw) * "d", data)
        # ⤷ X => double float, big endian
        for _i, walk in enumerate(lw):
            # hardcoded fixed depth ... bad but easy
            dv[walk[0]][walk[1]][walk[2]] = float(values[_i])
        return cls(**dv)

    def to_bytestr(self) -> bytes:
        """Serializes calibration data to byte string.
        Used to prepare data for writing it to EEPROM.

        Returns:
            Byte string representation of calibration values.
        """
        lw = list(dict_generator(self.dict()))
        values = [walk[-1] for walk in lw]
        return struct.pack(">" + len(lw) * "d", *values)
