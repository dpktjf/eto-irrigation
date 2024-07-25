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
    # CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import ETOApiClient
from .const import (
    CONF_ALBEDO,
    CONF_HUMIDITY_MAX,
    CONF_HUMIDITY_MIN,
    CONF_RAIN,
    CONF_SOLAR_RAD,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import ETODataUpdateCoordinator
from .data import ETOData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType

    from .data import ETOConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    # Platform.BINARY_SENSOR,
    # Platform.SWITCH,
]

# https://homeassistantapi.readthedocs.io/en/latest/api.html

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

ETO_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,  # type: ignore  # noqa: PGH003
        vol.Optional(CONF_TEMP_MIN, default=CONF_TEMP_MIN): cv.string,  # type: ignore  # noqa: PGH003
        vol.Optional(CONF_TEMP_MAX, default=CONF_TEMP_MAX): cv.string,  # type: ignore  # noqa: PGH003
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [vol.Any(ETO_SCHEMA)])}, extra=vol.ALLOW_EXTRA
)


async def async_setup_skip(hass: HomeAssistant, config: ConfigType) -> bool:
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
            name=entry.data[CONF_NAME],
            latitude=hass.config.latitude,
            longitude=hass.config.longitude,
            elevation=hass.config.elevation,
            temp_min=entry.data[CONF_TEMP_MIN],
            temp_max=entry.data[CONF_TEMP_MAX],
            humidity_min=entry.data[CONF_HUMIDITY_MIN],
            humidity_max=entry.data[CONF_HUMIDITY_MAX],
            wind=entry.data[CONF_WIND],
            rain=entry.data[CONF_RAIN],
            solar_rad=entry.data[CONF_SOLAR_RAD],
            albedo=entry.data[CONF_ALBEDO],
            session=async_get_clientsession(hass),
            states=hass.states,
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
