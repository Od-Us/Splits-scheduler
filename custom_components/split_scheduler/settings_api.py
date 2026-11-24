"""API de la carte de réglages : lecture et enregistrement de la configuration.

Les mêmes contrôles que le menu Paramètres de l'intégration ; l'enregistrement remplace
les options d'un coup, ce qui recharge l'intégration (comme « Enregistrer et fermer »).
"""

from __future__ import annotations

import copy
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, callback

from .const import (
    ATTR_HVAC_MODE,
    CONF_ALWAYS_QUIET,
    CONF_CLIMATES,
    CONF_GROUPS,
    CONF_HEAT_PUMPS,
    CONF_OUTDOOR,
    CONF_PLANNINGS,
    CONF_PRIORITY,
    CONF_PROFILES,
    CONF_PROGRAMS,
    CONF_SEND_NORMAL,
    CONF_SETTINGS,
    DOMAIN,
    allowed_profiles,
    describe_profile,
    ordered,
    profile_color,
)

_TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_config_get)
    websocket_api.async_register_command(hass, ws_config_save)


def _entry(hass: HomeAssistant) -> ConfigEntry | None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry
    return None


def config_view(hass: HomeAssistant, options: dict, is_admin: bool) -> dict[str, Any]:
    """Configuration présentée à la carte de réglages."""
    language = hass.config.language
    groups = ordered(options.get(CONF_GROUPS, {}))
    profiles = ordered(options.get(CONF_PROFILES, {}))
    plannings = ordered(options.get(CONF_PLANNINGS, {}))
    pumps = ordered(options.get(CONF_HEAT_PUMPS, {}))
    settings = options.get(CONF_SETTINGS, {})

    def name(eid: str) -> str:
        state = hass.states.get(eid)
        return state.name if state else eid

    return {
        "admin": is_admin,
        "version": hass.data.get(f"{DOMAIN}_version"),
        "settings": {
            CONF_OUTDOOR: settings.get(CONF_OUTDOOR),
            CONF_SEND_NORMAL: bool(settings.get(CONF_SEND_NORMAL)),
            CONF_ALWAYS_QUIET: bool(settings.get(CONF_ALWAYS_QUIET)),
        },
        "groups": [
            {"id": gid, "name": g["name"], "climates": g[CONF_CLIMATES],
             "names": {eid: name(eid) for eid in g[CONF_CLIMATES]}}
            for gid, g in groups.items()
        ],
        "profiles": [
            {"id": pid, "name": p["name"], "color": profile_color(p["name"]),
             "summary": describe_profile(p, language), "hvac_mode": p.get(ATTR_HVAC_MODE)}
            for pid, p in profiles.items()
        ],
        "plannings": [
            {"id": plid, "name": pl["name"], "allowed": allowed_profiles(pl, profiles),
             "programs": pl.get(CONF_PROGRAMS, {})}
            for plid, pl in plannings.items()
        ],
        "heat_pumps": [
            {"id": hpid, "name": hp["name"], "climates": hp.get(CONF_CLIMATES, []),
             "priority": hp.get(CONF_PRIORITY),
             "priority_name": name(hp[CONF_PRIORITY]) if hp.get(CONF_PRIORITY) else None}
            for hpid, hp in pumps.items()
        ],
    }


def validate_program(program: Any, allowed: list[str]) -> dict[str, list[list[str]]]:
    """Programme hebdomadaire valide et trié, sinon ValueError (message lisible)."""
    if not isinstance(program, dict):
        raise ValueError("programme invalide")
    result: dict[str, list[list[str]]] = {}
    for day, slots in program.items():
        if day not in {str(d) for d in range(7)}:
            raise ValueError(f"jour invalide : {day}")
        seen: dict[str, str] = {}
        for slot in slots or []:
            if not isinstance(slot, (list, tuple)) or len(slot) != 2:
                raise ValueError("ligne invalide")
            hhmm, pid = str(slot[0]), str(slot[1])
            if not _TIME.match(hhmm):
                raise ValueError(f"heure invalide : {hhmm}")
            if pid not in allowed:
                raise ValueError(f"profil non autorisé dans ce planning : {pid}")
            if hhmm in seen:
                raise ValueError(f"deux lignes à {hhmm}")
            seen[hhmm] = pid
        if seen:
            result[day] = [[t, seen[t]] for t in sorted(seen)]
    return result


def apply_changes(options: dict, changes: dict) -> dict:
    """Nouvelles options après les modifications de la carte (ValueError si refusées)."""
    new = copy.deepcopy(dict(options))
    profiles = new.get(CONF_PROFILES, {})
    groups = new.get(CONF_GROUPS, {})
    for plid, programs in (changes.get("programs") or {}).items():
        planning = new.get(CONF_PLANNINGS, {}).get(plid)
        if planning is None:
            raise ValueError(f"planning inconnu : {plid}")
        allowed = allowed_profiles(planning, profiles)
        target = planning.setdefault(CONF_PROGRAMS, {})
        for gid, program in programs.items():
            if gid not in groups:
                raise ValueError(f"groupe inconnu : {gid}")
            cleaned = validate_program(program, allowed)
            if cleaned:
                target[gid] = cleaned
            else:
                target.pop(gid, None)
    if (settings := changes.get("settings")) is not None:
        current = dict(new.get(CONF_SETTINGS, {}))
        outdoor = settings.get(CONF_OUTDOOR)
        if outdoor:
            if not str(outdoor).startswith("sensor."):
                raise ValueError("capteur extérieur invalide")
            current[CONF_OUTDOOR] = outdoor
        else:
            current.pop(CONF_OUTDOOR, None)
        for key in (CONF_SEND_NORMAL, CONF_ALWAYS_QUIET):
            if key in settings:
                current[key] = bool(settings[key])
        new[CONF_SETTINGS] = current
    return new


@websocket_api.websocket_command({vol.Required("type"): "split_scheduler/config/get"})
@callback
def ws_config_get(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Configuration pour la carte de réglages (lecture seule hors administrateurs)."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "Programmation des splits non chargée")
        return
    connection.send_result(msg["id"], config_view(hass, dict(entry.options), connection.user.is_admin))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "split_scheduler/config/save",
        vol.Optional("programs"): dict,
        vol.Optional("settings"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_config_save(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Enregistre les modifications de la carte (administrateurs) et recharge l'intégration."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "Programmation des splits non chargée")
        return
    try:
        options = apply_changes(dict(entry.options), msg)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid", str(err))
        return
    hass.config_entries.async_update_entry(entry, options=options)
    connection.send_result(msg["id"], {"saved": True})
