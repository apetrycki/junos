from __future__ import annotations

import asyncio
from typing import Any
from requests.exceptions import RequestException
from async_timeout import timeout
from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_PASSWORD, CONF_NAME
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandler,
)
from .const import (
    DOMAIN
)
import voluptuous as vol
from .junos import Junos

CONF_VERIFY = "verify"

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_VERIFY, default=True): bool
    }
)
OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA),
}

class JunosConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        self._abort_if_unique_id_configured()
        if user_input is not None:
            try:
                junos = Junos(config={
                    "URL": user_input.get(CONF_URL),
                    "USERNAME": user_input.get(CONF_NAME),
                    "PASSWORD": user_input.get(CONF_PASSWORD),
                    "VERIFY": user_input.get(CONF_VERIFY)
                })
                result = await self.hass.async_add_executor_job(junos.get_device_info)
            except RequestException:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    junos.url, raise_on_progress=False
                )
                
                return self.async_create_entry(
                    title=user_input[CONF_URL], data=user_input
                )
                  
        return self.async_show_form(
            step_id="user", 
            data_schema=vol.Schema(
            {
                vol.Required(CONF_URL): str,
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_VERIFY, default=True): bool
              }
        )  
        )
      
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SchemaOptionsFlowHandler:
        """Options callback for Junos."""
        return SchemaOptionsFlowHandler(config_entry, OPTIONS_FLOW)
