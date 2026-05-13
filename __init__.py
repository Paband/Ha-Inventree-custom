"""InvenTree Custom Integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_URL, CONF_API_KEY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import InvenTreeCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up InvenTree Custom from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = InvenTreeCoordinator(
        hass,
        url=entry.data[CONF_URL],
        api_key=entry.data[CONF_API_KEY],
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: InvenTreeCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.async_shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
