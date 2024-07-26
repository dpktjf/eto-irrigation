"""Adds config flow for ETO."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.components.sensor.const import (
    DOMAIN as SENSOR_DOMAIN,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithConfigEntry,
)

# https://github.com/home-assistant/core/blob/master/homeassistant/const.py
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    CONF_ALBEDO,
    CONF_HUMIDITY_MAX,
    CONF_HUMIDITY_MIN,
    CONF_RAIN,
    CONF_SOLAR_RAD,
    CONF_SPRINKLER_THROUGHPUT,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
    DOMAIN,
)


@callback
def configured_instances(hass: HomeAssistant) -> set[str]:
    """Return a set of configured instances."""
    entries = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        entries.append(entry.data.get(CONF_NAME))  # noqa: PERF401
    return set(entries)


def _get_data_schema(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: ConfigEntry | None = None,
) -> vol.Schema:
    """Get a schema with default values."""
    # If tracking home or no config entry is passed in, default value come from
    # Home location
    entity_selector = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=[SENSOR_DOMAIN],
            multiple=False,
        ),
    )
    if config_entry is None:
        # sections: https://developers.home-assistant.io/docs/data_entry_flow_index/
        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=({}).get(CONF_NAME, vol.UNDEFINED),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                    ),
                ),
                vol.Required(CONF_TEMP_MIN): entity_selector,
                vol.Required(CONF_TEMP_MAX): entity_selector,
                vol.Required(CONF_HUMIDITY_MIN): entity_selector,
                vol.Required(CONF_HUMIDITY_MAX): entity_selector,
                vol.Required(CONF_WIND): entity_selector,
                vol.Required(CONF_RAIN): entity_selector,
                vol.Required(CONF_SOLAR_RAD): entity_selector,
                vol.Required(CONF_ALBEDO): entity_selector,
                vol.Required(CONF_SPRINKLER_THROUGHPUT): entity_selector,
            }
        )
    # Not tracking home, default values come from config entry
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME,
                default=config_entry.data.get(CONF_NAME),  # type: ignore  # noqa: PGH003
            ): cv.string,
            vol.Required(
                CONF_TEMP_MIN,
                default=config_entry.data.get(CONF_TEMP_MIN),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_TEMP_MAX,
                default=config_entry.data.get(CONF_TEMP_MIN),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_HUMIDITY_MIN,
                default=config_entry.data.get(CONF_HUMIDITY_MIN),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_HUMIDITY_MAX,
                default=config_entry.data.get(CONF_HUMIDITY_MAX),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_WIND,
                default=config_entry.data.get(CONF_WIND),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_RAIN,
                default=config_entry.data.get(CONF_RAIN),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_SOLAR_RAD,
                default=config_entry.data.get(CONF_SOLAR_RAD),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_ALBEDO,
                default=config_entry.data.get(CONF_ALBEDO),  # type: ignore  # noqa: PGH003
            ): entity_selector,
            vol.Required(
                CONF_SPRINKLER_THROUGHPUT,
                default=config_entry.data.get(CONF_SPRINKLER_THROUGHPUT),  # type: ignore  # noqa: PGH003
            ): entity_selector,
        }
    )


class ETOFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ETO."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            if user_input.get(CONF_NAME) not in configured_instances(self.hass):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            _errors[CONF_NAME] = "already_configured"

        return self.async_show_form(
            step_id="user",
            data_schema=_get_data_schema(self.hass),
            errors=_errors,
        )

    async def async_step_onboarding(
        self,
        data: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> ConfigFlowResult:
        """Handle a flow initialized by onboarding."""
        return self.async_create_entry(title="Home", data={})

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for ETO."""
        return ETOOptionsFlowHandler(config_entry)


class ETOOptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Options flow for ETO component."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure options for ETO."""
        if user_input is not None:
            # Update config entry with data from user input
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=user_input
            )
            return self.async_create_entry(
                title=self._config_entry.title, data=user_input
            )

        return self.async_show_form(
            step_id="init",
            data_schema=_get_data_schema(self.hass, config_entry=self._config_entry),
        )
