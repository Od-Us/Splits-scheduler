"""Moteur de programmation : minuteries, application des profils, dérogations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
    async_track_time_interval,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_FAN_MODE,
    ATTR_QUIET,
    ATTR_HVAC_MODE,
    ATTR_SWING_HORIZONTAL_MODE,
    ATTR_SWING_MODE,
    ATTR_TEMPERATURE,
    CONF_CLIMATES,
    CONF_COMPRESSOR_MAX,
    CONF_COMPRESSORS,
    CONF_ENERGY,
    CONF_HEAT_PUMPS,
    CONF_MODEL,
    CONF_POWER,
    CONF_PRIORITY,
    CONF_ALWAYS_QUIET,
    CONF_OUTDOOR,
    CONF_SEND_NORMAL,
    CONF_SETTINGS,
    ATTR_OUTDOOR_DELTA,
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
    ordered,
)
from .compressor import Average, StartLog
from .outdoor import (
    MIN_INTERVAL,
    QUIET_BEFORE_CHANGE,
    THRESHOLD,
    OutdoorAverage,
    adapt_target,
    round_half,
)
from .compressor import robust_maximum
from .features import compressor_sensor, quiet_switch
from .heatpump import EnergyToday, find_conflicts, mode_side, shared_value
from .planning import Program, current_occurrence, next_occurrence

_LOGGER = logging.getLogger(__name__)

_NOT_READY = (STATE_UNAVAILABLE, STATE_UNKNOWN)
# Réglages qui ne valent pas dérogation (ni depuis la carte, ni à la télécommande)
_NOT_AN_OVERRIDE = (ATTR_FAN_MODE, ATTR_SWING_MODE, ATTR_SWING_HORIZONTAL_MODE)

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
class SplitOverride:
    """Dérogation d'un seul split (télécommande, fenêtre du thermostat)."""

    since: datetime
    until: datetime | None = None  # None : jusqu'au prochain créneau du groupe

    def as_dict(self) -> dict[str, Any]:
        return {
            "since": self.since.isoformat(),
            "until": self.until.isoformat() if self.until else None,
        }


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
    profile_changed_at: datetime | None = None
    compressor: StartLog | None = None
    # Consigne réellement demandée (adaptée à l'extérieur) et date du dernier envoi
    effective_target: float | None = None
    target_changed_at: datetime | None = None
    # Réglage fait à la main (carte, télécommande) : plus d'adaptation jusqu'au créneau suivant
    hand_set: bool = False
    # Dérogation : début, et heure de reprise choisie (None : prochain créneau)
    override_since: datetime | None = None
    override_until: datetime | None = None
    # Splits en dérogation individuelle (les autres suivent le programme)
    split_overrides: dict[str, SplitOverride] = field(default_factory=dict)
    # Réglages faits depuis la carte pendant une dérogation du groupe (consigne, mode)
    manual_settings: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "planning_id": self.planning_id,
            "enabled": self.enabled,
            "active_profile_id": self.active_profile_id,
            "override": self.override,
            "last_slot_key": self.last_slot_key,
            "profile_changed_at": (
                self.profile_changed_at.isoformat() if self.profile_changed_at else None
            ),
            "compressor": self.compressor.as_dict() if self.compressor else None,
            "effective_target": self.effective_target,
            "target_changed_at": (
                self.target_changed_at.isoformat() if self.target_changed_at else None
            ),
            "hand_set": self.hand_set,
            "override_since": self.override_since.isoformat() if self.override_since else None,
            "override_until": self.override_until.isoformat() if self.override_until else None,
            "split_overrides": {eid: o.as_dict() for eid, o in self.split_overrides.items()},
            "manual_settings": self.manual_settings,
        }


