"""Sample API Client."""

from __future__ import annotations

import datetime
import logging
import socket
from statistics import mean
from typing import TYPE_CHECKING, Any

import aiohttp
import async_timeout
from homeassistant.const import (
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
)

from custom_components.eto_test.api_helpers import (
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
from custom_components.eto_test.const import (
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
    CONF_RAIN,
    CONF_SOLAR_RAD,
    CONF_TEMP_MAX,
    CONF_TEMP_MIN,
    CONF_WIND,
)

if TYPE_CHECKING:
    from homeassistant.core import State, StateMachine

_LOGGER = logging.getLogger(__name__)


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


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise ETOApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class ETOApiClient:
    """Sample API Client."""

    def __init__(
        self,
        name: str,
        latitude: float,
        longitude: float,
        elevation: float,
        temp_min: str,
        temp_max: str,
        humidity_min: str,
        humidity_max: str,
        wind: str,
        rain: str,
        solar_rad: str,
        albedo: str,
        session: aiohttp.ClientSession,
        states: StateMachine,
    ) -> None:
        """Sample API Client."""
        self._name = name
        self._temp_min = temp_min
        self._temp_max = temp_max
        self._humidity_min = humidity_min
        self._humidity_max = humidity_max
        self._wind = wind
        self._rain = rain
        self._solar_rad = solar_rad
        self._albedo = albedo
        self._session = session
        self._states = states
        self._calc_data = {}
        self._calc_data[CONF_ELEVATION] = elevation
        self._calc_data[CONF_LATITUDE] = latitude
        self._calc_data[CONF_LONGITUDE] = longitude

    async def _get(self, ent) -> float:
        st = self._states.get(ent)
        if st is not None:
            try:
                return float(st.state)
            except ValueError:
                return -1
        return 0

    async def collect_calculation_data(self) -> None:
        """
        Collect all the necessary weather and other calculation data.

        Convert into the correct units for calculation.
        """
        # https://developers.home-assistant.io/docs/core/entity/sensor
        self._calc_data[CONF_TEMP_MIN] = await self._get(self._temp_min)
        self._calc_data[CONF_TEMP_MAX] = await self._get(self._temp_max)
        self._calc_data[CONF_HUMIDITY_MIN] = await self._get(self._humidity_min) / 100
        self._calc_data[CONF_HUMIDITY_MAX] = await self._get(self._humidity_max) / 100
        self._calc_data[CONF_WIND] = await self._get(self._wind)
        self._calc_data[CONF_RAIN] = await self._get(self._rain)
        self._calc_data[CONF_SOLAR_RAD] = await self._get(self._solar_rad)
        self._calc_data[CONF_ALBEDO] = await self._get(self._albedo)
        self._calc_data[CONF_DOY] = datetime.datetime.now().timetuple().tm_yday  # noqa: DTZ005

        await self.calc()
        _LOGGER.debug("collect_calculation_data: %s", self._calc_data)

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        _LOGGER.debug("async_get_data: %s", self._name)
        await self.collect_calculation_data()
        return await self._api_wrapper(
            method="get",
            url="https://jsonplaceholder.typicode.com/posts/1",
        )

    async def async_set_title(self, value: str) -> Any:
        """Get data from the API."""
        _LOGGER.debug("async_set_title: %s", self._name)
        return await self._api_wrapper(
            method="patch",
            url="https://jsonplaceholder.typicode.com/posts/1",
            data={"title": value},
            headers={"Content-type": "application/json; charset=UTF-8"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise ETOApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise ETOApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise ETOApiClientError(
                msg,
            ) from exception

    async def calc(self) -> None:
        """Perform ETO calculation."""
        _LOGGER.debug("calc...")

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

        """Step 6: Psychrometric constant (γ)"""
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
