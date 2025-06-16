"""Sample API Client."""

from __future__ import annotations

import datetime
from statistics import mean
from typing import TYPE_CHECKING, Any

from homeassistant.const import (
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    UnitOfSpeed,
)
from homeassistant.util.unit_conversion import SpeedConverter

from custom_components.eto_irrigation.api_helpers import (
    atm_pressure,
    c_to_k,
    cs_rad,
    deg2rad,
    delta_svp,
    delta_term,
    ea_from_rh,
    et_rad,
    eto,
    inv_rel_dist_earth_sun,
    net_in_sol_rad,
    net_out_lw_rad,
    net_rad,
    net_rad_eto,
    psi_term,
    psy_const,
    radiation_term,
    sol_dec,
    sunset_hour_angle,
    svp_from_t,
    temperature_term,
    wind_speed,
    wind_term,
)

from .const import (
    _LOGGER,
    CALC_FS_33,
    CALC_FS_34,
    CALC_FSETO_35,
    CALC_S1_5,
    CALC_S2_6,
    CALC_S3_7,
    CALC_S4_9,
    CALC_S5_10,
    CALC_S6_11,
    CALC_S7_12,
    CALC_S8_13,
    CALC_S9_14,
    CALC_S10_16,
    CALC_S10_17,
    CALC_S10_18,
    CALC_S11_19,
    CALC_S12_23,
    CALC_S12_24,
    CALC_S13_25,
    CALC_S14_26,
    CALC_S15_27,
    CALC_S16_28,
    CALC_S17_29,
    CALC_S18_30,
    CALC_S19_31,
    CALC_S19_32,
    CONF_ALBEDO,
    CONF_DOY,
    CONF_HUMIDITY_MAX,
    CONF_HUMIDITY_MIN,
    CONF_SOLAR_RAD,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
)

if TYPE_CHECKING:
    from .data import ETOConfigEntry


class ETOApiClientError(Exception):
    """Exception to indicate a general API error."""


class ETOApiClientCommunicationError(
    ETOApiClientError,
):
    """Exception to indicate a communication error."""


class ETOApiClientAuthenticationError(
    ETOApiClientError,
):
    """Exception to indicate an authentication error."""


class ETOApiClientCalculationError(
    ETOApiClientError,
):
    """Exception to indicate a calculation error."""


class ETOApiClientCalculationStartupError(
    ETOApiClientError,
):
    """Exception to indicate a calculation error - probably due to start-up ."""


