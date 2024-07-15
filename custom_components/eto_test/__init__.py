"""
Custom integration to integrate eto_test with Home Assistant.

For more details about this integration, please refer to
https://github.com/dpktjf/eto-test
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_loaded_integration

from .api import ETOApiClient
from .const import DEFAULT_NAME, DOMAIN
from .coordinator import ETODataUpdateCoordinator
from .data import ETOData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ETOConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    # Platform.BINARY_SENSOR,
    # Platform.SWITCH,
]

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

ETO_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,  # type: ignore
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,  # type: ignore
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [vol.Any(ETO_SCHEMA)])}, extra=vol.ALLOW_EXTRA
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Will setup the ETO platform."""
    hass.data[DOMAIN] = {}
    for entry in config[DOMAIN]:
        _LOGGER.debug("entry: %s", entry)

        if entry[CONF_NAME] in hass.data[DOMAIN]:
            _LOGGER.error(
                "Instance %s is duplicate, please assign an unique name",
                entry[CONF_NAME],
            )
            return False

    return True


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ETOConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    _LOGGER.debug("async_setup_entry")
    coordinator = ETODataUpdateCoordinator(
        hass=hass,
    )
    entry.runtime_data = ETOData(
        client=ETOApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ETOConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    _LOGGER.debug("async_unload_entry")
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ETOConfigEntry,
) -> None:
    """Reload config entry."""
    _LOGGER.debug("async_reload_entry")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
