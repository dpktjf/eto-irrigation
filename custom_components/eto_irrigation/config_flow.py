"""Adds config flow for ETO."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.sensor.const import (
    DOMAIN as SENSOR_DOMAIN,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)

# https://github.com/home-assistant/core/blob/master/homeassistant/const.py
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    _LOGGER,
    CONF_ALBEDO,
    CONF_HUMIDITY_MAX,
    CONF_HUMIDITY_MIN,
    CONF_SOLAR_RAD,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
    CONFIG_FLOW_VERSION,
    DOMAIN,
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
    }
)

OPTIONS = vol.Schema(
    {
        vol.Required(CONF_TEMP_MIN, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(CONF_TEMP_MAX, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(CONF_HUMIDITY_MIN, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(CONF_HUMIDITY_MAX, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(CONF_WIND, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(CONF_SOLAR_RAD, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
        vol.Required(CONF_ALBEDO, default=vol.UNDEFINED): selector.EntitySelector(
            selector.EntityFilterSelectorConfig(domain=[SENSOR_DOMAIN])
        ),
    }
)


@callback
def configured_instances(hass: HomeAssistant) -> set[str | None]:
    """Return a set of configured instances."""
    entries = [
        entry.data.get(CONF_NAME) for entry in hass.config_entries.async_entries(DOMAIN)
    ]
    return set(entries)


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for ETO."""

    VERSION = CONFIG_FLOW_VERSION

    def __init__(self) -> None:
        """Init method."""
        super().__init__()
        self.config: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Handle initial step."""
        if user_input:
            self.config = user_input
            if user_input[CONF_NAME] in configured_instances(self.hass):
                errors = {}
                errors[CONF_NAME] = "already_configured"
                return self.async_show_form(
                    step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
                )

            return await self.async_step_init()
        return self.async_show_form(step_id="user", data_schema=CONFIG_SCHEMA)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show basic config for vertical blinds."""
        if user_input is not None:
            self.config.update(user_input)
            return await self.async_step_update()

        return self.async_show_form(
            step_id="init",
            data_schema=OPTIONS,
        )

    async def async_step_update(
        self,
        user_input: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> ConfigFlowResult:
        """Create entry."""
        return self.async_create_entry(
            title=self.config[CONF_NAME],
            data={
                CONF_NAME: self.config[CONF_NAME],
            },
            options={
                CONF_TEMP_MIN: self.config.get(CONF_TEMP_MIN),
                CONF_TEMP_MAX: self.config.get(CONF_TEMP_MAX),
                CONF_HUMIDITY_MIN: self.config.get(CONF_HUMIDITY_MIN),
                CONF_HUMIDITY_MAX: self.config.get(CONF_HUMIDITY_MAX),
                CONF_WIND: self.config.get(CONF_WIND),
                CONF_SOLAR_RAD: self.config.get(CONF_SOLAR_RAD),
                CONF_ALBEDO: self.config.get(CONF_ALBEDO),
            },
        )


class OptionsFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.current_config: dict = dict(config_entry.data)
        self.options = dict(config_entry.options)
        _LOGGER.debug("options=%s", self.options)

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        schema = OPTIONS
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or self.options
            ),
        )

    async def _update_options(self) -> ConfigFlowResult:
        """Update config entry options."""
        return self.async_create_entry(title="", data=self.options)
