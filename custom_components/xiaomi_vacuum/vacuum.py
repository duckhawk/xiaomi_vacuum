"""Xiaomi Vacuum."""
from __future__ import annotations

from datetime import timedelta
from functools import partial
import logging

import voluptuous as vol
from miio import DeviceException, G1Vacuum
from miio.integrations.vacuum.mijia.g1vacuum import G1FanSpeed, G1State, G1WaterLevel

from homeassistant.components.vacuum import (
    PLATFORM_SCHEMA,
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.helpers import config_validation as cv, entity_platform

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Vacuum cleaner"
DATA_KEY = "vacuum.xiaomi_vacuum"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)

ATTR_STATUS = "status"
ATTR_ERROR = "error"
ATTR_FAN_SPEED = "fan_speed"
ATTR_CLEANING_TIME = "cleaning_time"
ATTR_CLEANING_AREA = "cleaning_area"
ATTR_MAIN_BRUSH_LEFT_TIME = "main_brush_time_left"
ATTR_MAIN_BRUSH_LIFE_LEVEL = "main_brush_life_level"
ATTR_SIDE_BRUSH_LEFT_TIME = "side_brush_time_left"
ATTR_SIDE_BRUSH_LIFE_LEVEL = "side_brush_life_level"
ATTR_FILTER_LIFE_LEVEL = "filter_life_level"
ATTR_FILTER_LEFT_TIME = "filter_left_time"
ATTR_SENSOR_DIRTY_LEFT = "sensor_dirty_left"
ATTR_BATTERY_LEVEL = "battery_level"
ATTR_ZONE_ARRAY = "zone"
ATTR_ZONE_REPEATER = "repeats"
ATTR_WATER_LEVEL = "water_level"

SERVICE_CLEAN_ZONE = "vacuum_clean_zone"
SERVICE_WATER_LEVEL = "set_water_level"

SUPPORT_XIAOMI = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.START
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.FAN_SPEED
)

G1_STATE_TO_ACTIVITY = {
    G1State.Idle: VacuumActivity.IDLE,
    G1State.Sweeping: VacuumActivity.CLEANING,
    G1State.Paused: VacuumActivity.PAUSED,
    G1State.Error: VacuumActivity.ERROR,
    G1State.Charging: VacuumActivity.DOCKED,
    G1State.GoCharging: VacuumActivity.RETURNING,
}

SPEED_CODE_TO_NAME = {
    G1FanSpeed.Mute: "Mute",
    G1FanSpeed.Standard: "Standard",
    G1FanSpeed.Medium: "Medium",
    G1FanSpeed.High: "High",
}

WATER_CODE_TO_NAME = {
    G1WaterLevel.Low: "Low",
    G1WaterLevel.Medium: "Med",
    G1WaterLevel.High: "High",
}


def _timedelta_minutes(value: timedelta | None) -> int | None:
    if value is None:
        return None
    return int(value.total_seconds() / 60)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Xiaomi vacuum cleaner robot platform."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config[CONF_HOST]
    token = config[CONF_TOKEN]
    name = config[CONF_NAME]

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:8])
    vacuum = G1Vacuum(host, token)

    entity = MiroboVacuum(name, vacuum)
    hass.data[DATA_KEY][host] = entity

    async_add_entities([entity], update_before_add=True)

    platform = entity_platform.current_platform.get()

    platform.async_register_entity_service(
        SERVICE_CLEAN_ZONE,
        {
            vol.Required(ATTR_ZONE_ARRAY): cv.string,
            vol.Required(ATTR_ZONE_REPEATER): vol.All(
                vol.Coerce(int), vol.Clamp(min=1, max=3)
            ),
        },
        MiroboVacuum.async_clean_zone.__name__,
    )

    platform.async_register_entity_service(
        SERVICE_WATER_LEVEL,
        {vol.Required(ATTR_WATER_LEVEL): cv.string},
        MiroboVacuum.async_set_water_level.__name__,
    )


