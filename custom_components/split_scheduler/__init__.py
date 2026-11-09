"""Programmation des splits de pompe à chaleur (groupes, profils, plannings)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_GROUPS, DOMAIN, PLATFORMS
from .scheduler import SplitScheduler

type SplitSchedulerConfigEntry = ConfigEntry[SplitScheduler]


async def async_setup_entry(hass: HomeAssistant, entry: SplitSchedulerConfigEntry) -> bool:
    """Met en place l'intégration."""
    scheduler = SplitScheduler(hass, entry)
    await scheduler.async_load()
    entry.runtime_data = scheduler

    _remove_deleted_groups(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    scheduler.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SplitSchedulerConfigEntry) -> bool:
    """Décharge l'intégration."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded


async def _async_options_updated(hass: HomeAssistant, entry: SplitSchedulerConfigEntry) -> None:
    """Recharge après modification des groupes, profils ou plannings."""
    await hass.config_entries.async_reload(entry.entry_id)


def _remove_deleted_groups(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Supprime les appareils (et leurs entités) des groupes supprimés."""
    registry = dr.async_get(hass)
    valid = {(DOMAIN, entry.entry_id)} | {
        (DOMAIN, f"{entry.entry_id}_{gid}") for gid in entry.options.get(CONF_GROUPS, {})
    }
    for device in dr.async_entries_for_config_entry(registry, entry.entry_id):
        if not device.identifiers & valid:
            registry.async_remove_device(device.id)
