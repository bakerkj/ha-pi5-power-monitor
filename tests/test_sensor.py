# Copyright (c) 2026 Kenneth Baker <bakerkj@umich.edu>
# All rights reserved.

"""Sensor-layer tests: total-power aggregate and selector wiring."""

from __future__ import annotations

from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorEntityDescription

from custom_components.pi5_power_monitor.coordinator import PmicData, _parse
from custom_components.pi5_power_monitor.sensor import (
    _rail_selector,
    _RailSensor,
    _TotalPower,
)

from .conftest import SAMPLE_PMIC_OUTPUT


def _coordinator_with(data: PmicData | None) -> MagicMock:
    c = MagicMock()
    c.data = data
    return c


def _desc(key: str, name: str) -> SensorEntityDescription:
    return SensorEntityDescription(key=key, name=name)


def test_total_power_sensor_returns_coordinator_total():
    data = _parse(SAMPLE_PMIC_OUTPUT)
    sensor = _TotalPower(_coordinator_with(data), "entry1", _desc("total_power", "x"))
    assert sensor.native_value is not None
    assert abs(sensor.native_value - data.total_power) < 1e-9


def test_total_power_sensor_returns_none_when_no_data_yet():
    sensor = _TotalPower(_coordinator_with(None), "entry1", _desc("total_power", "x"))
    assert sensor.native_value is None


def test_rail_selector_reads_requested_kind():
    """The per-rail selector is a plain callable; stability of its return
    value for each (rail, kind) pair is what the sensor platform depends on."""
    data = _parse(SAMPLE_PMIC_OUTPUT)
    for rail in ("VDD_CORE", "3V3_SYS"):
        for kind in ("voltage", "current", "power"):
            val = _rail_selector(rail, kind)(data)
            expected = getattr(data.rails[rail], kind)
            assert val == expected


def test_rail_sensor_uses_selector():
    """End-to-end: build a sensor around a selector and ensure it reports
    the same value the selector would return in isolation."""
    data = _parse(SAMPLE_PMIC_OUTPUT)
    sensor = _RailSensor(
        _coordinator_with(data),
        "entry1",
        _desc("VDD_CORE_power", "x"),
        _rail_selector("VDD_CORE", "power"),
    )
    assert sensor.native_value == data.rails["VDD_CORE"].power
