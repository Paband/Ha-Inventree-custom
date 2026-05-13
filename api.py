"""InvenTree API client."""
from __future__ import annotations

import aiohttp
import asyncio
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class InvenTreeApiError(Exception):
    """Raised when InvenTree API returns an error."""


class InvenTreeAuthError(Exception):
    """Raised when authentication fails."""


class InvenTreeClient:
    """Async client for the InvenTree REST API."""

    def __init__(self, url: str, api_key: str, session: aiohttp.ClientSession) -> None:
        self._base_url = url.rstrip("/")
        self._api_key = api_key
        self._session = session

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _get(self, endpoint: str, params: dict | None = None) -> Any:
        url = f"{self._base_url}/api/{endpoint.lstrip('/')}"
        try:
            async with self._session.get(url, headers=self._headers, params=params) as resp:
                if resp.status == 401:
                    raise InvenTreeAuthError("Invalid API key")
                if resp.status != 200:
                    raise InvenTreeApiError(f"HTTP {resp.status} from {url}")
                return await resp.json()
        except aiohttp.ClientConnectorError as err:
            raise InvenTreeApiError(f"Cannot connect to InvenTree: {err}") from err
        except asyncio.TimeoutError as err:
            raise InvenTreeApiError("Connection timed out") from err

    async def test_connection(self) -> bool:
        """Test that the connection and API key are valid."""
        await self._get("part/category/")
        return True

    async def get_all_parts(self) -> list[dict]:
        """Fetch all parts with stock information."""
        parts = []
        offset = 0
        limit = 100

        while True:
            data = await self._get("part/", params={"limit": limit, "offset": offset, "active": True})
            results = data.get("results", data) if isinstance(data, dict) else data
            parts.extend(results)

            # Handle paginated responses
            if isinstance(data, dict) and data.get("next"):
                offset += limit
            else:
                break

        return parts

    async def get_stock_for_part(self, part_id: int) -> float:
        """Get total stock quantity for a part."""
        data = await self._get("stock/", params={"part": part_id, "in_stock": True})
        results = data.get("results", data) if isinstance(data, dict) else data
        return sum(float(item.get("quantity", 0)) for item in results)

    async def get_parts_with_stock(self) -> list[dict]:
        """Fetch all parts and resolve their actual stock levels."""
        parts = await self.get_all_parts()
        enriched = []
        for part in parts:
            part_id = part.get("pk")
            # InvenTree returns 'in_stock' directly on the part object
            in_stock = float(part.get("in_stock", 0) or 0)
            minimum_stock = float(part.get("minimum_stock", 0) or 0)
            enriched.append({
                "pk": part_id,
                "name": part.get("name", "Unknown"),
                "description": part.get("description", ""),
                "ipn": part.get("IPN", ""),
                "category": part.get("category_detail", {}).get("name", "") if part.get("category_detail") else "",
                "in_stock": in_stock,
                "minimum_stock": minimum_stock,
                "low_stock": in_stock <= minimum_stock if minimum_stock > 0 else False,
                "units": part.get("units", ""),
            })
        return enriched
