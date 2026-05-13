"""Data coordinator for InvenTree Custom integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import InvenTreeClient, InvenTreeApiError, InvenTreeAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class InvenTreeCoordinator(DataUpdateCoordinator):
    """Polls InvenTree and shares data with all sensors."""

    def __init__(self, hass: HomeAssistant, url: str, api_key: str, scan_interval: int) -> None:
        self._url = url
        self._api_key = api_key
        self._session: aiohttp.ClientSession | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _get_client(self) -> InvenTreeClient:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return InvenTreeClient(self._url, self._api_key, self._session)

    async def _async_update_data(self) -> dict[int, dict]:
        """Fetch latest parts data from InvenTree."""
        try:
            client = await self._get_client()
            parts = await client.get_parts_with_stock()
            return {part["pk"]: part for part in parts}
        except InvenTreeAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except InvenTreeApiError as err:
            raise UpdateFailed(f"Error communicating with InvenTree: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_shutdown(self) -> None:
        """Close the aiohttp session on shutdown."""
        if self._session and not self._session.closed:
            await self._session.close()
        await super().async_shutdown()
