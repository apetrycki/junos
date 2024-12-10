"""Support for Junos sensors."""
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfPower,
    UnitOfVolumeFlowRate
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from . import JunosData

from .const import (
    _LOGGER,
    DOMAIN,
    COORDINATOR,
)

SENSOR_TYPES = {
    "enum": {
        "icon": "mdi:ethernet",
    },
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add a Junos Sensor entity from a config_entry."""

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: JunosData = data[COORDINATOR]

    sensors = coordinator.junos.get_sensors()
    for sensor in sensors:
        async_add_entities([JunosSensor(coordinator, sensor["name"], sensor["name"].index)], True)

class JunosSensor(SensorEntity):
    """Representation of a Junos sensor."""

    def __init__(self, data, sensor_name, sensor_index):
        """Initialize the sensor."""
        self.data = data
        self._name = sensor_name
        self._attr_unique_id = f"{data.junos.serial_number}-{self._name}"
        self._model = data.junos.description
        self._sensor_name = sensor_name
        self._type = "enum"
        self._options = ["up", "down"]
        self._index = sensor_index
        self._state = None
        self._native_unit_of_measurement = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this Junos device."""
        return self.data.device_info

    @property
    def name(self):
        """Return the name of the Junos sensor."""
        return self._name

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._type

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return SENSOR_TYPES[self._type]["icon"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._native_unit_of_measurement

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            "input_bps": self.input_bps,
            "input_pps": self.input_pps,
            "output_bps": self.output_bps,
            "output_pps": self.output_pps,
            "alarms": self.alarms
        }
    async def async_update(self):
        """Get the latest state of the sensor."""
        await self.data._async_update_data()
        self.sensors = self.data.junos.get_sensors()
        for sensor in self.sensors:
            if self._sensor_name == sensor["name"]:
                self._state = sensor["oper_status"]
                self.input_bps = sensor["input_bps"]
                self.input_pps = sensor["input_pps"]
                self.output_bps = sensor["output_bps"]
                self.output_pps = sensor["output_pps"]
                self.alarms = sensor["active_alarms"]
