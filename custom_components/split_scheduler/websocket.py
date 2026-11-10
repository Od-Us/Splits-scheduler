"""API websocket utilisée par la carte du tableau de bord."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_SWING_MODE,
    ATTR_TEMPERATURE,
    CONF_CLIMATES,
    CONF_COMPRESSOR,
    CONF_PROGRAMS,
    DOMAIN,
    describe_profile,
    profile_color,
)
from .scheduler import SplitScheduler

# Clé d'entité -> (domaine, suffixe de l'identifiant unique)
_GROUP_ENTITIES = {
    "profile": ("select", "profile"),
    "planning": ("select", "planning"),
    "programming": ("switch", "programming"),
    "resume": ("button", "resume"),
    "status": ("sensor", "status"),
    "next_change": ("sensor", "next_change"),
    "starts_24h": ("sensor", "compressor_starts_24h"),
    "starts_profile": ("sensor", "compressor_starts_profile"),
}


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_info)
    websocket_api.async_register_command(hass, ws_manual)


def _scheduler(hass: HomeAssistant) -> SplitScheduler | None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data
    return None


@websocket_api.websocket_command({vol.Required("type"): "split_scheduler/info"})
@callback
def ws_info(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Groupes, entités, profils (avec couleurs) et programmes."""
    scheduler = _scheduler(hass)
    if scheduler is None:
        connection.send_error(msg["id"], "not_loaded", "Programmation des splits non chargée")
        return
    registry = er.async_get(hass)
    entry_id = scheduler.entry.entry_id

    def entity(domain: str, unique_id: str) -> str | None:
        return registry.async_get_entity_id(domain, DOMAIN, unique_id)

    language = hass.config.language
    connection.send_result(
        msg["id"],
        {
            "time_zone": hass.config.time_zone,
            "global_planning": entity("select", f"{entry_id}_global_planning"),
            "outdoor": scheduler.outdoor_entity,
            "groups": [
                {
                    "id": gid,
                    "name": group["name"],
                    "climates": group[CONF_CLIMATES],
                    "compressor": group.get(CONF_COMPRESSOR),
                    "entities": {
                        key: entity(domain, f"{entry_id}_{gid}_{suffix}")
                        for key, (domain, suffix) in _GROUP_ENTITIES.items()
                    },
                }
                for gid, group in scheduler.groups.items()
            ],
            "profiles": [
                {
                    "id": pid,
                    "name": profile["name"],
                    "color": profile_color(profile["name"]),
                    "summary": describe_profile(profile, language),
                }
                for pid, profile in scheduler.profiles.items()
            ],
            "plannings": [
                {"id": plid, "name": planning["name"], "programs": planning.get(CONF_PROGRAMS, {})}
                for plid, planning in scheduler.plannings.items()
            ],
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "split_scheduler/manual",
        vol.Required("group_id"): str,
        vol.Optional(ATTR_TEMPERATURE): vol.Coerce(float),
        vol.Optional(ATTR_HVAC_MODE): str,
        vol.Optional(ATTR_FAN_MODE): str,
        vol.Optional(ATTR_SWING_MODE): str,
    }
)
@websocket_api.async_response
async def ws_manual(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Réglage manuel d'un groupe (dérogation jusqu'au prochain créneau)."""
    scheduler = _scheduler(hass)
    if scheduler is None or msg["group_id"] not in scheduler.groups:
        connection.send_error(msg["id"], "not_found", "Groupe inconnu")
        return
    settings = {
        key: msg[key]
        for key in (ATTR_HVAC_MODE, ATTR_TEMPERATURE, ATTR_FAN_MODE, ATTR_SWING_MODE)
        if key in msg
    }
    if not settings:
        connection.send_error(msg["id"], "invalid", "Aucun réglage")
        return
    await scheduler.async_manual_settings(msg["group_id"], settings)
    connection.send_result(msg["id"])