class SplitScheduler:
    """Pilote les groupes de splits d'une entrée de configuration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        options = entry.options
        self.groups: dict[str, dict] = ordered(options.get(CONF_GROUPS, {}))
        self.profiles: dict[str, dict] = ordered(options.get(CONF_PROFILES, {}))
        self.plannings: dict[str, dict] = ordered(options.get(CONF_PLANNINGS, {}))
        self.states: dict[str, GroupState] = {}
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self._timers: dict[str, CALLBACK_TYPE] = {}
        self._pending: dict[str, tuple[str, str]] = {}  # entity_id -> (groupe, profil)
        self._listeners: list[Callable[[], None]] = []
        self.outdoor_entity: str | None = options.get(CONF_SETTINGS, {}).get(CONF_OUTDOOR)
        # Multi-split : envoyés avec chaque commande (réglages généraux)
        self.send_normal: bool = bool(options.get(CONF_SETTINGS, {}).get(CONF_SEND_NORMAL))
        self.always_quiet: bool = bool(options.get(CONF_SETTINGS, {}).get(CONF_ALWAYS_QUIET))
        # Interrupteur « unité extérieure silencieuse » de chaque split (Faikout)
        self.quiet_switches: dict[str, str] = {}
        # Pompes à chaleur : capteurs du compresseur, pompe de chaque split, pompe principale
        # de chaque groupe (celle de la majorité de ses splits)
        self.heat_pumps: dict[str, dict] = ordered(options.get(CONF_HEAT_PUMPS, {}))
        self.pump_sources: dict[str, list[str]] = {}
        self.pump_of: dict[str, str] = {
            eid: hpid for hpid, hp in self.heat_pumps.items() for eid in hp.get(CONF_CLIMATES, [])
        }
        self.group_pumps: dict[str, list[str]] = {}
        self.energy: dict[str, EnergyToday] = {}
        # Fréquence maximale du compresseur par pompe : {valeur, source, unite}
        self.compressor_max: dict[str, dict[str, Any]] = {}
        self.outdoor = OutdoorAverage()
        self._unsubs: list[CALLBACK_TYPE] = []

    # ------------------------------------------------------------------ cycle de vie

    async def async_load(self) -> None:
        """Restaure l'état d'exécution sauvegardé."""
        saved = await self._store.async_load() or {}
        stored = saved.get("groups", {})
        for hpid, pump in self.heat_pumps.items():
            self.pump_sources[hpid] = list(pump.get(CONF_COMPRESSORS) or []) or [
                sensor for eid in pump.get(CONF_CLIMATES, []) if (sensor := compressor_sensor(self.hass, eid))
            ]
            self.energy[hpid] = EnergyToday.from_dict(saved.get("heat_pumps", {}).get(hpid))
        for gid, group in self.groups.items():
            counts: dict[str, int] = {}
            for eid in group[CONF_CLIMATES]:
                if (hpid := self.pump_of.get(eid)) is not None:
                    counts[hpid] = counts.get(hpid, 0) + 1
            # pompe principale en premier (la plus représentée), puis les autres
            self.group_pumps[gid] = sorted(counts, key=lambda h: -counts[h])
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
                profile_changed_at=_parse(data.get("profile_changed_at")),
                effective_target=data.get("effective_target"),
                target_changed_at=_parse(data.get("target_changed_at")),
                hand_set=data.get("hand_set", False),
                override_since=_parse(data.get("override_since")),
                override_until=_parse(data.get("override_until")),
                manual_settings=data.get("manual_settings") or {},
                split_overrides={
                    eid: SplitOverride(since=since, until=_parse(o.get("until")))
                    for eid, o in (data.get("split_overrides") or {}).items()
                    if eid in self.groups[gid][CONF_CLIMATES]
                    and (since := _parse(o.get("since"))) is not None
                },
            )
            if self.main_pump(gid):
                stored_log = data.get("compressor")
                self.states[gid].compressor = (
                    StartLog.from_dict(stored_log, _parse) if stored_log else None
                ) or StartLog(since=dt_util.utcnow())

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
        self.quiet_switches = {
            eid: switch for eid in climates if (switch := quiet_switch(self.hass, eid))
        }
        compressors = sorted({eid for sources in self.pump_sources.values() for eid in sources})
        if compressors:
            for gid in self.groups:
                if (hpid := self.main_pump(gid)) is None:
                    continue
                await self._async_backfill_compressor(gid)
                log = self.states[gid].compressor
                value = self.pump_frequency(hpid)
                if log is not None and log.running is None and value is not None:
                    log.feed(dt_util.utcnow(), str(value))  # état de départ
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, list(compressors), self._on_compressor_change
                )
            )
            await self._async_update_compressor_max()
            self._unsubs.append(
                async_track_time_interval(
                    self.hass, self._async_update_compressor_max, timedelta(hours=6)
                )
            )
        if self.outdoor_entity is None:
            self.outdoor_entity = detect_outdoor_sensor(
                self.hass, [eid for g in self.groups.values() for eid in g[CONF_CLIMATES]]
            )
        if self.outdoor_entity:
            await self._async_backfill_outdoor()
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, [self.outdoor_entity], self._on_outdoor_change
                )
            )
        meters = {
            eid: hpid
            for hpid, pump in self.heat_pumps.items()
            for eid in (pump.get(CONF_ENERGY), pump.get(CONF_POWER))
            if eid
        }
        if meters:
            for hpid in self.heat_pumps:
                self._feed_energy(hpid)
            self._unsubs.append(
                async_track_state_change_event(self.hass, list(meters), self._on_meter_change)
            )
        if compressors or self.outdoor_entity or meters:
            # Moyennes et adaptation à l'extérieur : réexamen chaque minute.
            self._unsubs.append(
                async_track_time_interval(self.hass, self._async_tick, timedelta(minutes=1))
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
        now = dt_util.utcnow()
        for state in self.states.values():
            if state.compressor is not None:
                keep = now - timedelta(hours=24)
                if state.profile_changed_at is not None:
                    keep = min(keep, state.profile_changed_at)
                state.compressor.prune(keep, now)
        return {
            "groups": {gid: st.as_dict() for gid, st in self.states.items()},
            "heat_pumps": {hpid: energy.as_dict() for hpid, energy in self.energy.items()},
        }

    @callback
    def _notify(self) -> None:
        for update in list(self._listeners):
            update()

    async def _async_tick(self, _now: datetime) -> None:
        for gid in self.groups:
            await self._async_adapt(gid)
        for hpid, pump in self.heat_pumps.items():
            if pump.get(CONF_POWER) and not pump.get(CONF_ENERGY):
                self._feed_energy(hpid)  # intégration de la puissance, minute par minute
        self._notify()

    # ------------------------------------------------------------------ température extérieure

    @callback
    def _on_outdoor_change(self, event: Event[EventStateChangedData]) -> None:
        new = event.data["new_state"]
        if new is not None:
            self.outdoor.add(new.last_updated, new.state)
            self.outdoor.prune(dt_util.utcnow())

    async def _async_backfill_outdoor(self) -> None:
        """Dernière heure de température extérieure, depuis l'historique si possible."""
        assert self.outdoor_entity is not None
        now = dt_util.utcnow()
        if "recorder" in self.hass.config.components:
            from homeassistant.components.recorder import history
            from homeassistant.helpers.recorder import get_instance

            try:
                changes = await get_instance(self.hass).async_add_executor_job(
                    history.state_changes_during_period,
                    self.hass,
                    now - self.outdoor.window,
                    now,
                    self.outdoor_entity,
                    True,
                )
            except Exception as err:  # noqa: BLE001 - l'historique est un plus
                _LOGGER.debug("Historique extérieur indisponible : %s", err)
                changes = {}
            for past in changes.get(self.outdoor_entity, []):
                self.outdoor.add(past.last_updated, past.state)
        if not self.outdoor.samples and (current := self.hass.states.get(self.outdoor_entity)):
            self.outdoor.add(current.last_updated, current.state)

    def outdoor_mean(self) -> float | None:
        return self.outdoor.mean(dt_util.utcnow()) if self.outdoor_entity else None

    def _group_mode(self, gid: str, profile: dict) -> str | None:
        if (mode := profile.get(ATTR_HVAC_MODE)) is not None:
            return mode
        first = self.hass.states.get(self.groups[gid][CONF_CLIMATES][0])
        return first.state if first is not None else None

    def _target_for(self, gid: str, profile: dict) -> float | None:
        """Consigne du profil, adaptée à l'extérieur si le profil le prévoit."""
        target = profile.get(ATTR_TEMPERATURE)
        adapted = adapt_target(
            target, self._group_mode(gid, profile), profile.get(ATTR_OUTDOOR_DELTA), self.outdoor_mean()
        )
        return round_half(adapted) if adapted is not None else None

    def _settings_for(self, gid: str, profile_id: str) -> dict:
        """Réglages à envoyer aux splits : ceux du profil, consigne éventuellement adaptée."""
        settings = dict(self.profiles.get(profile_id, {}))
        state = self.states[gid]
        if settings.get(ATTR_TEMPERATURE) is not None and state.effective_target is not None:
            settings[ATTR_TEMPERATURE] = state.effective_target
        return settings

    def group_target(self, gid: str) -> float | None:
        """Consigne du groupe : celle que la programmation impose (profil, adaptation à
        l'extérieur ou réglage depuis la carte), telle qu'un split l'accepte.

        None quand la programmation est coupée, sans profil, ou en mode arrêt.
        """
        state = self.states[gid]
        if not state.enabled or state.active_profile_id is None:
            return None
        settings = {**self._settings_for(gid, state.active_profile_id), **state.manual_settings}
        if settings.get(ATTR_HVAC_MODE) == "off" or settings.get(ATTR_TEMPERATURE) is None:
            return None
        wanted = float(settings[ATTR_TEMPERATURE])
        for entity_id in self.groups[gid][CONF_CLIMATES]:
            split = self.hass.states.get(entity_id)
            if split is not None and split.state not in _NOT_READY:
                return target_temperature(split.attributes, wanted)  # limites et pas du split
        return wanted

    def adaptation(self, gid: str) -> dict[str, Any]:
        """Informations d'adaptation pour l'affichage."""
        state = self.states[gid]
        profile = self.profiles.get(state.active_profile_id or "", {})
        target, delta = profile.get(ATTR_TEMPERATURE), profile.get(ATTR_OUTDOOR_DELTA)
        effective = state.effective_target
        return {
            "consigne_profil": target,
            "consigne_appliquee": effective if effective is not None else target,
            "ecart_max_exterieur": delta,
            "temperature_exterieure": self.outdoor_mean(),
            "adaptation_exterieure": bool(
                delta is not None and target is not None and effective is not None
                and abs(effective - round_half(target)) >= THRESHOLD and not state.hand_set
            ),
        }

    async def _async_adapt(self, gid: str) -> None:
        """Réadapte la consigne si l'extérieur a assez changé (règles de réactivité)."""
        state = self.states[gid]
        profile = self.profiles.get(state.active_profile_id or "")
        if (
            profile is None
            or profile.get(ATTR_OUTDOOR_DELTA) is None
            or profile.get(ATTR_TEMPERATURE) is None
            or not state.enabled
            or state.hand_set
        ):
            return
        now = dt_util.utcnow()
        wanted = self._target_for(gid, profile)
        current = state.effective_target
        if current is None:  # profil appliqué par une version antérieure
            current = round_half(profile[ATTR_TEMPERATURE])
        if wanted is None or abs(wanted - current) < THRESHOLD:
            return
        if state.target_changed_at is not None and now - state.target_changed_at < MIN_INTERVAL:
            return
        if state.next_change is not None and state.next_change - now < QUIET_BEFORE_CHANGE:
            return
        _LOGGER.info(
            "Groupe « %s » : consigne %s °C -> %s °C (extérieur %s °C, écart max %s °C)",
            self.groups[gid]["name"],
            current,
            wanted,
            self.outdoor_mean(),
            profile[ATTR_OUTDOOR_DELTA],
        )
        state.effective_target = wanted
        state.target_changed_at = now
        state.applied_at = now  # nos propres commandes : pas de fausse dérogation
        for entity_id in self.groups[gid][CONF_CLIMATES]:
            split = self.hass.states.get(entity_id)
            if split is None or split.state in _NOT_READY or entity_id in state.split_overrides:
                continue
            try:
                await self._async_send(entity_id, split, {ATTR_TEMPERATURE: wanted})
            except (HomeAssistantError, ValueError) as err:
                _LOGGER.warning("Échec de l'adaptation de %s : %s", entity_id, err)
        self._changed()

    # ------------------------------------------------------------------ compresseur

    # ------------------------------------------------------------------ pompes à chaleur

    def main_pump(self, gid: str) -> str | None:
        """Pompe à chaleur de la majorité des splits du groupe, si son compresseur est suivi."""
        pumps = self.group_pumps.get(gid) or []
        return pumps[0] if pumps and self.pump_sources.get(pumps[0]) else None

    def pump_frequency(self, hpid: str) -> float | None:
        """Fréquence du compresseur : médiane des capteurs des splits de la pompe."""
        values = []
        for eid in self.pump_sources.get(hpid, []):
            state = self.hass.states.get(eid)
            try:
                values.append(float(state.state))  # type: ignore[union-attr]
            except (AttributeError, TypeError, ValueError):
                continue
        return shared_value(values)

    def pump_unit(self, hpid: str) -> str | None:
        for eid in self.pump_sources.get(hpid, []):
            if (state := self.hass.states.get(eid)) and (
                unit := state.attributes.get("unit_of_measurement")
            ):
                return unit
        return self.compressor_max.get(hpid, {}).get("unite")

    def pump_modes(self, hpid: str) -> dict[str, str | None]:
        """Mode actuel (état du thermostat) de chaque split de la pompe."""
        modes: dict[str, str | None] = {}
        for eid in self.heat_pumps[hpid].get(CONF_CLIMATES, []):
            state = self.hass.states.get(eid)
            modes[eid] = state.state if state and state.state not in _NOT_READY else None
        return modes

    def pump_conflicts(self, hpid: str) -> dict[str, str | None]:
        """Splits en mode opposé au split prioritaire (ou entre eux sans prioritaire)."""
        return find_conflicts(self.pump_modes(hpid), self.heat_pumps[hpid].get(CONF_PRIORITY))

    def group_conflicts(self, gid: str) -> list[dict[str, Any]]:
        """Splits du groupe en conflit de mode avec leur pompe à chaleur."""
        result = []
        for hpid in self.group_pumps.get(gid, []):
            for eid, priority in self.pump_conflicts(hpid).items():
                if eid in self.groups[gid][CONF_CLIMATES]:
                    result.append({"entity_id": eid, "pompe": self.heat_pumps[hpid]["name"], "prioritaire": priority})
        return result

    def pump_mode(self, hpid: str) -> str:
        """Côté de fonctionnement de la pompe : heat, cool, conflict ou idle."""
        if self.pump_conflicts(hpid):
            return "conflict"
        sides = {mode_side(mode) for mode in self.pump_modes(hpid).values()} - {None}
        return next(iter(sides)) if sides else "idle"

    def pump_load(self, hpid: str | None) -> tuple[float | None, dict[str, Any]]:
        """Charge du compresseur en % de sa fréquence maximale (bornée à 100)."""
        info = self.compressor_max.get(hpid, {}) if hpid else {}
        value = self.pump_frequency(hpid) if hpid else None
        attrs = {
            "frequence": value,
            "frequence_max": info.get("valeur"),
            "source_max": info.get("source"),
            "unite": self.pump_unit(hpid) if hpid else None,
            "capteurs": self.pump_sources.get(hpid, []) if hpid else [],
        }
        maximum = info.get("valeur")
        if value is None or not maximum:
            return None, attrs
        return round(min(100.0, max(0.0, value / maximum * 100))), attrs

    def compressor_load(self, gid: str) -> tuple[float | None, dict[str, Any]]:
        """Charge du compresseur de la pompe principale du groupe."""
        return self.pump_load(self.main_pump(gid))

    def energy_today(self, hpid: str) -> float | None:
        pump = self.heat_pumps[hpid]
        if not pump.get(CONF_ENERGY) and not pump.get(CONF_POWER):
            return None
        energy = self.energy[hpid]
        if energy.day != dt_util.now().date().isoformat():
            return 0.0
        return round(energy.kwh, 2)

    def _number(self, entity_id: str | None) -> float | None:
        state = self.hass.states.get(entity_id) if entity_id else None
        try:
            return float(state.state)  # type: ignore[union-attr]
        except (AttributeError, TypeError, ValueError):
            return None

    def _feed_energy(self, hpid: str) -> None:
        """Consommation du jour : compteur cumulé (kWh), sinon intégration de la puissance (W)."""
        pump, now = self.heat_pumps[hpid], dt_util.now()
        energy = self.energy[hpid]
        if pump.get(CONF_ENERGY):
            total = self._number(pump[CONF_ENERGY])
            if total is not None:
                state = self.hass.states.get(pump[CONF_ENERGY])
                if state and state.attributes.get("unit_of_measurement") == "Wh":
                    total /= 1000
                energy.from_counter(now, total)
        elif pump.get(CONF_POWER):
            watts = self._number(pump[CONF_POWER])
            state = self.hass.states.get(pump[CONF_POWER])
            if watts is not None and state and state.attributes.get("unit_of_measurement") == "kW":
                watts *= 1000
            energy.from_power(now, watts)

    @callback
    def _on_meter_change(self, event: Event[EventStateChangedData]) -> None:
        for hpid, pump in self.heat_pumps.items():
            if event.data["entity_id"] in (pump.get(CONF_ENERGY), pump.get(CONF_POWER)):
                self._feed_energy(hpid)
        self._store.async_delay_save(self._data_to_save, 60)
        self._notify()

    def pump_info(self, hpid: str) -> dict[str, Any]:
        """Tout ce que la carte affiche pour une pompe à chaleur."""
        pump = self.heat_pumps[hpid]
        load, attrs = self.pump_load(hpid)
        outdoor = detect_outdoor_sensor(self.hass, pump.get(CONF_CLIMATES, []))
        return {
            "id": hpid,
            "name": pump["name"],
            "model": pump.get(CONF_MODEL),
            "climates": pump.get(CONF_CLIMATES, []),
            "priority": pump.get(CONF_PRIORITY),
            "sources": self.pump_sources.get(hpid, []),
            "frequency": attrs["frequence"],
            "unit": attrs["unite"],
            "max": attrs["frequence_max"],
            "max_source": attrs["source_max"],
            "load": load,
            "power_sensor": pump.get(CONF_POWER),
            "power": self._number(pump.get(CONF_POWER)),
            "energy_sensor": pump.get(CONF_ENERGY),
            "energy_today": self.energy_today(hpid),
            "outdoor_sensor": outdoor,
            "outdoor": self._number(outdoor),
            "modes": self.pump_modes(hpid),
            "mode": self.pump_mode(hpid),
            "conflicts": self.pump_conflicts(hpid),
        }

    # ------------------------------------------------------------------ compresseur

    @callback
    def _on_compressor_change(self, event: Event[EventStateChangedData]) -> None:
        new = event.data["new_state"]
        if new is None:
            return
        for gid, group in self.groups.items():
            hpid = self.main_pump(gid)
            log = self.states[gid].compressor
            if hpid is None or log is None or event.data["entity_id"] not in self.pump_sources[hpid]:
                continue
            value = self.pump_frequency(hpid)
            if value is not None and log.feed(new.last_changed, str(value)):
                _LOGGER.debug("Groupe « %s » : démarrage du compresseur", group["name"])
                self._changed()
        self._notify()  # charge du compresseur (%) à jour

    async def _async_update_compressor_max(self, _now: datetime | None = None) -> None:
        """Fréquence maximale de chaque compresseur : saisie, sinon observée sur 30 jours."""
        for hpid, pump in self.heat_pumps.items():
            sources = self.pump_sources.get(hpid)
            if not sources:
                continue
            unit = self.pump_unit(hpid)
            if pump.get(CONF_COMPRESSOR_MAX):
                self.compressor_max[hpid] = {
                    "valeur": float(pump[CONF_COMPRESSOR_MAX]), "source": "saisie", "unite": unit,
                }
                continue
            found = [
                value
                for eid in sources
                if (value := robust_maximum(await self._async_hourly_maxima(eid), unit)) is not None
            ]
            value = shared_value(found)
            self.compressor_max[hpid] = {
                "valeur": value, "source": "observee_30j" if value is not None else None, "unite": unit,
            }
        self._notify()

    async def _async_hourly_maxima(self, entity_id: str) -> list[float]:
        """Maxima horaires des 30 derniers jours : statistiques de l'enregistreur, sinon
        historique détaillé (10 jours par défaut) regroupé par heure."""
        if "recorder" not in self.hass.config.components:
            return []
        from homeassistant.components.recorder import history, statistics
        from homeassistant.helpers.recorder import get_instance

        now = dt_util.utcnow()
        start = now - timedelta(days=30)
        try:
            stats = await get_instance(self.hass).async_add_executor_job(
                statistics.statistics_during_period,
                self.hass, start, now, {entity_id}, "hour", None, {"max"},
            )
            maxima = [row["max"] for row in stats.get(entity_id, []) if row.get("max") is not None]
            if maxima:
                return [float(v) for v in maxima]
            changes = await get_instance(self.hass).async_add_executor_job(
                history.state_changes_during_period, self.hass, start, now, entity_id, True
            )
        except Exception as err:  # noqa: BLE001 - l'historique est un plus, pas un besoin
            _LOGGER.debug("Historique du compresseur indisponible : %s", err)
            return []
        hours: dict[datetime, float] = {}
        for past in changes.get(entity_id, []):
            try:
                value = float(past.state)
            except ValueError:
                continue
            hour = past.last_changed.replace(minute=0, second=0, microsecond=0)
            hours[hour] = max(hours.get(hour, 0.0), value)
        return list(hours.values())

    async def _async_backfill_compressor(self, gid: str) -> None:
        """Reconstitue les démarrages depuis l'historique (si l'enregistreur est actif)."""
        state = self.states[gid]
        hpid = self.main_pump(gid)
        if hpid is None:
            return
        entity_id = self.pump_sources[hpid][0]
        if "recorder" not in self.hass.config.components or state.compressor is None:
            return
        from homeassistant.components.recorder import history
        from homeassistant.helpers.recorder import get_instance

        now = dt_util.utcnow()
        start = now - timedelta(hours=24)
        if state.profile_changed_at is not None:
            start = min(start, state.profile_changed_at)
        start = max(start, now - timedelta(days=7))
        try:
            changes = await get_instance(self.hass).async_add_executor_job(
                history.state_changes_during_period, self.hass, start, now, entity_id, True
            )
        except Exception as err:  # noqa: BLE001 - l'historique est un plus, pas un besoin
            _LOGGER.debug("Historique du compresseur indisponible : %s", err)
            return
        states = changes.get(entity_id, [])
        if not states:
            return
        log = StartLog(since=max(start, states[0].last_changed))
        for past in states:
            log.feed(past.last_changed, past.state)
        state.compressor = log

    def compressor_averages(self, gid: str) -> tuple[Average, Average] | None:
        """Démarrages par heure : sur 24 h glissantes et depuis le dernier changement de profil."""
        state = self.states[gid]
        if state.compressor is None:
            return None
        now = dt_util.utcnow()
        day = state.compressor.average(now - timedelta(hours=24), now)
        profile = state.compressor.average(state.profile_changed_at or state.compressor.since, now)
        return day, profile

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
        if state.override or state.split_overrides:
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

        until = state.override_until
        if state.enabled and state.override and until is not None:
            if now < until:
                # Dérogation à durée choisie : les créneaux d'ici là sont ignorés.
                at_resume = current_occurrence(program, dt_util.as_local(until))
                state.next_change = until
                state.next_profile_id = at_resume.profile_id if at_resume else None
                self._timers[gid] = async_track_point_in_time(
                    self.hass, self._make_timer_action(gid, until), until
                )
                self._changed()
                return
            # Heure de reprise atteinte : retour au programme
            state.override_until = None
            force = True

        if state.enabled:
            if current is not None:
                key = f"{state.planning_id}|{current.start.isoformat()}"
                if force or key != state.last_slot_key:
                    state.last_slot_key = key
                    await self._async_apply(gid, current.profile_id, manual=False)
            elif force:
                state.override = False
                state.override_since = state.override_until = None
            if upcoming is not None:
                state.next_change = upcoming.start
                state.next_profile_id = upcoming.profile_id
                self._timers[gid] = async_track_point_in_time(
                    self.hass, self._make_timer_action(gid, upcoming.start), upcoming.start
                )
        await self._async_split_timers(gid, now)
        self._changed()

    async def _async_split_timers(self, gid: str, now: datetime) -> None:
        """Reprise des splits dont l'heure de reprise choisie est atteinte ; minuteurs des autres."""
        state = self.states[gid]
        for key in [k for k in self._timers if k.startswith(f"{gid}|")]:
            self._timers.pop(key)()
        if not state.enabled or state.override:
            return
        for entity_id, ovr in list(state.split_overrides.items()):
            if ovr.until is None:
                continue
            if ovr.until <= now:
                await self.async_resume_split(gid, entity_id, refresh=False)
                continue
            self._timers[f"{gid}|{entity_id}"] = async_track_point_in_time(
                self.hass, self._make_split_timer_action(gid, entity_id), ovr.until
            )

    def _make_split_timer_action(self, gid: str, entity_id: str) -> Callable[[datetime], Any]:
        async def _action(fired: datetime) -> None:
            self._timers.pop(f"{gid}|{entity_id}", None)
            await self.async_resume_split(gid, entity_id)

        return _action

    def _make_timer_action(self, gid: str, target: datetime) -> Callable[[datetime], Any]:
        async def _action(fired: datetime) -> None:
            self._timers.pop(gid, None)
            # Le minuteur peut se déclencher quelques millisecondes en avance.
            await self.async_refresh_group(gid, now=max(dt_util.now(), target))

        return _action

    def resume_at(self, gid: str) -> datetime | None:
        """Heure de reprise d'une dérogation : choisie, sinon le prochain créneau."""
        state = self.states[gid]
        if not state.override:
            return None
        if state.override_until is not None:
            return state.override_until
        upcoming = next_occurrence(self.program(gid, state.planning_id), dt_util.now())
        return upcoming.start if upcoming else None

    async def async_shift_override(self, gid: str, minutes: int) -> bool:
        """Boutons −30 / +30 : durée de la dérogation à partir de maintenant.

        Sans appui, elle court jusqu'au prochain créneau ; +30 la fixe à 30 min, puis
        60, 90… (au plus 24 h) ; revenir à 0 rend « jusqu'au prochain créneau ».
        False s'il n'y a pas de dérogation.
        """
        state = self.states[gid]
        if not state.override:
            return False
        state.override_until = _shifted_duration(state.override_until, minutes)
        await self.async_refresh_group(gid)
        return True

    def split_resume_at(self, gid: str, entity_id: str) -> datetime | None:
        """Heure de reprise d'un split en dérogation : choisie, sinon le prochain créneau."""
        ovr = self.states[gid].split_overrides.get(entity_id)
        if ovr is None:
            return None
        if ovr.until is not None:
            return ovr.until
        upcoming = next_occurrence(self.program(gid, self.states[gid].planning_id), dt_util.now())
        return upcoming.start if upcoming else None

    async def async_shift_split(self, gid: str, entity_id: str, minutes: int) -> bool:
        """Boutons −30 / +30 d'un split en dérogation : durée, comme pour le groupe."""
        ovr = self.states[gid].split_overrides.get(entity_id)
        if ovr is None:
            return False
        ovr.until = _shifted_duration(ovr.until, minutes)
        await self._async_split_timers(gid, dt_util.now())
        self._changed()
        return True

    async def async_resume_split(self, gid: str, entity_id: str, *, refresh: bool = True) -> None:
        """Remet un seul split au profil en cours du groupe."""
        state = self.states[gid]
        if state.split_overrides.pop(entity_id, None) is None:
            return
        _LOGGER.info("Groupe « %s » : %s reprend le programme", self.groups[gid]["name"], entity_id)
        if state.active_profile_id is not None:
            state.applied_at = dt_util.utcnow()  # nos propres commandes : pas de détection
            await self._async_apply_entity(gid, state.active_profile_id, entity_id)
        if refresh:
            await self._async_split_timers(gid, dt_util.now())
            self._changed()

    def split_overrides_info(self, gid: str) -> list[dict[str, Any]]:
        """Splits en dérogation : depuis, reprise et écarts avec le profil en cours."""
        state = self.states[gid]
        settings = (
            self._settings_for(gid, state.active_profile_id) if state.active_profile_id else {}
        )
        result = []
        for entity_id, ovr in state.split_overrides.items():
            resume = self.split_resume_at(gid, entity_id)
            current = self.hass.states.get(entity_id)
            result.append(
                {
                    "entity_id": entity_id,
                    "depuis": ovr.since.isoformat(),
                    "reprise": resume.isoformat() if resume else None,
                    "reprise_choisie": ovr.until is not None,
                    "ecarts": _differences(current, settings) if current is not None else [],
                }
            )
        return result

    def override_info(self, gid: str) -> dict[str, Any]:
        """Dérogation en cours : début, reprise, profil repris, créneau ignoré."""
        state = self.states[gid]
        resume = self.resume_at(gid)
        info: dict[str, Any] = {
            "derogation_depuis": state.override_since.isoformat() if state.override_since else None,
            "reprise": resume.isoformat() if resume else None,
            "reprise_choisie": state.override_until is not None,
            "reprise_profil": None,
            "creneau_ignore": None,
        }
        if resume is None:
            return info
        program = self.program(gid, state.planning_id)
        at_resume = current_occurrence(program, dt_util.as_local(resume))
        info["reprise_profil"] = self.profile_name(at_resume.profile_id) if at_resume else None
        upcoming = next_occurrence(program, dt_util.now())
        if upcoming is not None and upcoming.start < resume:
            info["creneau_ignore"] = {
                "heure": upcoming.start.isoformat(),
                "profil": self.profile_name(upcoming.profile_id),
            }
        return info

    async def async_select_profile(self, gid: str, profile_id: str) -> None:
        """Choix manuel d'un profil : il vaut jusqu'au prochain créneau."""
        await self._async_apply(gid, profile_id, manual=True)
        self._changed()

    async def async_select_planning(self, gid: str, planning_id: str) -> None:
        """Change le planning d'un groupe et applique aussitôt son créneau en cours."""
        self.states[gid].planning_id = planning_id
        self.states[gid].split_overrides.clear()
        self.states[gid].last_slot_key = None
        await self.async_refresh_group(gid, force=True)

    async def async_select_planning_all(self, planning_id: str) -> None:
        for gid in self.groups:
            await self.async_select_planning(gid, planning_id)

    async def async_set_enabled(self, gid: str, enabled: bool) -> None:
        state = self.states[gid]
        state.enabled = enabled
        state.split_overrides.clear()
        if enabled:
            state.override = False
        await self.async_refresh_group(gid, force=enabled)

    async def async_resume(self, gid: str) -> None:
        """Annule une dérogation : réapplique le profil programmé maintenant."""
        self.states[gid].enabled = True
        self.states[gid].override = False
        self.states[gid].split_overrides.clear()
        await self.async_refresh_group(gid, force=True)

    async def async_manual_settings(self, gid: str, settings: dict[str, Any]) -> None:
        """Réglage manuel (depuis la carte), envoyé à tous les splits du groupe.

        Il vaut dérogation jusqu'au prochain créneau, comme un choix de profil.
        """
        state = self.states[gid]
        state.applied_at = dt_util.utcnow()  # nos propres commandes : pas de détection
        comfort_only = all(key in _NOT_AN_OVERRIDE for key in settings)
        if comfort_only:
            # Ventilateur / oscillation : envoyés à tous les splits, sans dérogation ;
            # le prochain changement de profil les rétablit.
            _LOGGER.info("Groupe « %s » : réglage %s (sans dérogation)", self.groups[gid]["name"], settings)
            for entity_id in self.groups[gid][CONF_CLIMATES]:
                current = self.hass.states.get(entity_id)
                if current is None or current.state in _NOT_READY:
                    continue
                try:
                    await self._async_send(entity_id, current, settings)
                except (HomeAssistantError, ValueError) as err:
                    _LOGGER.warning("Échec du réglage de %s : %s", entity_id, err)
            self._changed()
            return
        if state.enabled and state.active_profile_id is not None:
            if not state.override:
                state.override_since = dt_util.utcnow()
            state.override = True
            state.hand_set = True
        state.split_overrides.clear()  # le réglage de la carte vaut pour tous les splits
        if state.override:
            state.manual_settings.update(
                {k: v for k, v in settings.items() if k in (ATTR_TEMPERATURE, ATTR_HVAC_MODE)}
            )
        _LOGGER.info("Groupe « %s » : réglage manuel %s", self.groups[gid]["name"], settings)
        for entity_id in self.groups[gid][CONF_CLIMATES]:
            current = self.hass.states.get(entity_id)
            if current is None or current.state in _NOT_READY:
                continue
            try:
                await self._async_send(entity_id, current, settings)
            except (HomeAssistantError, ValueError) as err:
                _LOGGER.warning("Échec du réglage manuel de %s : %s", entity_id, err)
        self._changed()

    # ------------------------------------------------------------------ application aux splits

    async def _async_apply(self, gid: str, profile_id: str, *, manual: bool) -> None:
        profile = self.profiles.get(profile_id)
        if profile is None:
            _LOGGER.warning("Profil %s introuvable pour le groupe %s", profile_id, gid)
            return
        state = self.states[gid]
        if profile_id != state.active_profile_id or state.profile_changed_at is None:
            state.profile_changed_at = dt_util.utcnow()
        state.active_profile_id = profile_id
        if manual and not state.override:
            state.override_since = dt_util.utcnow()
        if not manual:
            state.override_since = state.override_until = None
        state.override = manual
        state.hand_set = False
        state.manual_settings = {}
        state.applied_at = dt_util.utcnow()
        state.effective_target = self._target_for(gid, profile)
        state.target_changed_at = state.applied_at
        _LOGGER.info(
            "Groupe « %s » : profil « %s »%s",
            self.groups[gid]["name"],
            profile["name"],
            " (choix manuel)" if manual else "",
        )
        now = dt_util.utcnow()
        for entity_id in self.groups[gid][CONF_CLIMATES]:
            ovr = state.split_overrides.get(entity_id)
            if ovr is not None:
                if not manual and ovr.until is not None and now < ovr.until:
                    continue  # reprise choisie plus tard : ce créneau est ignoré pour ce split
                del state.split_overrides[entity_id]
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
            await self._async_send(entity_id, current, self._settings_for(gid, profile_id))
        except (HomeAssistantError, ValueError) as err:
            _LOGGER.warning("Échec de l'envoi du profil à %s : %s", entity_id, err)

    async def _async_send(self, entity_id: str, current: State, profile: dict) -> None:
        attrs = current.attributes

        async def call(service: str, **data: Any) -> None:
            await self.hass.services.async_call(
                "climate", service, {ATTR_ENTITY_ID: entity_id, **data}, blocking=True
            )

        await self._async_send_always(entity_id, current)

        hvac_mode = profile.get(ATTR_HVAC_MODE)
        if hvac_mode is not None and hvac_mode != current.state:
            if hvac_mode not in attrs.get("hvac_modes", []):
                _LOGGER.warning("%s ne gère pas le mode %s", entity_id, hvac_mode)
                hvac_mode = None
            else:
                await call("set_hvac_mode", hvac_mode=hvac_mode)
        if (quiet := profile.get(ATTR_QUIET)) is not None and not self.always_quiet:
            await self._async_send_quiet(entity_id, quiet)
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

    async def _async_send_always(self, entity_id: str, current: State) -> None:
        """Réglages généraux multi-split : préréglage Normal et/ou silence extérieur, renvoyés
        à chaque commande, même si le split les indique déjà (sa réponse n'est pas fiable)."""
        if self.send_normal:
            presets = current.attributes.get("preset_modes") or []
            normal = "home" if "home" in presets else "none" if "none" in presets else None
            if normal is None:
                _LOGGER.debug("%s : pas de préréglage Normal (home / none)", entity_id)
            else:
                try:
                    await self.hass.services.async_call(
                        "climate", "set_preset_mode",
                        {ATTR_ENTITY_ID: entity_id, "preset_mode": normal}, blocking=True,
                    )
                except (HomeAssistantError, ValueError) as err:
                    _LOGGER.warning("%s : échec du préréglage Normal : %s", entity_id, err)
        if self.always_quiet:
            switch = self.quiet_switches.get(entity_id)
            state = self.hass.states.get(switch) if switch else None
            if state is None or state.state in _NOT_READY:
                _LOGGER.warning(
                    "%s : unité extérieure silencieuse indisponible (interrupteur Faikout %s)",
                    entity_id, switch or "absent",
                )
            else:
                try:
                    await self.hass.services.async_call(
                        "switch", "turn_on", {ATTR_ENTITY_ID: switch}, blocking=True
                    )
                except HomeAssistantError as err:
                    _LOGGER.warning("%s : échec : %s", switch, err)

    async def _async_send_quiet(self, entity_id: str, on: bool) -> bool:
        """Unité extérieure silencieuse d'un split ; False si l'interrupteur ne répond pas."""
        switch = self.quiet_switches.get(entity_id)
        current = self.hass.states.get(switch) if switch else None
        if current is None or current.state in _NOT_READY:
            _LOGGER.warning(
                "%s : unité extérieure silencieuse indisponible (interrupteur Faikout %s ; "
                "vérifier l'option « HA switches » de Faikout)", entity_id, switch or "absent",
            )
            return False
        if current.state != ("on" if on else "off"):
            try:
                await self.hass.services.async_call(
                    "switch", "turn_on" if on else "turn_off", {ATTR_ENTITY_ID: switch}, blocking=True
                )
            except HomeAssistantError as err:
                _LOGGER.warning("%s : échec : %s", switch, err)
                return False
        return True

    async def async_set_quiet(self, gid: str, on: bool) -> list[str]:
        """Depuis la carte : silence de l'unité extérieure pour les splits du groupe.

        Ce n'est pas une dérogation : la programmation continue, et le profil suivant
        qui précise ce réglage le réapplique.
        """
        failed = []
        for entity_id in self.groups[gid][CONF_CLIMATES]:
            if entity_id in self.quiet_switches and not await self._async_send_quiet(entity_id, on):
                failed.append(entity_id)
        return failed

    def quiet_info(self, gid: str) -> dict[str, dict[str, str | None]]:
        """Diagnostic : interrupteur « quiet » de chaque split et son état."""
        result = {}
        for entity_id in self.groups[gid][CONF_CLIMATES]:
            switch = self.quiet_switches.get(entity_id)
            st = self.hass.states.get(switch) if switch else None
            result[entity_id] = {
                "interrupteur": switch,
                "etat": st.state if st else ("absent" if switch else None),
            }
        return result

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
        if entity_id in self.pump_of or any(
            entity_id in st.split_overrides for st in self.states.values()
        ):
            self._notify()  # écarts et conflits de mode affichés pour ce split : à jour
        for gid, group in self.groups.items():
            state = self.states[gid]
            if (
                entity_id not in group[CONF_CLIMATES]
                or not state.enabled
                or (state.applied_at is not None and now - state.applied_at < GRACE_PERIOD)
            ):
                continue
            single = len(group[CONF_CLIMATES]) == 1
            if state.override:
                if single and state.hand_set:
                    # Groupe d'un seul split en dérogation : la consigne du groupe suit le split
                    state.manual_settings = _manual_from(new)
                    self._changed()
                continue
            if entity_id in state.split_overrides or state.active_profile_id is None:
                continue
            profile = self._settings_for(gid, state.active_profile_id)
            if not _deviates(new, profile):
                continue
            if single:
                _LOGGER.info(
                    "Groupe « %s » : réglage manuel détecté sur %s (seul split du groupe), "
                    "groupe en dérogation jusqu'au prochain créneau",
                    group["name"],
                    entity_id,
                )
                state.override_since = now
                state.override = True
                state.hand_set = True
                state.manual_settings = _manual_from(new)
            else:
                _LOGGER.info(
                    "Groupe « %s » : réglage manuel détecté sur %s, ce split seul est en "
                    "dérogation jusqu'au prochain créneau",
                    group["name"],
                    entity_id,
                )
                state.split_overrides[entity_id] = SplitOverride(since=now)
            self._changed()