class MiroboVacuum(StateVacuumEntity):
    """Representation of a Xiaomi Vacuum cleaner robot."""

    def __init__(self, name: str, vacuum: G1Vacuum) -> None:
        self._attr_name = name
        self._vacuum = vacuum
        self._fan_speeds_reverse: dict[str, int] | None = None
        self._water_level_reverse: dict[str, int] | None = None
        self._attr_activity: VacuumActivity | None = None
        self._error: str | None = None
        self._battery_percentage: int | None = None
        self._current_fan_speed: int | None = None
        self._main_brush_time_left: int | None = None
        self._main_brush_life_level: int | None = None
        self._side_brush_time_left: int | None = None
        self._side_brush_life_level: int | None = None
        self._filter_life_level: int | None = None
        self._filter_left_time: int | None = None
        self._cleaning_area: int | None = None
        self._cleaning_time: int | None = None
        self._current_water_level: int | None = None

    @property
    def fan_speed(self) -> str | None:
        if self._current_fan_speed is None or self._fan_speeds_reverse is None:
            return None
        for speed, code in self._fan_speeds_reverse.items():
            if code == self._current_fan_speed:
                return speed
        return str(self._current_fan_speed)

    @property
    def fan_speed_list(self) -> list[str]:
        if self._fan_speeds_reverse is None:
            return []
        return list(self._fan_speeds_reverse)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        if self._attr_activity is None:
            return None
        return {
            ATTR_STATUS: self._attr_activity,
            ATTR_ERROR: self._error,
            ATTR_FAN_SPEED: self.fan_speed,
            ATTR_BATTERY_LEVEL: self._battery_percentage,
            ATTR_MAIN_BRUSH_LEFT_TIME: self._main_brush_time_left,
            ATTR_MAIN_BRUSH_LIFE_LEVEL: self._main_brush_life_level,
            ATTR_SIDE_BRUSH_LEFT_TIME: self._side_brush_time_left,
            ATTR_SIDE_BRUSH_LIFE_LEVEL: self._side_brush_life_level,
            ATTR_FILTER_LIFE_LEVEL: self._filter_life_level,
            ATTR_FILTER_LEFT_TIME: self._filter_left_time,
            ATTR_SENSOR_DIRTY_LEFT: self._filter_life_level,
            ATTR_CLEANING_AREA: self._cleaning_area,
            ATTR_CLEANING_TIME: self._cleaning_time,
            ATTR_WATER_LEVEL: self._water_level_name,
            "water_level_list": list(WATER_CODE_TO_NAME.values()),
        }

    @property
    def supported_features(self) -> VacuumEntityFeature:
        return SUPPORT_XIAOMI

    @property
    def _water_level_name(self) -> str | None:
        if self._current_water_level is None or self._water_level_reverse is None:
            return None
        for name, code in self._water_level_reverse.items():
            if code == self._current_water_level:
                return name
        return str(self._current_water_level)

    async def _try_command(self, mask_error: str, func, *args, **kwargs) -> bool:
        try:
            await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
            return True
        except (DeviceException, OSError) as exc:
            _LOGGER.error(mask_error, exc)
            return False

    async def async_locate(self, **kwargs) -> None:
        await self._try_command("Unable to locate the vacuum: %s", self._vacuum.find)

    async def async_start(self) -> None:
        await self._try_command("Unable to start the vacuum: %s", self._vacuum.start)

    async def async_stop(self, **kwargs) -> None:
        await self._try_command("Unable to stop the vacuum: %s", self._vacuum.stop)

    async def async_clean_zone(self, zone: str, repeats: int = 1) -> None:
        await self._try_command(
            "Unable to send zoned_clean command to the vacuum: %s",
            self._vacuum.zone_cleanup,
            zone,
        )

    async def async_pause(self) -> None:
        await self._try_command("Unable to pause the vacuum: %s", self._vacuum.stop)

    async def async_return_to_base(self, **kwargs) -> None:
        await self._try_command("Unable to return home: %s", self._vacuum.home)

    async def async_set_fan_speed(self, fan_speed: str, **kwargs) -> None:
        if self._fan_speeds_reverse is None:
            return
        if fan_speed in self._fan_speeds_reverse:
            speed = self._fan_speeds_reverse[fan_speed]
        else:
            try:
                speed = int(fan_speed)
            except ValueError as exc:
                _LOGGER.error(
                    "Fan speed step not recognized (%s). Valid speeds are: %s",
                    exc,
                    self.fan_speed_list,
                )
                return
        await self._try_command(
            "Unable to set fan speed: %s",
            self._vacuum.set_fan_speed_preset,
            speed,
        )

    async def async_set_water_level(self, water_level: str, **kwargs) -> None:
        if self._water_level_reverse is None:
            return
        if water_level in self._water_level_reverse:
            level = self._water_level_reverse[water_level]
        else:
            try:
                level = int(water_level)
            except ValueError as exc:
                _LOGGER.error(
                    "Water level step not recognized (%s). Valid are: %s",
                    exc,
                    list(self._water_level_reverse),
                )
                return
        await self._try_command(
            "Unable to set water level: %s",
            self._vacuum.set_water_level,
            level,
        )

    async def async_update(self) -> None:
        await self.hass.async_add_executor_job(self._update_state)

    def _update_state(self) -> None:
        try:
            state = self._vacuum.status()
        except (DeviceException, OSError, TimeoutError) as exc:
            _LOGGER.warning("Unable to fetch vacuum state: %s", exc)
            return

        self._fan_speeds_reverse = {
            name: speed.value for speed, name in SPEED_CODE_TO_NAME.items()
        }
        self._water_level_reverse = {
            name: level.value for level, name in WATER_CODE_TO_NAME.items()
        }

        self._attr_activity = G1_STATE_TO_ACTIVITY.get(state.state)
        self._error = state.error
        self._battery_percentage = state.battery
        self._current_fan_speed = state.fan_speed.value
        self._main_brush_time_left = _timedelta_minutes(state.main_brush_time_left)
        self._main_brush_life_level = state.main_brush_life_level
        self._side_brush_time_left = _timedelta_minutes(state.side_brush_time_left)
        self._side_brush_life_level = state.side_brush_life_level
        self._filter_life_level = state.filter_life_level
        self._filter_left_time = _timedelta_minutes(state.filter_time_left)
        self._cleaning_area = state.clean_area
        self._cleaning_time = _timedelta_minutes(state.clean_time)
        self._current_water_level = state.water_level.value
