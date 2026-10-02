# Copyright (c) 2026 Kenneth Baker <bakerkj@umich.edu>
# All rights reserved.

"""Shared fixtures for the pi5_power_monitor tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable the custom-component shim for every test automatically."""
    yield


# A representative raw vcgencmd pmic_read_adc output block, taken verbatim from
# an idle Pi 5 running HAOS. Tests parse this and assert the derived values.
SAMPLE_PMIC_OUTPUT = """\
3V7_WL_SW_A current(0)=0.00195186A
   3V3_SYS_A current(1)=0.12589500A
   1V8_SYS_A current(2)=0.23129540A
  DDR_VDD2_A current(3)=0.00000000A
  DDR_VDDQ_A current(4)=0.00000000A
   1V1_SYS_A current(5)=0.18835450A
    0V8_SW_A current(6)=0.30644200A
  VDD_CORE_A current(7)=0.82156000A
   3V3_DAC_A current(17)=0.00000000A
   3V3_ADC_A current(18)=0.00000000A
   0V8_AON_A current(16)=0.00311355A
      HDMI_A current(22)=0.00036630A
 3V7_WL_SW_V volt(8)=3.70720000V
   3V3_SYS_V volt(9)=3.30260900V
   1V8_SYS_V volt(10)=1.81294100V
  DDR_VDD2_V volt(11)=1.10732500V
  DDR_VDDQ_V volt(12)=0.60183090V
   1V1_SYS_V volt(13)=1.10622600V
    0V8_SW_V volt(14)=0.80146440V
  VDD_CORE_V volt(15)=0.81203820V
   3V3_DAC_V volt(20)=3.30952000V
   3V3_ADC_V volt(21)=3.31226800V
   0V8_AON_V volt(19)=0.79912020V
      HDMI_V volt(23)=5.12416000V
     EXT5V_V volt(24)=5.13756000V
      BATT_V volt(25)=0.00000000V
"""
