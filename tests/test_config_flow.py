# Copyright (c) 2026 Kenneth Baker <bakerkj@umich.edu>
# All rights reserved.

"""Config and options flow tests."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pi5_power_monitor.const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


async def test_user_flow_creates_entry_with_defaults(hass):
    """Zero-input create seeds scan_interval with its documented default."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry"
    assert result["options"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL


async def test_user_flow_is_single_instance(hass):
    """A second attempt aborts via HA's single_config_entry manifest guard."""
    existing = MockConfigEntry(domain=DOMAIN, options={})
    existing.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "abort"
    assert result["reason"] in {"single_instance_allowed", "already_configured"}


async def test_options_flow_updates_scan_interval(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_SCAN_INTERVAL: 60},
    )
    assert result["type"] == "create_entry"
    assert result["data"][CONF_SCAN_INTERVAL] == 60
