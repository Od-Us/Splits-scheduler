"""Interrupteur d'activation de la programmation de chaque groupe."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SplitSchedulerConfigEntry
from .entity import GroupEntity
from .scheduler import SplitScheduler


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SplitSchedulerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    scheduler = entry.runtime_data
    async_add_entities(ProgrammingSwitch(scheduler, gid) for gid in scheduler.groups)


class ProgrammingSwitch(GroupEntity, SwitchEntity):
    """Programmation active (éteinte : plus aucun changement automatique)."""

    _attr_icon = "mdi:calendar-clock"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "programming")

    @property
    def is_on(self) -> bool:
        return self.group_state.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.scheduler.async_set_enabled(self.group_id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.scheduler.async_set_enabled(self.group_id, False)
