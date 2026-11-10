"""Capteurs : statut et prochain changement de chaque groupe."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SplitSchedulerConfigEntry
from .const import CONF_COMPRESSOR, STATUSES
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
        if scheduler.groups[gid].get(CONF_COMPRESSOR):
            entities += [
                CompressorStartsSensor(scheduler, gid, "compressor_starts_24h", 0),
                CompressorStartsSensor(scheduler, gid, "compressor_starts_profile", 1),
            ]
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


class CompressorStartsSensor(GroupEntity, SensorEntity):
    """Démarrages du compresseur par heure, en moyenne.

    Tous les splits du groupe sont supposés reliés au même compresseur.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "/h"
    _attr_icon = "mdi:sine-wave"
    _attr_suggested_display_precision = 1

    def __init__(self, scheduler: SplitScheduler, group_id: str, key: str, index: int) -> None:
        super().__init__(scheduler, group_id, key)
        self._index = index  # 0 : 24 h glissantes, 1 : depuis le dernier changement de profil

    def _average(self):
        averages = self.scheduler.compressor_averages(self.group_id)
        return averages[self._index] if averages else None

    @property
    def native_value(self) -> float | None:
        average = self._average()
        return average.per_hour if average else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        average = self._average()
        attrs: dict[str, Any] = {
            "capteur_compresseur": self.scheduler.groups[self.group_id].get(CONF_COMPRESSOR),
        }
        if average is not None:
            attrs.update(demarrages=average.starts, duree_h=average.hours, depuis=average.since.isoformat())
        if self._index == 1:
            attrs["profil"] = self.scheduler.profile_name(self.group_state.active_profile_id)
        return attrs
