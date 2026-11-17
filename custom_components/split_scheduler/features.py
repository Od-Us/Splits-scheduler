"""Unité extérieure silencieuse (« quiet ») d'un split Faikout.

Faikout publie cette fonction comme interrupteur MQTT sur l'appareil du split
(option « HA switches ») ; son unique_id est celui du thermostat suivi de
« quiet ».
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import QUIET_SUFFIX
from .planning import normalize


def quiet_switch(hass: HomeAssistant, climate_id: str) -> str | None:
    """Interrupteur « Quiet outdoor » d'un split, s'il existe."""
    registry = er.async_get(hass)
    climate = registry.async_get(climate_id)
    if climate is None or climate.device_id is None:
        return None
    switches = [
        e for e in er.async_entries_for_device(registry, climate.device_id) if e.domain == "switch"
    ]
    exact = f"{climate.unique_id}{QUIET_SUFFIX}"
    match = next((e for e in switches if e.unique_id == exact), None) or next(
        (e for e in switches if str(e.unique_id).endswith(QUIET_SUFFIX)), None
    )
    return match.entity_id if match else None


def compressor_sensor(hass: HomeAssistant, climate_id: str) -> str | None:
    """Capteur « Compressor » de Faikout sur l'appareil d'un split."""
    registry = er.async_get(hass)
    entry = registry.async_get(climate_id)
    if entry is None or entry.device_id is None:
        return None
    for candidate in er.async_entries_for_device(registry, entry.device_id):
        label = normalize(f"{candidate.entity_id} {candidate.original_name or ''} {candidate.name or ''}")
        if candidate.domain == "sensor" and "compress" in label:
            return candidate.entity_id
    return None
