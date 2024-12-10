"""Daikin Skyport integration."""
import os
from datetime import timedelta
from async_timeout import timeout
from requests.exceptions import RequestException
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_NAME,
    CONF_URL,
    Platform
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle
from homeassistant.helpers.json import save_json
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .junos import Junos, InvalidCredentials
from .const import (
    _LOGGER,
    DOMAIN,
    MANUFACTURER,
    COORDINATOR,
)

CONF_VERIFY = "verify"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)
UNDO_UPDATE_LISTENER = "undo_update_listener"

NETWORK = None

#PLATFORMS = [Platform.SENSOR, Platform.SWITCH]
PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Junos as config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info("Juniper Junos Starting")

    url: str = entry.data[CONF_URL]
    password: str = entry.data[CONF_PASSWORD]
    username: str = entry.data[CONF_NAME]
    verify: bool = entry.data[CONF_VERIFY]
    config = {
        "URL": url,
        "USERNAME": username,
        "PASSWORD": password,
        "VERIFY": verify
    }
        
    assert entry.unique_id is not None
    unique_id = entry.unique_id

    _LOGGER.debug("Using URL: %s", url)
    
    device_info = Junos(config=config)
    await hass.async_add_executor_job(device_info.get_device_info)

    coordinator = JunosData(
        hass, config, unique_id, device_info.description, entry
    )

    try:
        await coordinator._async_update_data()
    except InvalidCredentials as ex:
        _LOGGER.warn("Unable to connect with credentials provided.")
        raise ConfigEntryNotReady("Unable to connect with credentials provided.")

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)

    undo_listener = entry.add_update_listener(update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unload Entry: %s", str(entry))
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Reload Entry: %s", str(entry))
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    _LOGGER.debug("Update listener: %s", str(entry))

class JunosData:
    """Get the latest data and update the states."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        config, 
        unique_id: str,
        description: str,
        entry: ConfigEntry) -> None:
        """Init the Junos data object."""
        self.platforms = []
        try:
            self.url: str = entry.data[CONF_URL]
        except (NameError, KeyError):
            _LOGGER.error("No URL in config")
        try:
            self.username: str = entry.data[CONF_NAME]
        except (NameError, KeyError):
            _LOGGER.error("No username in config")
        try:
            self.password: str = entry.data[CONF_PASSWORD]
        except (NameError, KeyError):
            _LOGGER.error("No password in config")
        self.verify: bool = entry.data[CONF_VERIFY]
        self.hass = hass
        self.entry = entry
        self.unique_id = unique_id
        self.junos = Junos(config=config)
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer=MANUFACTURER,
            model=description,
            name=self.url,
            )
        _LOGGER.debug("model: %s", description)
        
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _async_update_data(self):
        """Update data via library."""
        try:
            current = await self.hass.async_add_executor_job(self.junos.update)
            _LOGGER.debug("Junos _async_update_data")
        except BaseException as e:
            _LOGGER.debug("Junos update failed: %s", e)
        _LOGGER.debug("Junos data updated successfully")
        return

