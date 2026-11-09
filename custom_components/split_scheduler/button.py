"""Bouton « Reprendre la programmation » de chaque groupe."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    async_add_entities(ResumeButton(scheduler, gid) for gid in scheduler.groups)


class ResumeButton(GroupEntity, ButtonEntity):
    """Annule la dérogation et réapplique tout de suite le profil programmé."""

    _attr_icon = "mdi:calendar-sync"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "resume")

    async def async_press(self) -> None:
        await self.scheduler.async_resume(self.group_id)
