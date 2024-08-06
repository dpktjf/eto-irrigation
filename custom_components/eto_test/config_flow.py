"""Adds config flow for ETO."""

from __future__ import annotations

import logging
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
from homeassistant.core import callback
from homeassistant.helpers import selector

from custom_components.eto_test.utils import build_data_and_options

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
    CONFIG_FLOW_VERSION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ETOConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for ETO."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> ETOOptionsFlow:
        """Get the options flow for this handler."""
        return ETOOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        description_placeholders = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME].lower())
            self._abort_if_unique_id_configured()

            data, options = build_data_and_options(user_input)
            _LOGGER.debug(
                "data=%s ,options=%s, user_input=%s", data, options, user_input
            )
            return self.async_create_entry(
                title=user_input[CONF_NAME], data=user_input, options={}
            )

        entity_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[SENSOR_DOMAIN],
                multiple=False,
            ),
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
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

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )


class ETOOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            _LOGGER.debug(
                "async_step_init: %s, config_entry=%s", user_input, self.config_entry
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self) -> vol.Schema:
        entity_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=[SENSOR_DOMAIN],
                multiple=False,
            ),
        )
        return vol.Schema(
            {
                vol.Required(
                    CONF_TEMP_MIN,
                    default=self.config_entry.options.get(
                        CONF_TEMP_MIN,
                        self.config_entry.data.get(CONF_TEMP_MIN),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_TEMP_MAX,
                    default=self.config_entry.options.get(
                        CONF_TEMP_MAX,
                        self.config_entry.data.get(CONF_TEMP_MAX),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_HUMIDITY_MIN,
                    default=self.config_entry.options.get(
                        CONF_HUMIDITY_MIN,
                        self.config_entry.data.get(CONF_HUMIDITY_MIN),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_HUMIDITY_MAX,
                    default=self.config_entry.options.get(
                        CONF_HUMIDITY_MAX,
                        self.config_entry.data.get(CONF_HUMIDITY_MAX),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_WIND,
                    default=self.config_entry.options.get(
                        CONF_WIND,
                        self.config_entry.data.get(CONF_WIND),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_RAIN,
                    default=self.config_entry.options.get(
                        CONF_RAIN,
                        self.config_entry.data.get(CONF_RAIN),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_SOLAR_RAD,
                    default=self.config_entry.options.get(
                        CONF_SOLAR_RAD,
                        self.config_entry.data.get(CONF_SOLAR_RAD),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_ALBEDO,
                    default=self.config_entry.options.get(
                        CONF_ALBEDO,
                        self.config_entry.data.get(CONF_ALBEDO),
                    ),
                ): entity_selector,
                vol.Required(
                    CONF_SPRINKLER_THROUGHPUT,
                    default=self.config_entry.options.get(
                        CONF_SPRINKLER_THROUGHPUT,
                        self.config_entry.data.get(CONF_SPRINKLER_THROUGHPUT),
                    ),
                ): entity_selector,
            }
        )
