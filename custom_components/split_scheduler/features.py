"""Fonctions Daikin (confort, Streamer, présence, extérieur silencieux) via Faikout.

Faikout publie ces fonctions comme interrupteurs MQTT sur l'appareil du split
(option « HA switches ») ; leur unique_id est celui du thermostat suivi du
suffixe de la fonction (ex. « …comfort »).
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import FEATURES


def feature_switches(hass: HomeAssistant, climate_id: str) -> dict[str, str]:
    """Interrupteurs des fonctions Daikin d'un split : {clé du profil: entity_id}."""
    registry = er.async_get(hass)
    climate = registry.async_get(climate_id)
    if climate is None or climate.device_id is None:
        return {}
    switches = [
        e for e in er.async_entries_for_device(registry, climate.device_id) if e.domain == "switch"
    ]
    found: dict[str, str] = {}
    for key, suffix in FEATURES.items():
        exact = f"{climate.unique_id}{suffix}"
        match = next((e for e in switches if e.unique_id == exact), None) or next(
            (e for e in switches if str(e.unique_id).endswith(suffix)), None
        )
        if match is not None:
            found[key] = match.entity_id
    return found
