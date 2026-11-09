"""Capteurs : statut et prochain changement de chaque groupe."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SplitSchedulerConfigEntry
from .const import STATUSES
from .entity import GroupEntity
from .scheduler import SplitScheduler


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SplitSchedulerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    scheduler = entry.runtime_data
    entities: list[SensorEntity] = []
    for gid in scheduler.groups:
        entities += [StatusSensor(scheduler, gid), NextChangeSensor(scheduler, gid)]
    async_add_entities(entities)


class StatusSensor(GroupEntity, SensorEntity):
    """Programmé, dérogation, programmation désactivée ou sans programme."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUSES
    _attr_icon = "mdi:list-status"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "status")

    @property
    def native_value(self) -> str:
        return self.scheduler.status(self.group_id)


class NextChangeSensor(GroupEntity, SensorEntity):
    """Date du prochain changement de profil programmé."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "next_change")

    @property
    def native_value(self) -> datetime | None:
        return self.group_state.next_change

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"prochain_profil": self.scheduler.profile_name(self.group_state.next_profile_id)}
