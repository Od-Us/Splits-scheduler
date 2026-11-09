"""Tests de bout en bout dans Home Assistant (splits simulés)."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.split_scheduler.const import DOMAIN, default_options

PARIS = ZoneInfo("Europe/Paris")
SALON = ["climate.salon_1", "climate.salon_2"]
ATTRS = {
    "hvac_modes": ["off", "heat", "cool", "dry", "fan_only", "auto"],
    "fan_modes": ["auto", "low", "medium", "high"],
    "swing_modes": ["off", "vertical", "horizontal", "both"],
    "min_temp": 10,
    "max_temp": 30,
    "temperature": 19,
    "fan_mode": "auto",
    "swing_mode": "off",
    "supported_features": 1 | 8 | 32,
}


def _options():
    options = default_options()
    options["profiles"]["boost"]["fan_mode"] = "high"
    options["profiles"]["hors_gel"]["temperature"] = 8.0  # sous le minimum du split
    options["groups"] = {"salon": {"name": "Salon", "climates": SALON}}
    options["plannings"]["normal"]["programs"] = {
        "salon": {str(d): [["06:30", "confort"], ["22:00", "eco"]] for d in range(7)}
    }
    options["plannings"]["absence"]["programs"] = {"salon": {"0": [["00:00", "hors_gel"]]}}
    return options


@pytest.fixture
async def calls(hass: HomeAssistant):
    await hass.config.async_set_time_zone("Europe/Paris")
    return {
        name: async_mock_service(hass, "climate", name)
        for name in ("set_hvac_mode", "set_temperature", "set_fan_mode", "set_swing_mode")
    }


def _set_climates(hass, state="off", **extra):
    for eid in SALON:
        hass.states.async_set(eid, state, {**ATTRS, **extra})


async def _setup(hass, freezer, when: datetime) -> MockConfigEntry:
    freezer.move_to(when)
    entry = MockConfigEntry(domain=DOMAIN, title="Programmation des splits", options=_options())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _clear(calls):
    for c in calls.values():
        c.clear()


async def test_applies_current_slot_then_next(hass, calls, freezer: FrozenDateTimeFactory):
    _set_climates(hass)
    await _setup(hass, freezer, datetime(2026, 11, 9, 12, 0, tzinfo=PARIS))

    assert hass.states.get("select.salon_profile").state == "Confort"
    assert hass.states.get("select.salon_planning").state == "Normal"
    assert hass.states.get("sensor.salon_status").state == "scheduled"
    assert [c.data for c in calls["set_hvac_mode"]] == [
        {"entity_id": eid, "hvac_mode": "heat"} for eid in SALON
    ]
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [20.0, 20.0]
    nxt = hass.states.get("sensor.salon_next_change")
    assert dt_util.parse_datetime(nxt.state) == datetime(2026, 11, 9, 22, tzinfo=PARIS)
    assert nxt.attributes["prochain_profil"] == "Eco"

    # Les splits suivent ; à 22:00 on passe en Eco
    _set_climates(hass, "heat", temperature=20)
    _clear(calls)
    freezer.move_to(datetime(2026, 11, 9, 22, 0, tzinfo=PARIS))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("select.salon_profile").state == "Eco"
    assert calls["set_hvac_mode"] == []  # déjà en chauffage
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [18.0, 18.0]


async def test_manual_change_kept_until_next_slot(hass, calls, freezer):
    _set_climates(hass, "heat", temperature=20)
    await _setup(hass, freezer, datetime(2026, 11, 9, 12, 0, tzinfo=PARIS))

    # Changement à la télécommande 10 minutes plus tard
    freezer.tick(timedelta(minutes=10))
    hass.states.async_set(SALON[0], "heat", {**ATTRS, "temperature": 23})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_status").state == "override"
    assert hass.states.get("select.salon_profile").attributes["derogation"] is True

    # Rien n'est réimposé avant 22:00…
    _clear(calls)
    freezer.move_to(datetime(2026, 11, 9, 21, 59, tzinfo=PARIS))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert calls["set_temperature"] == []

    # … puis le créneau suivant reprend la main
    freezer.move_to(datetime(2026, 11, 9, 22, 0, tzinfo=PARIS))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_status").state == "scheduled"
    assert len(calls["set_temperature"]) == 2


async def test_own_commands_are_not_an_override(hass, calls, freezer):
    _set_climates(hass)
    await _setup(hass, freezer, datetime(2026, 11, 9, 12, 0, tzinfo=PARIS))
    _set_climates(hass, "heat", temperature=20)  # retour MQTT de nos commandes
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_status").state == "scheduled"


async def test_select_profile_and_resume(hass, calls, freezer):
    _set_climates(hass, "heat", temperature=20)
    await _setup(hass, freezer, datetime(2026, 11, 9, 12, 0, tzinfo=PARIS))
    _clear(calls)

    await hass.services.async_call(
        "select", "select_option",
        {"entity_id": "select.salon_profile", "option": "Boost"}, blocking=True,
    )
    assert hass.states.get("select.salon_profile").state == "Boost"
    assert hass.states.get("sensor.salon_status").state == "override"
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [23.0, 23.0]
    assert [c.data["fan_mode"] for c in calls["set_fan_mode"]] == ["high", "high"]

    await hass.services.async_call(
        "button", "press", {"entity_id": "button.salon_resume_schedule"},
        blocking=True,
    )
    assert hass.states.get("select.salon_profile").state == "Confort"
    assert hass.states.get("sensor.salon_status").state == "scheduled"


async def test_change_planning_globally(hass, calls, freezer):
    _set_climates(hass, "heat", temperature=20)
    await _setup(hass, freezer, datetime(2026, 11, 11, 12, 0, tzinfo=PARIS))
    _clear(calls)

    await hass.services.async_call(
        "select", "select_option",
        {"entity_id": "select.programmation_des_splits_planning_of_all_groups",
         "option": "Absence prolongée"},
        blocking=True,
    )
    assert hass.states.get("select.salon_planning").state == "Absence prolongée"
    assert hass.states.get("select.salon_profile").state == "Hors gel"
    # 8 °C demandé, borné au minimum du split
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [10, 10]
    # Créneau unique du lundi : prochain changement lundi prochain
    nxt = hass.states.get("sensor.salon_next_change")
    assert dt_util.parse_datetime(nxt.state) == datetime(2026, 11, 16, 0, tzinfo=PARIS)

    # Le split reste à 10 °C (borné) : ce n'est pas une dérogation
    freezer.tick(timedelta(minutes=5))
    _set_climates(hass, "heat", temperature=10)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_status").state == "scheduled"


async def test_disable_programming(hass, calls, freezer):
    _set_climates(hass, "heat", temperature=20)
    await _setup(hass, freezer, datetime(2026, 11, 9, 12, 0, tzinfo=PARIS))
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.salon_scheduling"}, blocking=True
    )
    assert hass.states.get("sensor.salon_status").state == "disabled"
    assert hass.states.get("sensor.salon_next_change").state == "unknown"
    _clear(calls)
    freezer.move_to(datetime(2026, 11, 9, 22, 0, tzinfo=PARIS))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert calls["set_temperature"] == []


async def test_unavailable_split_receives_profile_when_back(hass, calls, freezer):
    hass.states.async_set(SALON[0], "unavailable", {})
    hass.states.async_set(SALON[1], "heat", {**ATTRS, "temperature": 20})
    await _setup(hass, freezer, datetime(2026, 11, 9, 23, 0, tzinfo=PARIS))
    assert [c.data["entity_id"] for c in calls["set_temperature"]] == [SALON[1]]

    hass.states.async_set(SALON[0], "heat", {**ATTRS, "temperature": 21})
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in calls["set_temperature"]][-1] == SALON[0]


async def test_restart_keeps_override_but_catches_up(hass, calls, freezer):
    _set_climates(hass, "heat", temperature=20)
    entry = await _setup(hass, freezer, datetime(2026, 11, 9, 12, 0, tzinfo=PARIS))
    freezer.tick(timedelta(minutes=10))
    hass.states.async_set(SALON[0], "heat", {**ATTRS, "temperature": 23})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_status").state == "override"
    _clear(calls)

    # Redémarrage dans le même créneau : la dérogation est conservée
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert calls["set_temperature"] == []
    assert hass.states.get("sensor.salon_status").state == "override"

    # Arrêt pendant le changement de 22:00 : rattrapé au redémarrage
    await hass.config_entries.async_unload(entry.entry_id)
    freezer.move_to(datetime(2026, 11, 9, 23, 30, tzinfo=PARIS))
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [18.0, 18.0]
    assert hass.states.get("select.salon_profile").state == "Eco"
    assert hass.states.get("sensor.salon_status").state == "scheduled"
