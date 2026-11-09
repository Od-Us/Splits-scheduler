"""Moteur de programmation : minuteries, application des profils, dérogations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_point_in_time,
    async_track_state_change_event,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_SWING_HORIZONTAL_MODE,
    ATTR_SWING_MODE,
    ATTR_TEMPERATURE,
    CONF_CLIMATES,
    CONF_GROUPS,
    CONF_PLANNINGS,
    CONF_PROFILES,
    CONF_PROGRAMS,
    DOMAIN,
    GRACE_PERIOD,
    STATUS_DISABLED,
    STATUS_NO_PROGRAM,
    STATUS_OVERRIDE,
    STATUS_SCHEDULED,
    STORAGE_VERSION,
    TEMPERATURE_TOLERANCE,
)
from .planning import Program, current_occurrence, next_occurrence

_LOGGER = logging.getLogger(__name__)

_NOT_READY = (STATE_UNAVAILABLE, STATE_UNKNOWN)

# (réglage du profil, attribut d'état, attribut listant les valeurs, service)
_MODE_SETTINGS = (
    (ATTR_FAN_MODE, "fan_mode", "fan_modes", "set_fan_mode"),
    (ATTR_SWING_MODE, "swing_mode", "swing_modes", "set_swing_mode"),
    (
        ATTR_SWING_HORIZONTAL_MODE,
        "swing_horizontal_mode",
        "swing_horizontal_modes",
        "set_swing_horizontal_mode",
    ),
)


@dataclass
class GroupState:
    """État d'exécution d'un groupe (en partie persisté)."""

    planning_id: str
    enabled: bool = True
    active_profile_id: str | None = None
    override: bool = False
    last_slot_key: str | None = None
    applied_at: datetime | None = None
    scheduled_profile_id: str | None = None
    next_change: datetime | None = None
    next_profile_id: str | None = None
    has_program: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "planning_id": self.planning_id,
            "enabled": self.enabled,
            "active_profile_id": self.active_profile_id,
            "override": self.override,
            "last_slot_key": self.last_slot_key,
        }


class SplitScheduler:
    """Pilote les groupes de splits d'une entrée de configuration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        options = entry.options
        self.groups: dict[str, dict] = dict(options.get(CONF_GROUPS, {}))
        self.profiles: dict[str, dict] = dict(options.get(CONF_PROFILES, {}))
        self.plannings: dict[str, dict] = dict(options.get(CONF_PLANNINGS, {}))
        self.states: dict[str, GroupState] = {}
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self._timers: dict[str, CALLBACK_TYPE] = {}
        self._pending: dict[str, tuple[str, str]] = {}  # entity_id -> (groupe, profil)
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[CALLBACK_TYPE] = []

    # ------------------------------------------------------------------ cycle de vie

    async def async_load(self) -> None:
        """Restaure l'état d'exécution sauvegardé."""
        stored = (await self._store.async_load() or {}).get("groups", {})
        default_planning = next(iter(self.plannings), "")
        for gid in self.groups:
            data = stored.get(gid, {})
            planning_id = data.get("planning_id")
            if planning_id not in self.plannings:
                planning_id = default_planning
            active = data.get("active_profile_id")
            self.states[gid] = GroupState(
                planning_id=planning_id,
                enabled=data.get("enabled", True),
                active_profile_id=active if active in self.profiles else None,
                override=data.get("override", False),
                last_slot_key=data.get("last_slot_key"),
            )

    @callback
    def async_start(self) -> None:
        """Démarre la programmation une fois Home Assistant entièrement lancé."""
        self._unsubs.append(async_at_started(self.hass, self._async_on_started))

    async def _async_on_started(self, _hass: HomeAssistant) -> None:
        climates = sorted({eid for g in self.groups.values() for eid in g[CONF_CLIMATES]})
        if climates:
            self._unsubs.append(
                async_track_state_change_event(self.hass, climates, self._on_climate_change)
            )
        for gid in self.groups:
            await self.async_refresh_group(gid)

    async def async_stop(self) -> None:
        """Arrête minuteries et écouteurs, sauvegarde l'état."""
        for unsub in (*self._unsubs, *self._timers.values()):
            unsub()
        self._unsubs.clear()
        self._timers.clear()
        await self._store.async_save(self._data_to_save())

    # ------------------------------------------------------------------ notifications

    @callback
    def async_add_listener(self, update: Callable[[], None]) -> CALLBACK_TYPE:
        """Abonne une entité aux changements d'état."""
        self._listeners.append(update)

        @callback
        def remove() -> None:
            self._listeners.remove(update)

        return remove

    @callback
    def _changed(self) -> None:
        self._store.async_delay_save(self._data_to_save, 1)
        for update in list(self._listeners):
            update()

    def _data_to_save(self) -> dict[str, Any]:
        return {"groups": {gid: st.as_dict() for gid, st in self.states.items()}}

    # ------------------------------------------------------------------ consultation

    def program(self, gid: str, planning_id: str) -> Program:
        return self.plannings.get(planning_id, {}).get(CONF_PROGRAMS, {}).get(gid, {})

    def profile_name(self, profile_id: str | None) -> str | None:
        if profile_id is None:
            return None
        return self.profiles.get(profile_id, {}).get("name")

    def status(self, gid: str) -> str:
        state = self.states[gid]
        if not state.enabled:
            return STATUS_DISABLED
        if state.override:
            return STATUS_OVERRIDE
        if not state.has_program:
            return STATUS_NO_PROGRAM
        return STATUS_SCHEDULED

    # ------------------------------------------------------------------ actions

    async def async_refresh_group(
        self, gid: str, *, force: bool = False, now: datetime | None = None
    ) -> None:
        """Applique le créneau en cours si besoin et programme le suivant.

        Sans ``force``, le profil du créneau en cours n'est appliqué que s'il
        ne l'a pas déjà été : un redémarrage de Home Assistant ou un rechargement
        ne défait donc pas une dérogation manuelle, mais un changement manqué
        pendant un arrêt est rattrapé.
        """
        now = dt_util.as_local(now or dt_util.now())
        if (unsub := self._timers.pop(gid, None)) is not None:
            unsub()
        state = self.states[gid]
        program = self.program(gid, state.planning_id)
        state.has_program = any(program.values())
        current = current_occurrence(program, now)
        upcoming = next_occurrence(program, now)
        state.scheduled_profile_id = current.profile_id if current else None
        state.next_change = state.next_profile_id = None

        if state.enabled:
            if current is not None:
                key = f"{state.planning_id}|{current.start.isoformat()}"
                if force or key != state.last_slot_key:
                    state.last_slot_key = key
                    await self._async_apply(gid, current.profile_id, manual=False)
            elif force:
                state.override = False
            if upcoming is not None:
                state.next_change = upcoming.start
                state.next_profile_id = upcoming.profile_id
                self._timers[gid] = async_track_point_in_time(
                    self.hass, self._make_timer_action(gid, upcoming.start), upcoming.start
                )
        self._changed()

    def _make_timer_action(self, gid: str, target: datetime) -> Callable[[datetime], Any]:
        async def _action(fired: datetime) -> None:
            self._timers.pop(gid, None)
            # Le minuteur peut se déclencher quelques millisecondes en avance.
            await self.async_refresh_group(gid, now=max(dt_util.now(), target))

        return _action

    async def async_select_profile(self, gid: str, profile_id: str) -> None:
        """Choix manuel d'un profil : il vaut jusqu'au prochain créneau."""
        await self._async_apply(gid, profile_id, manual=True)
        self._changed()

    async def async_select_planning(self, gid: str, planning_id: str) -> None:
        """Change le planning d'un groupe et applique aussitôt son créneau en cours."""
        self.states[gid].planning_id = planning_id
        self.states[gid].last_slot_key = None
        await self.async_refresh_group(gid, force=True)

    async def async_select_planning_all(self, planning_id: str) -> None:
        for gid in self.groups:
            await self.async_select_planning(gid, planning_id)

    async def async_set_enabled(self, gid: str, enabled: bool) -> None:
        state = self.states[gid]
        state.enabled = enabled
        if enabled:
            state.override = False
        await self.async_refresh_group(gid, force=enabled)

    async def async_resume(self, gid: str) -> None:
        """Annule une dérogation : réapplique le profil programmé maintenant."""
        self.states[gid].enabled = True
        self.states[gid].override = False
        await self.async_refresh_group(gid, force=True)

    # ------------------------------------------------------------------ application aux splits

    async def _async_apply(self, gid: str, profile_id: str, *, manual: bool) -> None:
        profile = self.profiles.get(profile_id)
        if profile is None:
            _LOGGER.warning("Profil %s introuvable pour le groupe %s", profile_id, gid)
            return
        state = self.states[gid]
        state.active_profile_id = profile_id
        state.override = manual
        state.applied_at = dt_util.utcnow()
        _LOGGER.info(
            "Groupe « %s » : profil « %s »%s",
            self.groups[gid]["name"],
            profile["name"],
            " (choix manuel)" if manual else "",
        )
        for entity_id in self.groups[gid][CONF_CLIMATES]:
            await self._async_apply_entity(gid, profile_id, entity_id)

    async def _async_apply_entity(self, gid: str, profile_id: str, entity_id: str) -> None:
        current = self.hass.states.get(entity_id)
        if current is None or current.state in _NOT_READY:
            # Split injoignable : le profil sera envoyé dès son retour.
            _LOGGER.info("%s indisponible, profil mis en attente", entity_id)
            self._pending[entity_id] = (gid, profile_id)
            return
        self._pending.pop(entity_id, None)
        try:
            await self._async_send(entity_id, current, self.profiles[profile_id])
        except (HomeAssistantError, ValueError) as err:
            _LOGGER.warning("Échec de l'envoi du profil à %s : %s", entity_id, err)

    async def _async_send(self, entity_id: str, current: State, profile: dict) -> None:
        attrs = current.attributes

        async def call(service: str, **data: Any) -> None:
            await self.hass.services.async_call(
                "climate", service, {ATTR_ENTITY_ID: entity_id, **data}, blocking=True
            )

        hvac_mode = profile.get(ATTR_HVAC_MODE)
        if hvac_mode is not None and hvac_mode != current.state:
            if hvac_mode not in attrs.get("hvac_modes", []):
                _LOGGER.warning("%s ne gère pas le mode %s", entity_id, hvac_mode)
                hvac_mode = None
            else:
                await call("set_hvac_mode", hvac_mode=hvac_mode)
        mode = hvac_mode or current.state
        if mode == "off":
            return

        temperature = profile.get(ATTR_TEMPERATURE)
        features = attrs.get("supported_features", 0)
        if (
            temperature is not None
            and mode != "fan_only"
            and features & ClimateEntityFeature.TARGET_TEMPERATURE
        ):
            wanted = temperature
            temperature = target_temperature(attrs, temperature)
            if temperature != wanted:
                _LOGGER.info(
                    "%s : consigne %s °C ramenée à %s °C (limites et pas du split)",
                    entity_id,
                    wanted,
                    temperature,
                )
            if attrs.get("temperature") != temperature:
                await call("set_temperature", temperature=temperature)

        for setting, attr, choices, service in _MODE_SETTINGS:
            value = profile.get(setting)
            if value is None or attrs.get(attr) == value:
                continue
            if value not in attrs.get(choices, []):
                _LOGGER.warning("%s : valeur « %s » non gérée pour %s", entity_id, value, attr)
                continue
            await call(service, **{attr: value})

    # ------------------------------------------------------------------ suivi des splits

    @callback
    def _on_climate_change(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        new = event.data["new_state"]
        old = event.data["old_state"]
        if new is None or new.state in _NOT_READY:
            return

        if (pending := self._pending.pop(entity_id, None)) is not None:
            gid, profile_id = pending
            if gid in self.states and self.states[gid].active_profile_id == profile_id:
                self.hass.async_create_task(
                    self._async_apply_entity(gid, profile_id, entity_id)
                )
            return

        if old is None or old.state in _NOT_READY:
            return
        now = dt_util.utcnow()
        for gid, group in self.groups.items():
            state = self.states[gid]
            if (
                entity_id not in group[CONF_CLIMATES]
                or not state.enabled
                or state.override
                or state.active_profile_id is None
                or (state.applied_at is not None and now - state.applied_at < GRACE_PERIOD)
            ):
                continue
            profile = self.profiles.get(state.active_profile_id, {})
            if _deviates(new, profile):
                _LOGGER.info(
                    "Groupe « %s » : réglage manuel détecté sur %s, conservé "
                    "jusqu'au prochain créneau",
                    group["name"],
                    entity_id,
                )
                state.override = True
                self._changed()


def _deviates(state: State, profile: dict) -> bool:
    """Le split s'écarte-t-il des réglages imposés par le profil ?"""
    attrs = state.attributes
    hvac_mode = profile.get(ATTR_HVAC_MODE)
    if hvac_mode is not None and state.state != hvac_mode:
        return True
    if state.state == "off":
        return False
    temperature = profile.get(ATTR_TEMPERATURE)
    current = attrs.get("temperature")
    if (
        temperature is not None
        and current is not None
        and state.state != "fan_only"
        and abs(float(current) - target_temperature(attrs, temperature)) > TEMPERATURE_TOLERANCE
    ):
        return True
    for setting, attr, choices, _ in _MODE_SETTINGS:
        value = profile.get(setting)
        if value is not None and value in attrs.get(choices, []) and attrs.get(attr) != value:
            return True
    return False


def target_temperature(attrs: Mapping[str, Any], wanted: float) -> float:
    """Consigne réellement acceptée par le split : arrondie à son pas, bornée.

    Ex. Faikout en S21 : pas de 0,5 °C, 16 à 32 °C ; un hors-gel à 10 °C
    devient 16 °C.
    """
    step = attrs.get("target_temp_step")
    if step:
        wanted = round(round(wanted / float(step)) * float(step), 2)
    low, high = attrs.get("min_temp"), attrs.get("max_temp")
    if low is not None:
        wanted = max(wanted, float(low))
    if high is not None:
        wanted = min(wanted, float(high))
    return wanted