def _manual_from(split: State) -> dict[str, Any]:
    """Consigne et mode d'un split, comme réglage manuel du groupe."""
    settings: dict[str, Any] = {ATTR_HVAC_MODE: split.state}
    if (temperature := split.attributes.get("temperature")) is not None:
        settings[ATTR_TEMPERATURE] = float(temperature)
    return settings


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
    # Ventilateur et oscillation : pas des dérogations (le prochain profil les rétablit)
    return False


def _differences(state: State, profile: dict) -> list[dict[str, Any]]:
    """Réglages du split qui s'écartent du profil : [{reglage, valeur, prevu}]."""
    if state.state in _NOT_READY:
        return []
    attrs = state.attributes
    result: list[dict[str, Any]] = []
    hvac_mode = profile.get(ATTR_HVAC_MODE)
    if hvac_mode is not None and state.state != hvac_mode:
        result.append({"reglage": "hvac_mode", "valeur": state.state, "prevu": hvac_mode})
    if state.state == "off":
        return result
    temperature = profile.get(ATTR_TEMPERATURE)
    current = attrs.get("temperature")
    if temperature is not None and current is not None and state.state != "fan_only":
        wanted = target_temperature(attrs, temperature)
        if abs(float(current) - wanted) > TEMPERATURE_TOLERANCE:
            result.append({"reglage": "temperature", "valeur": float(current), "prevu": wanted})
    return result


