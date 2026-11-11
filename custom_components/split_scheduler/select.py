"""Sélecteurs : profil et planning de chaque groupe, planning global."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SplitSchedulerConfigEntry
from .const import allowed_profiles
from .entity import GroupEntity, SchedulerEntity
from .scheduler import SplitScheduler


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SplitSchedulerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    scheduler = entry.runtime_data
    entities: list[SelectEntity] = [GlobalPlanningSelect(scheduler)]
    for gid in scheduler.groups:
        entities += [ProfileSelect(scheduler, gid), PlanningSelect(scheduler, gid)]
    async_add_entities(entities)


def _id_by_name(items: dict[str, dict], name: str) -> str:
    return next(iid for iid, item in items.items() if item["name"] == name)


class ProfileSelect(GroupEntity, SelectEntity):
    """Profil actif du groupe ; un choix manuel vaut jusqu'au prochain créneau."""

    _attr_icon = "mdi:thermostat-auto"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "profile")

    @property
    def options(self) -> list[str]:
        """Profils autorisés dans le planning actif du groupe (et le profil en cours)."""
        scheduler = self.scheduler
        planning = scheduler.plannings.get(self.group_state.planning_id, {})
        ids = allowed_profiles(planning, scheduler.profiles)
        active = self.group_state.active_profile_id
        if active in scheduler.profiles and active not in ids:
            ids = [pid for pid in scheduler.profiles if pid in ids or pid == active]
        return [scheduler.profiles[pid]["name"] for pid in ids]

    @property
    def current_option(self) -> str | None:
        return self.scheduler.profile_name(self.group_state.active_profile_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self.group_state
        return {
            "profil_programme": self.scheduler.profile_name(state.scheduled_profile_id),
            "derogation": state.override,
            "splits": self.scheduler.groups[self.group_id]["climates"],
            **self.scheduler.adaptation(self.group_id),
        }

    async def async_select_option(self, option: str) -> None:
        await self.scheduler.async_select_profile(
            self.group_id, _id_by_name(self.scheduler.profiles, option)
        )


class PlanningSelect(GroupEntity, SelectEntity):
    """Planning hebdomadaire suivi par le groupe."""

    _attr_icon = "mdi:calendar-week"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "planning")
        self._attr_options = [p["name"] for p in scheduler.plannings.values()]

    @property
    def current_option(self) -> str | None:
        planning = self.scheduler.plannings.get(self.group_state.planning_id)
        return planning["name"] if planning else None

    async def async_select_option(self, option: str) -> None:
        await self.scheduler.async_select_planning(
            self.group_id, _id_by_name(self.scheduler.plannings, option)
        )


class GlobalPlanningSelect(SchedulerEntity, SelectEntity):
    """Bascule tous les groupes sur un même planning."""

    _attr_icon = "mdi:calendar-multiple"

    def __init__(self, scheduler: SplitScheduler) -> None:
        super().__init__(scheduler, "global_planning")
        self._attr_options = [p["name"] for p in scheduler.plannings.values()]

    @property
    def current_option(self) -> str | None:
        """Le planning commun à tous les groupes, sinon inconnu (« mixte »)."""
        ids = {st.planning_id for st in self.scheduler.states.values()}
        if len(ids) != 1:
            return None
        planning = self.scheduler.plannings.get(ids.pop())
        return planning["name"] if planning else None

    async def async_select_option(self, option: str) -> None:
        await self.scheduler.async_select_planning_all(
            _id_by_name(self.scheduler.plannings, option)
        )
