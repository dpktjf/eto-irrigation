"""DataUpdateCoordinator for eto_test."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ETOApiClient,
    ETOApiClientAuthenticationError,
    ETOApiClientError,
)
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ETOConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class ETODataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ETOConfigEntry

    def __init__(
        self,
        eto_client: ETOApiClient,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        self._eto_client = eto_client

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            self.logger.debug(self.config_entry)
            return await self._eto_client.async_get_data()
        except ETOApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except ETOApiClientError as exception:
            raise UpdateFailed(exception) from exception
