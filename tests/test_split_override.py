"""Dérogation d'un seul split : les autres splits du groupe suivent le programme."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.split_scheduler.const import DOMAIN, default_options, with_positions

PARIS = ZoneInfo("Europe/Paris")
SPLITS = ["climate.chambre_1", "climate.chambre_2", "climate.chambre_3"]
ATTRS = {"hvac_modes": ["off", "heat", "cool"], "temperature": 20, "min_temp": 16, "max_temp": 32,
         "target_temp_step": 0.5, "supported_features": 1}


async def _setup(hass, freezer, start):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    calls = {n: async_mock_service(hass, "climate", n) for n in ("set_hvac_mode", "set_temperature")}
    freezer.move_to(start)
    for eid in SPLITS:
        hass.states.async_set(eid, "heat", ATTRS)
    options = default_options()
    options["groups"] = {"chambres": {"name": "Chambres", "climates": SPLITS}}
    options["plannings"]["normal"]["programs"] = {
        "chambres": {str(d): [["06:00", "confort"], ["22:30", "eco"]] for d in range(7)}
    }
    options["plannings"]["vacances"]["programs"] = {
        "chambres": {str(d): [["00:00", "hors_gel"]] for d in range(7)}
    }
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, calls


async def _at(hass, freezer, when):
    freezer.move_to(when)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done()


def _overrides(hass):
    return hass.states.get("select.chambres_profil").attributes["derogations_splits"]


async def _remote(hass, freezer, eid, **attrs):
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(eid, "heat", {**ATTRS, **attrs})
    await hass.async_block_till_done()


async def test_only_changed_split_is_held(hass: HomeAssistant, freezer):
    entry, calls = await _setup(hass, freezer, datetime(2026, 11, 10, 21, 0, tzinfo=PARIS))
    scheduler = entry.runtime_data
    await _remote(hass, freezer, SPLITS[1], temperature=23)
    assert [o["entity_id"] for o in _overrides(hass)] == [SPLITS[1]]
    assert hass.states.get("select.chambres_profil").attributes["derogation"] is False

    # Reprise choisie à 23:30 : le créneau de 22:30 n'est envoyé qu'aux deux autres
    await scheduler.async_shift_split("chambres", SPLITS[1], 60)
    calls["set_temperature"].clear()
    await _at(hass, freezer, datetime(2026, 11, 10, 22, 30, tzinfo=PARIS))
    assert [c.data["entity_id"] for c in calls["set_temperature"]] == [SPLITS[0], SPLITS[2]]
    assert [o["entity_id"] for o in _overrides(hass)] == [SPLITS[1]]

    # Redémarrage : la dérogation du split est conservée, puis il reprend à 23:30
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert [o["entity_id"] for o in _overrides(hass)] == [SPLITS[1]]
    calls["set_temperature"].clear()
    await _at(hass, freezer, datetime(2026, 11, 10, 23, 30, tzinfo=PARIS))
    assert [(c.data["entity_id"], c.data["temperature"]) for c in calls["set_temperature"]] == [
        (SPLITS[1], 18.0)
    ]
    assert _overrides(hass) == []
    assert hass.states.get("sensor.chambres_statut").state == "scheduled"


async def test_default_resume_is_next_slot_for_that_split(hass: HomeAssistant, freezer):
    _, calls = await _setup(hass, freezer, datetime(2026, 11, 10, 21, 0, tzinfo=PARIS))
    await _remote(hass, freezer, SPLITS[0], temperature=23)
    calls["set_temperature"].clear()
    await _at(hass, freezer, datetime(2026, 11, 10, 22, 30, tzinfo=PARIS))
    assert sorted(c.data["entity_id"] for c in calls["set_temperature"]) == SPLITS
    assert _overrides(hass) == []


async def test_card_setting_and_planning_change_clear_split_overrides(hass: HomeAssistant, freezer):
    entry, calls = await _setup(hass, freezer, datetime(2026, 11, 10, 21, 0, tzinfo=PARIS))
    scheduler = entry.runtime_data
    await _remote(hass, freezer, SPLITS[0], temperature=23)
    calls["set_temperature"].clear()
    await scheduler.async_manual_settings("chambres", {"temperature": 21})
    assert _overrides(hass) == []
    assert hass.states.get("select.chambres_profil").attributes["derogation"] is True
    assert len(calls["set_temperature"]) == 3   # tous les splits

    await scheduler.async_resume("chambres")
    await _remote(hass, freezer, SPLITS[2], temperature=24)
    assert [o["entity_id"] for o in _overrides(hass)] == [SPLITS[2]]
    await hass.services.async_call("select", "select_option",
                                   {"entity_id": "select.chambres_planning", "option": "Vacances"},
                                   blocking=True)
    assert _overrides(hass) == []