class ETOApiClient:
    """Sample API Client."""

    def __init__(
        self,
        name: str,
        latitude: float,
        longitude: float,
        elevation: float,
        config: ETOConfigEntry,
    ) -> None:
        """Sample API Client."""
        self._name = name
        self._entities = {}
        self._entities[config.options[CONF_TEMP_MIN]] = None
        self._entities[config.options[CONF_TEMP_MAX]] = None
        self._entities[config.options[CONF_HUMIDITY_MIN]] = None
        self._entities[config.options[CONF_HUMIDITY_MAX]] = None
        self._entities[config.options[CONF_WIND]] = None
        self._entities[config.options[CONF_SOLAR_RAD]] = None
        self._entities[config.options[CONF_ALBEDO]] = None
        self._calc_data = {}
        self._calc_data[CONF_ELEVATION] = elevation
        self._calc_data[CONF_LATITUDE] = latitude
        self._calc_data[CONF_LONGITUDE] = longitude
        self._calc_data[CONF_TEMP_MIN] = None
        self._calc_data[CONF_TEMP_MAX] = None
        self._calc_data[CONF_HUMIDITY_MIN] = None
        self._calc_data[CONF_HUMIDITY_MAX] = None
        self._calc_data[CONF_WIND] = None
        self._calc_data[CONF_SOLAR_RAD] = None
        self._calc_data[CONF_ALBEDO] = None
        self._calc_data[CONF_DOY] = None
        self._calc_data[CALC_FSETO_35] = None
        self._config = config

    async def entity_update(self, entity_id: str, new_state: float) -> None:
        """Update to an entity pushed."""
        self._entities[entity_id] = new_state

    async def collect_calculation_data(self) -> None:
        """
        Collect all the necessary weather and other calculation data.

        Convert into the correct units for calculation.
        """
        # https://developers.home-assistant.io/docs/core/entity/sensor
        if self._entities[self._config.options[CONF_TEMP_MIN]] is None:
            _LOGGER.debug("CONF_TEMP_MIN no data yet")
        if self._entities[self._config.options[CONF_TEMP_MAX]] is None:
            _LOGGER.debug("CONF_TEMP_MAX no data yet")
        if self._entities[self._config.options[CONF_HUMIDITY_MIN]] is None:
            _LOGGER.debug("CONF_HUMIDITY_MIN no data yet")
        if self._entities[self._config.options[CONF_HUMIDITY_MAX]] is None:
            _LOGGER.debug("CONF_HUMIDITY_MAX no data yet")
        if self._entities[self._config.options[CONF_WIND]] is None:
            _LOGGER.debug("CONF_WIND no data yet")
        if self._entities[self._config.options[CONF_SOLAR_RAD]] is None:
            _LOGGER.debug("CONF_SOLAR_RAD no data yet")
        if self._entities[self._config.options[CONF_ALBEDO]] is None:
            _LOGGER.debug("CONF_ALBEDO no data yet")

        if (
            self._entities[self._config.options[CONF_TEMP_MIN]] is None
            or self._entities[self._config.options[CONF_TEMP_MAX]] is None
            or self._entities[self._config.options[CONF_HUMIDITY_MIN]] is None
            or self._entities[self._config.options[CONF_HUMIDITY_MAX]] is None
            or self._entities[self._config.options[CONF_WIND]] is None
            or self._entities[self._config.options[CONF_SOLAR_RAD]] is None
            or self._entities[self._config.options[CONF_ALBEDO]] is None
        ):
            _LOGGER.debug("no data yet")
            return

        try:
            self._calc_data[CONF_TEMP_MIN] = self._entities[
                self._config.options[CONF_TEMP_MIN]
            ]
            self._calc_data[CONF_TEMP_MAX] = self._entities[
                self._config.options[CONF_TEMP_MAX]
            ]
            _LOGGER.debug(
                "temp min/max = %s/%s",
                self._calc_data[CONF_TEMP_MIN],
                self._calc_data[CONF_TEMP_MAX],
            )
            self._calc_data[CONF_HUMIDITY_MIN] = (
                self._entities[self._config.options[CONF_HUMIDITY_MIN]] / 100
            )
            self._calc_data[CONF_HUMIDITY_MAX] = (
                self._entities[self._config.options[CONF_HUMIDITY_MAX]] / 100
            )
            self._calc_data[CONF_WIND] = self._entities[self._config.options[CONF_WIND]]
            self._calc_data[CONF_WIND] = SpeedConverter.convert(
                self._calc_data[CONF_WIND],
                UnitOfSpeed.KILOMETERS_PER_HOUR,
                UnitOfSpeed.METERS_PER_SECOND,
            )
            self._calc_data[CONF_SOLAR_RAD] = self._entities[
                self._config.options[CONF_SOLAR_RAD]
            ]
            self._calc_data[CONF_ALBEDO] = self._entities[
                self._config.options[CONF_ALBEDO]
            ]
            self._calc_data[CONF_DOY] = datetime.datetime.now().timetuple().tm_yday  # noqa: DTZ005

            await self.calc_eto()

            _LOGGER.debug("collect_calculation_data: %s", self._calc_data)
        except ValueError as exception:
            msg = f"Value error fetching information - {exception}"
            _LOGGER.exception(msg)
            raise ETOApiClientCalculationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            _LOGGER.exception(msg)
            raise ETOApiClientError(
                msg,
            ) from exception

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        await self.collect_calculation_data()
        return self._calc_data

    async def calc_eto(self) -> None:
        """Perform ETO calculation."""
        """Step 1: Mean daily temperature."""
        self._calc_data[CALC_S1_5] = mean(
            [self._calc_data[CONF_TEMP_MIN], self._calc_data[CONF_TEMP_MAX]]
        )

        """Step 2: Mean daily solar radiation (Rs)."""
        self._calc_data[CALC_S2_6] = self._calc_data[CONF_SOLAR_RAD] * 0.0864

        """Step 3: The average daily wind speed in meters per second (ms-1)
        measured at 2m above the ground level is required. OWM reprts at 10m."""
        self._calc_data[CALC_S3_7] = wind_speed(self._calc_data[CONF_WIND], 10)

        """Step 4: For the calculation of evapotranspiration, the slope of
        the relationship between saturation vapor pressure and
        temperature, Δ, is required."""
        self._calc_data[CALC_S4_9] = delta_svp(self._calc_data[CALC_S1_5])

        """Step 5: Atmospheric Pressure (P)"""
        self._calc_data[CALC_S5_10] = atm_pressure(self._calc_data[CONF_ELEVATION])

        """Step 6: Psychrometric constant (γ)"""  # noqa: RUF001
        self._calc_data[CALC_S6_11] = psy_const(self._calc_data[CALC_S5_10])

        """Step 7: Delta Term (DT) (auxiliary calculation for Radiation Term)"""
        self._calc_data[CALC_S7_12] = delta_term(
            self._calc_data[CALC_S4_9],
            self._calc_data[CALC_S6_11],
            self._calc_data[CALC_S3_7],
        )

        """Step 8: Psi Term (PT) (auxiliary calculation for Wind Term)"""
        self._calc_data[CALC_S8_13] = psi_term(
            self._calc_data[CALC_S4_9],
            self._calc_data[CALC_S6_11],
            self._calc_data[CALC_S3_7],
        )

        """Step 9: Temperature Term (TT) (aux calculation for Wind Term)"""
        self._calc_data[CALC_S9_14] = temperature_term(
            self._calc_data[CALC_S1_5], self._calc_data[CALC_S3_7]
        )

        """Step 10: Mean saturation vapor pressure derived from air temperature(es)"""
        self._calc_data[CALC_S10_16] = svp_from_t(self._calc_data[CONF_TEMP_MAX])
        self._calc_data[CALC_S10_17] = svp_from_t(self._calc_data[CONF_TEMP_MIN])
        self._calc_data[CALC_S10_18] = mean(
            [self._calc_data[CALC_S10_16], self._calc_data[CALC_S10_17]]
        )

        """Step 11: Actual vapor pressure (ea) derived from relative humidity"""
        self._calc_data[CALC_S11_19] = mean(
            [
                ea_from_rh(
                    self._calc_data[CALC_S10_16], self._calc_data[CONF_HUMIDITY_MIN]
                ),
                ea_from_rh(
                    self._calc_data[CALC_S10_17], self._calc_data[CONF_HUMIDITY_MAX]
                ),
            ]
        )

        """Step 12: The inverse relative distance Earth-Sun (dr) and solar
        declination (d)"""
        self._calc_data[CALC_S12_23] = inv_rel_dist_earth_sun(self._calc_data[CONF_DOY])
        self._calc_data[CALC_S12_24] = sol_dec(self._calc_data[CONF_DOY])

        """Step 13: Conversion of latitude (φ) in degrees to radians"""
        self._calc_data[CALC_S13_25] = deg2rad(self._calc_data[CONF_LATITUDE])

        """Step 14: Sunset hour angle (ωs)"""
        self._calc_data[CALC_S14_26] = sunset_hour_angle(
            self._calc_data[CALC_S13_25], self._calc_data[CALC_S12_24]
        )

        """Step 15: Extraterrestrial radiation (Ra)"""
        self._calc_data[CALC_S15_27] = et_rad(
            self._calc_data[CALC_S13_25],
            self._calc_data[CALC_S12_24],
            self._calc_data[CALC_S14_26],
            self._calc_data[CALC_S12_23],
        )

        """Step 16: Clear sky solar radiation (Rso)"""
        self._calc_data[CALC_S16_28] = cs_rad(
            self._calc_data[CONF_ELEVATION], self._calc_data[CALC_S15_27]
        )

        """Step 17: Net solar or net shortwave radiation (Rns)"""
        self._calc_data[CALC_S17_29] = net_in_sol_rad(
            self._calc_data[CALC_S2_6], self._calc_data[CONF_ALBEDO]
        )

        """Step 18: Net outgoing long wave solar radiation (Rnl)"""
        self._calc_data[CALC_S18_30] = net_out_lw_rad(
            c_to_k(self._calc_data[CONF_TEMP_MIN]),
            c_to_k(self._calc_data[CONF_TEMP_MAX]),
            self._calc_data[CALC_S2_6],
            self._calc_data[CALC_S16_28],
            self._calc_data[CALC_S11_19],
        )

        """Step 19: Net radiation (Rn)"""
        self._calc_data[CALC_S19_31] = net_rad(
            self._calc_data[CALC_S17_29], self._calc_data[CALC_S18_30]
        )
        self._calc_data[CALC_S19_32] = net_rad_eto(self._calc_data[CALC_S19_31])

        """FS1. Radiation term (ETrad)"""
        self._calc_data[CALC_FS_33] = radiation_term(
            self._calc_data[CALC_S7_12], self._calc_data[CALC_S19_32]
        )

        """FS2. Wind term (ETwind)"""
        self._calc_data[CALC_FS_34] = wind_term(
            self._calc_data[CALC_S8_13],
            self._calc_data[CALC_S9_14],
            self._calc_data[CALC_S11_19],
            self._calc_data[CALC_S10_18],
        )

        """Final Reference Evapotranspiration Value (ETo)"""
        self._calc_data[CALC_FSETO_35] = eto(
            self._calc_data[CALC_FS_34], self._calc_data[CALC_FS_33]
        )
