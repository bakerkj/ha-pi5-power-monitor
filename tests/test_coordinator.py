# Copyright (c) 2026 Kenneth Baker <bakerkj@umich.edu>
# All rights reserved.

"""Parser and coordinator tests for the pi5_power_monitor integration.

The parser is a free function so these tests don't need HA fixtures at all,
which keeps them fast and makes regression triage straightforward: if the
parser output changes, these go red before anything else.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.pi5_power_monitor.coordinator import (
    Pi5PowerMonitorCoordinator,
    PmicData,
    _parse,
)

from .conftest import SAMPLE_PMIC_OUTPUT


def test_parser_populates_every_rail():
    """Every rail the integration knows about appears in rails map."""
    from custom_components.pi5_power_monitor.const import RAILS_V_AND_A, RAILS_V_ONLY

    data = _parse(SAMPLE_PMIC_OUTPUT)
    assert isinstance(data, PmicData)
    for rail in (*RAILS_V_AND_A, *RAILS_V_ONLY):
        assert rail in data.rails, rail


def test_parser_voltage_and_current_align():
    """A spot check: VDD_CORE's parsed V and I should match the sample verbatim."""
    data = _parse(SAMPLE_PMIC_OUTPUT)
    core = data.rails["VDD_CORE"]
    assert core.voltage is not None and abs(core.voltage - 0.81203820) < 1e-6
    assert core.current is not None and abs(core.current - 0.82156000) < 1e-6
    # Power is V * I
    assert core.power is not None
    assert abs(core.power - 0.81203820 * 0.82156000) < 1e-6


def test_parser_voltage_only_rails_have_no_current():
    """EXT5V and BATT carry voltage only; current and power must stay None so
    the sensor layer renders them as unknown rather than fabricating a 0."""
    data = _parse(SAMPLE_PMIC_OUTPUT)
    ext5v = data.rails["EXT5V"]
    assert ext5v.voltage is not None and ext5v.voltage > 5.0
    assert ext5v.current is None
    assert ext5v.power is None

    batt = data.rails["BATT"]
    assert batt.voltage == 0.0  # UPS or PoE powered -> battery rail isolated
    assert batt.current is None
    assert batt.power is None


def test_parser_total_power_matches_sum_of_rail_powers():
    """The total is the integration's primary aggregate; it has to
    agree exactly with the sum of per-rail power across every V+I rail."""
    data = _parse(SAMPLE_PMIC_OUTPUT)
    manual = sum(r.power or 0 for r in data.rails.values() if r.power is not None)
    assert abs(data.total_power - manual) < 1e-9


def test_parser_ignores_unknown_lines():
    """A spurious header or firmware addition must not raise or lose rails."""
    noisy = "VC version b1a2c3d\n" + SAMPLE_PMIC_OUTPUT + "\nendblock\n"
    data = _parse(noisy)
    assert data.rails["VDD_CORE"].voltage is not None


async def test_coordinator_kills_subprocess_on_timeout(hass):
    """A hung vcgencmd must be reaped on timeout so repeated polls don't
    accumulate zombie processes."""
    proc = MagicMock()
    proc.communicate = AsyncMock(side_effect=TimeoutError)
    proc.kill = MagicMock()
    proc.wait = AsyncMock()

    with (
        patch(
            "custom_components.pi5_power_monitor.coordinator.asyncio.create_subprocess_exec",
            AsyncMock(return_value=proc),
        ),
        patch(
            "custom_components.pi5_power_monitor.coordinator.asyncio.wait_for",
            AsyncMock(side_effect=TimeoutError),
        ),
    ):
        coord = Pi5PowerMonitorCoordinator(hass, 30)
        with pytest.raises(UpdateFailed):
            await coord._async_update_data()

    proc.kill.assert_called_once()
    proc.wait.assert_awaited_once()


def test_parser_handles_empty_output():
    """Empty output must leave total_power as None so energy dashboards do
    not ingest a fake 0 W baseline when the parser recognized nothing."""
    data = _parse("")
    assert data.total_power is None
    assert data.rails["VDD_CORE"].voltage is None
    assert data.rails["VDD_CORE"].current is None
    assert data.rails["VDD_CORE"].power is None
