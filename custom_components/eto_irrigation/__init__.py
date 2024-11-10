"""
Custom integration to integrate eto_irrigation with Home Assistant.

For more details about this integration, please refer to
https://github.com/dpktjf/eto-irrigation
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import (
    CONF_NAME,
    # CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.helpers.event import async_track_state_change_event

from .api import ETOApiClient
from .const import (
    CONF_ALBEDO,
    CONF_HUMIDITY_MAX,
    CONF_HUMIDITY_MIN,
    CONF_SOLAR_RAD,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
)
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

# https://homeassistantapi.readthedocs.io/en/latest/api.html

DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ETOConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    _name = entry.data[CONF_NAME]

    eto_api = ETOApiClient(
        name=_name,
        latitude=hass.config.latitude,
        longitude=hass.config.longitude,
        elevation=hass.config.elevation,
        config=entry,
    )
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    coordinator = ETODataUpdateCoordinator(eto_api, hass)

    _min_temp = entry.options.get(CONF_TEMP_MIN)
    _max_temp = entry.options.get(CONF_TEMP_MAX)
    _min_hum = entry.options.get(CONF_HUMIDITY_MIN)
    _max_hum = entry.options.get(CONF_HUMIDITY_MAX)
    _wind = entry.options.get(CONF_WIND)
    _solar_rad = entry.options.get(CONF_SOLAR_RAD)
    _albedo = entry.options.get(CONF_ALBEDO)
    _entities = []
    for entity in [
        _min_temp,
        _max_temp,
        _min_hum,
        _max_hum,
        _wind,
        _solar_rad,
        _albedo,
    ]:
        if entity is not None:
            _entities.append(entity)  # noqa: PERF401
    entry.async_on_unload(
        async_track_state_change_event(
            hass,
            _entities,
            coordinator.async_check_entity_state_change,
        )
    )

    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    entry.runtime_data = ETOData(_name, eto_api, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_options(hass: HomeAssistant, entry: ETOConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ETOConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
