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

from .features import compressor_sensor, quiet_switch
from .planning import normalize, profiles_used

from .const import (
    ATTR_HVAC_MODE,
    ATTR_OUTDOOR_DELTA,
    ATTR_QUIET,
    ATTR_TEMPERATURE,
    CONF_ALLOWED,
    CONF_COMPRESSOR_MAX,
    CONF_COMPRESSORS,
    CONF_ENERGY,
    CONF_MODEL,
    CONF_OFFSETS,
    CONF_POWER,
    HVAC_MODES,
    PROFILE_SETTINGS,
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
    ATTR_COLOR,
    color_of,
    valid_color,
)
from .const import _EXTRA_COLORS, _PROFILE_COLORS

_TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
_ID = re.compile(r"^[A-Za-z0-9_]{1,40}$")
_MODE_LISTS = {"fan_mode": "fan_modes", "swing_mode": "swing_modes",
               "swing_horizontal_mode": "swing_horizontal_modes"}


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

    climates = sorted({eid for g in groups.values() for eid in g[CONF_CLIMATES]}
                      | {eid for hp in pumps.values() for eid in hp.get(CONF_CLIMATES, [])})
    states = [st for eid in climates if (st := hass.states.get(eid)) is not None]

    def known(attr: str) -> list[str]:
        found: list[str] = []
        for st in states:
            for value in st.attributes.get(attr) or []:
                if str(value) not in found:
                    found.append(str(value))
        return found

    return {
        "admin": is_admin,
        "names": {eid: name(eid) for eid in climates},
        "modes": {
            "hvac_mode": [m for m in HVAC_MODES if m in known("hvac_modes")] or HVAC_MODES,
            **{key: known(attr) for key, attr in _MODE_LISTS.items()},
        },
        "quiet_available": any(quiet_switch(hass, eid) for eid in climates),
        "detected_compressors": {eid: sensor for eid in climates if (sensor := compressor_sensor(hass, eid))},
        "offsets": options.get(CONF_OFFSETS, {}),
        "colors": {"prefixes": [list(x) for x in _PROFILE_COLORS], "extra": list(_EXTRA_COLORS)},
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
            {**{k: v for k, v in p.items() if k != "pos"}, "id": pid, "color": color_of(p), "color_set": p.get(ATTR_COLOR),
             "summary": describe_profile(p, language)}
            for pid, p in profiles.items()
        ],
        "plannings": [
            {"id": plid, "name": pl["name"], "allowed": allowed_profiles(pl, profiles),
             "programs": pl.get(CONF_PROGRAMS, {})}
            for plid, pl in plannings.items()
        ],
        "heat_pumps": [
            {**{k: v for k, v in hp.items() if k != "pos"}, "id": hpid, "climates": hp.get(CONF_CLIMATES, []),
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
    if "profiles" in changes:
        new[CONF_PROFILES] = _profiles(changes["profiles"])
    if "plannings" in changes:
        new[CONF_PLANNINGS] = _plannings(changes["plannings"], new)
    if "groups" in changes:
        new[CONF_GROUPS] = _groups(changes["groups"])
    if "heat_pumps" in changes:
        new[CONF_HEAT_PUMPS] = _heat_pumps(changes["heat_pumps"])
    if "offsets" in changes:
        new[CONF_OFFSETS] = _offsets(changes["offsets"])
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
    _check_integrity(new)
    return new


def _items(items: Any, kind: str) -> list[tuple[str, dict]]:
    """Liste ordonnée [{id, name, …}] -> [(id, élément)], noms obligatoires et uniques."""
    if not isinstance(items, list):
        raise ValueError(f"{kind} : liste attendue")
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    out = []
    for item in items:
        if not isinstance(item, dict) or not _ID.match(str(item.get("id", ""))):
            raise ValueError(f"{kind} : identifiant invalide")
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError(f"{kind} : le nom est obligatoire")
        if normalize(name) in seen_names:
            raise ValueError(f"{kind} : le nom « {name} » est déjà utilisé")
        if item["id"] in seen_ids:
            raise ValueError(f"{kind} : identifiant en double")
        seen_names.add(normalize(name))
        seen_ids.add(item["id"])
        out.append((item["id"], {**item, "name": name}))
    return out


def _number(value: Any, low: float, high: float, what: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"{what} : nombre attendu") from err
    if not low <= number <= high:
        raise ValueError(f"{what} : entre {low:g} et {high:g}")
    return number


def _profiles(items: Any) -> dict:
    result: dict[str, dict] = {}
    for pos, (pid, item) in enumerate(_items(items, "Profils")):
        profile: dict[str, Any] = {"name": item["name"], "pos": pos}
        for setting in PROFILE_SETTINGS:
            value = item.get(setting)
            if value in (None, ""):
                continue
            if setting == ATTR_TEMPERATURE:
                profile[setting] = _number(value, 5, 35, f"{item['name']} : consigne")
            elif setting == ATTR_HVAC_MODE and value not in HVAC_MODES:
                raise ValueError(f"{item['name']} : mode inconnu")
            else:
                profile[setting] = str(value)
        if item.get("color_set"):
            if (color := valid_color(item["color_set"])) is None:
                raise ValueError(f"{item['name']} : couleur invalide")
            profile[ATTR_COLOR] = color
        if isinstance(item.get(ATTR_QUIET), bool):
            profile[ATTR_QUIET] = item[ATTR_QUIET]
        if item.get(ATTR_OUTDOOR_DELTA) not in (None, ""):
            profile[ATTR_OUTDOOR_DELTA] = _number(item[ATTR_OUTDOOR_DELTA], 1, 30, f"{item['name']} : écart extérieur")
        result[pid] = profile
    if not result:
        raise ValueError("Il faut garder au moins un profil.")
    return result


def _plannings(items: Any, current: dict) -> dict:
    old = current.get(CONF_PLANNINGS, {})
    profiles = current.get(CONF_PROFILES, {})
    result: dict[str, dict] = {}
    for pos, (plid, item) in enumerate(_items(items, "Plannings")):
        allowed = [pid for pid in profiles if pid in (item.get("allowed") or [])]
        if not allowed:
            raise ValueError(f"{item['name']} : cochez au moins un profil")
        source = old.get(plid) or old.get(item.get("copy_from") or "", {})
        result[plid] = {"name": item["name"], "pos": pos, CONF_ALLOWED: allowed,
                        CONF_PROGRAMS: copy.deepcopy(source.get(CONF_PROGRAMS, {}))}
    if not result:
        raise ValueError("Il faut garder au moins un planning.")
    return result


def _groups(items: Any) -> dict:
    result: dict[str, dict] = {}
    for pos, (gid, item) in enumerate(_items(items, "Groupes")):
        climates = [str(e) for e in item.get(CONF_CLIMATES) or [] if str(e).startswith("climate.")]
        if not climates:
            raise ValueError(f"{item['name']} : choisissez au moins un split")
        result[gid] = {"name": item["name"], "pos": pos, CONF_CLIMATES: list(dict.fromkeys(climates))}
    return result


def _heat_pumps(items: Any) -> dict:
    result: dict[str, dict] = {}
    taken: set[str] = set()
    for pos, (hpid, item) in enumerate(_items(items, "Pompes à chaleur")):
        climates = list(dict.fromkeys(str(e) for e in item.get(CONF_CLIMATES) or [] if str(e).startswith("climate.")))
        if not climates:
            raise ValueError(f"{item['name']} : choisissez au moins un split")
        if taken & set(climates):
            raise ValueError(f"{item['name']} : un split appartient déjà à une autre pompe à chaleur")
        taken |= set(climates)
        pump: dict[str, Any] = {"name": item["name"], "pos": pos, CONF_CLIMATES: climates}
        if item.get(CONF_PRIORITY):
            if item[CONF_PRIORITY] not in climates:
                raise ValueError(f"{item['name']} : le split prioritaire doit faire partie de ses splits")
            pump[CONF_PRIORITY] = item[CONF_PRIORITY]
        if str(item.get(CONF_MODEL) or "").strip():
            pump[CONF_MODEL] = str(item[CONF_MODEL]).strip()
        if item.get(CONF_COMPRESSORS):
            pump[CONF_COMPRESSORS] = [str(e) for e in item[CONF_COMPRESSORS] if str(e).startswith("sensor.")]
        if item.get(CONF_COMPRESSOR_MAX) not in (None, "", 0):
            pump[CONF_COMPRESSOR_MAX] = _number(item[CONF_COMPRESSOR_MAX], 1, 15000, f"{item['name']} : fréquence maximale")
        for key in (CONF_POWER, CONF_ENERGY):
            if str(item.get(key) or "").startswith("sensor."):
                pump[key] = item[key]
        result[hpid] = pump
    return result


def _offsets(values: Any) -> dict:
    if not isinstance(values, dict):
        raise ValueError("décalages invalides")
    result: dict[str, dict] = {}
    for eid, sides in values.items():
        split = {}
        for side in ("heat", "cool"):
            value = (sides or {}).get(side)
            if value not in (None, "", 0):
                split[side] = round(_number(value, -3, 3, "décalage") * 2) / 2
        if split:
            result[str(eid)] = split
    return result


def _check_integrity(options: dict) -> None:
    """Programmes cohérents : groupes existants, profils existants et autorisés."""
    profiles = options.get(CONF_PROFILES, {})
    groups = options.get(CONF_GROUPS, {})
    for planning in options.get(CONF_PLANNINGS, {}).values():
        programs = planning.get(CONF_PROGRAMS, {})
        for gid in [g for g in programs if g not in groups]:
            programs.pop(gid)   # groupe supprimé : son programme aussi
        allowed = set(allowed_profiles(planning, profiles))
        for program in programs.values():
            missing = profiles_used(program) - set(profiles)
            if missing:
                raise ValueError("Profil supprimé mais encore utilisé dans un programme ; retirez-le d'abord des programmes.")
            refused = profiles_used(program) - allowed
            if refused:
                names = ", ".join(sorted(profiles[p]["name"] for p in refused))
                raise ValueError(f"{planning['name']} : {names} utilisé dans un programme mais non autorisé")


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
        vol.Optional("profiles"): list,
        vol.Optional("plannings"): list,
        vol.Optional("groups"): list,
        vol.Optional("heat_pumps"): list,
        vol.Optional("offsets"): dict,
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
