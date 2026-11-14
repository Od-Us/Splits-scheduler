"""Unité extérieure silencieuse (« quiet ») d'un split Faikout.

Faikout publie cette fonction comme interrupteur MQTT sur l'appareil du split
(option « HA switches ») ; son unique_id est celui du thermostat suivi de
« quiet ».
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import QUIET_SUFFIX


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