DURATION_STEP = timedelta(minutes=30)


def _shifted_duration(until: datetime | None, minutes: int) -> datetime | None:
    """Nouvelle fin de dérogation après un appui sur −30 / +30.

    La durée restante est arrondie à la demi-heure supérieure puis décalée ; une durée
    nulle (ou négative) rend None : « jusqu'au prochain créneau ». Au plus 24 h.
    """
    now = dt_util.utcnow()
    steps = 0
    if until is not None and until > now:
        steps = -(-(until - now) // DURATION_STEP)  # arrondi supérieur
    steps += round(minutes / 30)
    if steps <= 0:
        return None
    return now + min(steps * DURATION_STEP, timedelta(hours=24))


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


def _parse(value: str | None) -> datetime | None:
    return dt_util.parse_datetime(value) if value else None


def detect_outdoor_sensor(hass: HomeAssistant, climates: list[str]) -> str | None:
    """Capteur de température extérieure du même appareil qu'un split (Faikout « Outside »)."""
    from homeassistant.helpers import entity_registry as er

    from .planning import normalize

    registry = er.async_get(hass)
    for climate in climates:
        entry = registry.async_get(climate)
        if entry is None or entry.device_id is None:
            continue
        for candidate in er.async_entries_for_device(registry, entry.device_id):
            label = normalize(
                f"{candidate.entity_id} {candidate.original_name or ''} {candidate.name or ''}"
            )
            if candidate.domain == "sensor" and any(
                word in label for word in ("outside", "outdoor", "exterieur", "exterieure")
            ):
                return candidate.entity_id
    return None
