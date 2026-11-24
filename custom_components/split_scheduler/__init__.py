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

from . import settings_api, websocket
from .const import (
    CARD_FILENAME,
    SETTINGS_CARD_FILENAME,
    CARD_URL_BASE,
    CONF_GROUPS,
    CONF_MIGRATIONS,
    CONF_POS,
    CONF_PROFILES,
    DOMAIN,
    CONF_CLIMATES,
    CONF_COMPRESSOR,
    CONF_COMPRESSOR_MAX,
    CONF_COMPRESSORS,
    CONF_HEAT_PUMPS,
    MIGRATION_HEAT_PUMPS,
    MIGRATION_REMOVE_PRESETS,
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
    settings_api.async_register(hass)
    version = (await async_get_integration(hass, DOMAIN)).version
    hass.data[f"{DOMAIN}_version"] = str(version)
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL_BASE, str(Path(__file__).parent / "frontend"), cache_headers=False
            )
        ]
    )
    # Chargée sur tous les tableaux de bord : la carte apparaît dans « Ajouter une carte ».
    add_extra_js_url(hass, f"{CARD_URL_BASE}/{CARD_FILENAME}?v={version}")
    add_extra_js_url(hass, f"{CARD_URL_BASE}/{SETTINGS_CARD_FILENAME}?v={version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SplitSchedulerConfigEntry) -> bool:
    """Met en place l'intégration."""
    _add_summer_profiles(hass, entry)
    _remove_presets(hass, entry)
    _create_heat_pumps(hass, entry)
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


def _remove_presets(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Retire une fois le préréglage (Normal / ECONO / Powerful) des profils existants."""
    migrations = list(entry.options.get(CONF_MIGRATIONS, []))
    if MIGRATION_REMOVE_PRESETS in migrations:
        return
    options = {**entry.options}
    options[CONF_PROFILES] = {
        pid: {k: v for k, v in p.items() if k != "preset_mode"}
        for pid, p in options.get(CONF_PROFILES, {}).items()
    }
    options[CONF_MIGRATIONS] = [*migrations, MIGRATION_REMOVE_PRESETS]
    hass.config_entries.async_update_entry(entry, options=options)


def _create_heat_pumps(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reprend une fois le capteur du compresseur réglé par groupe : une pompe à chaleur
    regroupant les splits de ces groupes (cas d'une seule unité extérieure ; à répartir
    ensuite en plusieurs pompes si besoin)."""
    migrations = list(entry.options.get(CONF_MIGRATIONS, []))
    if MIGRATION_HEAT_PUMPS in migrations:
        return
    options = {**entry.options}
    groups = {gid: dict(g) for gid, g in options.get(CONF_GROUPS, {}).items()}
    heat_pumps = dict(options.get(CONF_HEAT_PUMPS, {}))
    sensors: list[str] = []
    climates: list[str] = []
    maximum = None
    for group in groups.values():
        sensor = group.pop(CONF_COMPRESSOR, None)
        group_max = group.pop(CONF_COMPRESSOR_MAX, None)
        if not sensor:
            continue
        if sensor not in sensors:
            sensors.append(sensor)
        climates += [eid for eid in group.get(CONF_CLIMATES, []) if eid not in climates]
        maximum = maximum or group_max
    if sensors and not heat_pumps:
        pump = {"name": "Pompe à chaleur", CONF_CLIMATES: climates, CONF_COMPRESSORS: sensors}
        if maximum:
            pump[CONF_COMPRESSOR_MAX] = maximum
        heat_pumps["pac"] = pump
    options[CONF_GROUPS] = groups
    options[CONF_HEAT_PUMPS] = heat_pumps
    options[CONF_MIGRATIONS] = [*migrations, MIGRATION_HEAT_PUMPS]
    hass.config_entries.async_update_entry(entry, options=options)
