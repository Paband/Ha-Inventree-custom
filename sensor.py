"""Sensors for InvenTree Custom integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InvenTreeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up InvenTree sensors from a config entry."""
    coordinator: InvenTreeCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Wait for first data
    await coordinator.async_config_entry_first_refresh()

    entities = []
    for part_id, part in coordinator.data.items():
        entities.append(InvenTreeStockSensor(coordinator, part_id))
        entities.append(InvenTreeLowStockSensor(coordinator, part_id))

    async_add_entities(entities, update_before_add=False)


def _device_info(part: dict, entry_id: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"part_{part['pk']}")},
        name=part["name"],
        manufacturer="InvenTree",
        model=part.get("category", "Part"),
        sw_version=part.get("ipn") or None,
    )


class InvenTreeStockSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing current stock level for a part."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: InvenTreeCoordinator, part_id: int) -> None:
        super().__init__(coordinator)
        self._part_id = part_id
        self._attr_unique_id = f"inventree_stock_{part_id}"

    @property
    def _part(self) -> dict:
        return self.coordinator.data.get(self._part_id, {})

    @property
    def name(self) -> str:
        return f"{self._part.get('name', self._part_id)} Stock"

    @property
    def native_value(self) -> float | None:
        return self._part.get("in_stock")

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._part.get("units") or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        part = self._part
        return {
            "part_id": part.get("pk"),
            "part_name": part.get("name"),
            "description": part.get("description"),
            "ipn": part.get("ipn"),
            "category": part.get("category"),
            "minimum_stock": part.get("minimum_stock"),
            "low_stock": part.get("low_stock"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._part, self.coordinator.config_entry.entry_id)

    @property
    def icon(self) -> str:
        return "mdi:package-variant-closed"


class InvenTreeLowStockSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that turns on when a part is below minimum stock."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: InvenTreeCoordinator, part_id: int) -> None:
        super().__init__(coordinator)
        self._part_id = part_id
        self._attr_unique_id = f"inventree_low_stock_{part_id}"

    @property
    def _part(self) -> dict:
        return self.coordinator.data.get(self._part_id, {})

    @property
    def name(self) -> str:
        return f"{self._part.get('name', self._part_id)} Low Stock"

    @property
    def is_on(self) -> bool | None:
        """True when stock is at or below minimum."""
        return self._part.get("low_stock")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        part = self._part
        return {
            "part_id": part.get("pk"),
            "part_name": part.get("name"),
            "in_stock": part.get("in_stock"),
            "minimum_stock": part.get("minimum_stock"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._part, self.coordinator.config_entry.entry_id)

    @property
    def icon(self) -> str:
        return "mdi:alert-circle" if self.is_on else "mdi:check-circle"
