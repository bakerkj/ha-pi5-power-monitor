# Copyright (c) 2026 Kenneth Baker <bakerkj@umich.edu>
# All rights reserved.

"""Constants for the Raspberry Pi 5 Power Monitor integration."""

from typing import Final

DOMAIN: Final = "pi5_power_monitor"

# Config entry options
CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_SCAN_INTERVAL: Final = 30

# vcgencmd binary location inside the HA container on Pi 5 HAOS. The firmware
# mailbox device /dev/vcio and this binary are both present by default; no
# additional mounts or packages are required.
VCGENCMD_BINARY: Final = "/usr/bin/vcgencmd"
VCGENCMD_SUBCOMMAND: Final = "pmic_read_adc"

# Ordered list of PMIC rails that carry BOTH voltage and current readings.
# Order drives sensor registration order and keeps per-rail entities grouped
# together in the UI. Keyed by the stem vcgencmd reports (``<RAIL>_V`` /
# ``<RAIL>_A``).
RAILS_V_AND_A: Final = (
    "3V7_WL_SW",
    "3V3_SYS",
    "1V8_SYS",
    "DDR_VDD2",
    "DDR_VDDQ",
    "1V1_SYS",
    "0V8_SW",
    "VDD_CORE",
    "3V3_DAC",
    "3V3_ADC",
    "0V8_AON",
    "HDMI",
)

# Rails that carry only a voltage reading (no current channel in the PMIC).
RAILS_V_ONLY: Final = (
    "EXT5V",
    "BATT",
)

# Rails whose entities are enabled by default; everything else is disabled
# so the entity list is not flooded. VDD_CORE tracks CPU draw and is the
# single most useful per-rail sensor for correlating with workload.
DEFAULT_ENABLED_RAILS: Final = ("VDD_CORE",)
