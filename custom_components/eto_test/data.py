"""Custom types for eto_test."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    #from homeassistant.loader import Integration

    from .api import ETOApiClient
    from .coordinator import ETODataUpdateCoordinator


type ETOConfigEntry = ConfigEntry[ETOData]


@dataclass
class ETOData:
    """Data for the ETO Test."""

    name: str
    client: ETOApiClient
    coordinator: ETODataUpdateCoordinator
    #integration: Integration
