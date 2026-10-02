# Copyright (c) 2026 Kenneth Baker <bakerkj@umich.edu>
# All rights reserved.

"""Sensor entities for the Raspberry Pi 5 Power Monitor integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_ENABLED_RAILS, DOMAIN, RAILS_V_AND_A, RAILS_V_ONLY
from .coordinator import Pi5PowerMonitorCoordinator, PmicData

if TYPE_CHECKING:
    from . import Pi5ConfigEntry


def _device_info(entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="Raspberry Pi 5 Power Monitor",
        manufacturer="Renesas / Raspberry Pi",
        model="DA9091",
    )


class _Base(CoordinatorEntity[Pi5PowerMonitorCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_suggested_display_precision = 3

    def __init__(
        self,
        coordinator: Pi5PowerMonitorCoordinator,
        entry_id: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = _device_info(entry_id)


class _RailSensor(_Base):
    def __init__(
        self,
        coordinator: Pi5PowerMonitorCoordinator,
        entry_id: str,
        description: SensorEntityDescription,
        selector_fn: Callable[[PmicData], float | None],
    ) -> None:
        super().__init__(coordinator, entry_id, description)
        self._selector = selector_fn

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        return self._selector(data) if data is not None else None


class _TotalPower(_Base):
    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        return data.total_power if data is not None else None


def _rail_descriptions(rail: str) -> list[tuple[SensorEntityDescription, str]]:
    enabled = rail in DEFAULT_ENABLED_RAILS
    out: list[tuple[SensorEntityDescription, str]] = [
        (
            SensorEntityDescription(
                key=f"{rail}_voltage",
                name=f"{rail} voltage",
                device_class=SensorDeviceClass.VOLTAGE,
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                state_class=SensorStateClass.MEASUREMENT,
                entity_registry_enabled_default=enabled,
            ),
            "voltage",
        ),
    ]
    if rail in RAILS_V_AND_A:
        out.append(
            (
                SensorEntityDescription(
                    key=f"{rail}_current",
                    name=f"{rail} current",
                    device_class=SensorDeviceClass.CURRENT,
                    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_registry_enabled_default=enabled,
                ),
                "current",
            )
        )
        out.append(
            (
                SensorEntityDescription(
                    key=f"{rail}_power",
                    name=f"{rail} power",
                    device_class=SensorDeviceClass.POWER,
                    native_unit_of_measurement=UnitOfPower.WATT,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_registry_enabled_default=enabled,
                ),
                "power",
            )
        )
    return out


def _rail_selector(rail: str, kind: str) -> Callable[[PmicData], float | None]:
    def _get(data: PmicData) -> float | None:
        return getattr(data.rails[rail], kind)

    return _get


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Pi5ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data

    entities: list[_Base] = []
    for rail in (*RAILS_V_AND_A, *RAILS_V_ONLY):
        for desc, kind in _rail_descriptions(rail):
            entities.append(
                _RailSensor(
                    coordinator, entry.entry_id, desc, _rail_selector(rail, kind)
                )
            )

    entities.append(
        _TotalPower(
            coordinator,
            entry.entry_id,
            SensorEntityDescription(
                key="total_power",
                name="Total power",
                device_class=SensorDeviceClass.POWER,
                native_unit_of_measurement=UnitOfPower.WATT,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )
    )
    async_add_entities(entities)
