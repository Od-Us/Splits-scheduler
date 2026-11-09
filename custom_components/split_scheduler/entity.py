"""Entités de base."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, TITLE
from .scheduler import SplitScheduler


class SchedulerEntity(Entity):
    """Entité tenue à jour par le moteur de programmation."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, scheduler: SplitScheduler, key: str) -> None:
        self.scheduler = scheduler
        self._attr_translation_key = key
        entry_id = scheduler.entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)}, name=TITLE, entry_type=DeviceEntryType.SERVICE
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.scheduler.async_add_listener(self.async_write_ha_state))


class GroupEntity(SchedulerEntity):
    """Entité rattachée à un groupe de splits (un appareil par groupe)."""

    def __init__(self, scheduler: SplitScheduler, group_id: str, key: str) -> None:
        super().__init__(scheduler, key)
        self.group_id = group_id
        entry_id = scheduler.entry.entry_id
        self._attr_unique_id = f"{entry_id}_{group_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{group_id}")},
            name=scheduler.groups[group_id]["name"],
            model="Groupe de splits",
            via_device=(DOMAIN, entry_id),
        )

    @property
    def group_state(self):
        return self.scheduler.states[self.group_id]
