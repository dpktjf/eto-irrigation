"""Sensor platform for eto_test."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfLength

from custom_components.eto_test.api import ETOApiClientError
from custom_components.eto_test.const import CALC_FSETO_35, CONF_ALBEDO, CONF_DOY, CONF_HUMIDITY_MAX, CONF_HUMIDITY_MIN, CONF_RAIN, CONF_SOLAR_RAD, CONF_TEMP_MAX, CONF_TEMP_MIN, CONF_WIND

from .entity import ETOEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ETODataUpdateCoordinator
    from .data import ETOConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="eto_test",
        name="Reference Evapotranspiration Value",
        icon="mdi:weather-rainy",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ETOConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        ETOSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ETOSensor(ETOEntity, SensorEntity):
    """eto_test Sensor class."""

    def __init__(
        self,
        coordinator: ETODataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        _LOGGER.debug(self.coordinator.data[CALC_FSETO_35])
        return self.coordinator.data[CALC_FSETO_35].round(2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the device specific state attributes."""
        attributes: dict[str, Any] = {}
        _LOGGER.debug("extra_state_attributes")

        try:
            attributes[CONF_TEMP_MIN] = self.coordinator.data[CONF_TEMP_MIN]
            attributes[CONF_TEMP_MAX] = self.coordinator.data[CONF_TEMP_MAX]
            attributes[CONF_HUMIDITY_MIN] = self.coordinator.data[CONF_HUMIDITY_MIN]
            attributes[CONF_HUMIDITY_MAX] = self.coordinator.data[CONF_HUMIDITY_MAX]
            attributes[CONF_RAIN] = self.coordinator.data[CONF_RAIN]
            attributes[CONF_WIND] = self.coordinator.data[CONF_WIND]
            attributes[CONF_ALBEDO] = self.coordinator.data[CONF_ALBEDO]
            attributes[CONF_SOLAR_RAD] = self.coordinator.data[CONF_SOLAR_RAD]
            attributes[CONF_DOY] = self.coordinator.data[CONF_DOY]
        except ETOApiClientError as ex:
            _LOGGER.exception(ex)  # noqa: TRY401

        return attributes
