"""Programmation des splits de pompe à chaleur (groupes, profils, plannings)."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from . import websocket
from .const import (
    CARD_FILENAME,
    CARD_URL_BASE,
    CONF_GROUPS,
    CONF_MIGRATIONS,
    CONF_POS,
    CONF_PROFILES,
    DOMAIN,
    MIGRATION_SUMMER_PROFILES,
    PLATFORMS,
    SUMMER_PROFILES,
    default_options,
)
from .planning import normalize
from .scheduler import SplitScheduler

type SplitSchedulerConfigEntry = ConfigEntry[SplitScheduler]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Carte du tableau de bord et API websocket (une fois pour toutes)."""
    websocket.async_register(hass)
    version = (await async_get_integration(hass, DOMAIN)).version
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL_BASE, str(Path(__file__).parent / "frontend"), cache_headers=False
            )
        ]
    )
    # Chargée sur tous les tableaux de bord : la carte apparaît dans « Ajouter une carte ».
    add_extra_js_url(hass, f"{CARD_URL_BASE}/{CARD_FILENAME}?v={version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SplitSchedulerConfigEntry) -> bool:
    """Met en place l'intégration."""
    _add_summer_profiles(hass, entry)
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


def _add_summer_profiles(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ajoute une fois « Confort été » et « Eco été » aux installations existantes.

    Un profil du même nom (ou du même identifiant) déjà présent est conservé ;
    un profil supprimé ensuite par l'utilisateur n'est pas recréé.
    """
    migrations = list(entry.options.get(CONF_MIGRATIONS, []))
    if MIGRATION_SUMMER_PROFILES in migrations:
        return
    options = {**entry.options}
    profiles = {pid: dict(p) for pid, p in options.get(CONF_PROFILES, {}).items()}
    names = {normalize(p["name"]) for p in profiles.values()}
    next_pos = max((p.get(CONF_POS, -1) for p in profiles.values()), default=-1) + 1
    for pid in SUMMER_PROFILES:
        profile = dict(default_options()[CONF_PROFILES][pid])
        if pid in profiles or normalize(profile["name"]) in names:
            continue
        profile[CONF_POS] = next_pos
        next_pos += 1
        profiles[pid] = profile
    options[CONF_PROFILES] = profiles
    options[CONF_MIGRATIONS] = [*migrations, MIGRATION_SUMMER_PROFILES]
    hass.config_entries.async_update_entry(entry, options=options)
