"""Préréglage du split (ECONO / Powerful) et durée des dérogations."""

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
SPLIT = "climate.salon"
ATTRS = {"hvac_modes": ["off", "heat"], "temperature": 15, "min_temp": 16, "max_temp": 32,
         "target_temp_step": 0.5, "supported_features": 17,
         "preset_modes": ["none", "eco", "boost", "home"], "preset_mode": "home"}


async def _setup(hass, freezer, start):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    calls = {n: async_mock_service(hass, "climate", n)
             for n in ("set_hvac_mode", "set_temperature", "set_preset_mode")}
    freezer.move_to(start)
    hass.states.async_set(SPLIT, "heat", ATTRS)
    options = default_options()
    options["profiles"]["eco_absence"]["preset_mode"] = "eco"
    options["profiles"]["boost"]["preset_mode"] = "boost"
    options["groups"] = {"salon": {"name": "Salon", "climates": [SPLIT]}}
    options["plannings"]["normal"]["programs"] = {
        "salon": {str(d): [["06:00", "confort"], ["08:30", "eco_absence"], ["22:30", "eco"]] for d in range(7)}
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


def _attrs(hass):
    return hass.states.get("select.salon_profil").attributes


async def test_preset_sent_and_boost_end_is_not_override(hass: HomeAssistant, freezer):
    day = datetime(2026, 11, 10, 12, 0, tzinfo=PARIS)
    _, calls = await _setup(hass, freezer, day)
    assert [c.data["preset_mode"] for c in calls["set_preset_mode"]] == ["eco"]   # Eco absence -> ECONO
    await hass.services.async_call("select", "select_option",
                                   {"entity_id": "select.salon_profil", "option": "Boost"}, blocking=True)
    assert [c.data["preset_mode"] for c in calls["set_preset_mode"]][-1] == "boost"
    await hass.services.async_call("button", "press", {"entity_id": "button.salon_reprendre_la_programmation"}, blocking=True)
    # Le split revient seul de Powerful : pas de dérogation
    freezer.tick(timedelta(minutes=25))
    hass.states.async_set(SPLIT, "heat", {**ATTRS, "temperature": 17, "preset_mode": "eco"})
    await hass.async_block_till_done()
    hass.states.async_set(SPLIT, "heat", {**ATTRS, "temperature": 17, "preset_mode": "home"})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_statut").state == "override"  # eco attendu, home reçu


async def test_override_duration_wins_over_slots(hass: HomeAssistant, freezer):
    day = datetime(2026, 11, 10, 21, 30, tzinfo=PARIS)
    entry, calls = await _setup(hass, freezer, day)
    scheduler = entry.runtime_data
    await hass.services.async_call("select", "select_option",
                                   {"entity_id": "select.salon_profil", "option": "Boost"}, blocking=True)
    attrs = _attrs(hass)
    assert attrs["reprise"] == datetime(2026, 11, 10, 22, 30, tzinfo=PARIS).isoformat()  # par défaut : créneau
    assert attrs["reprise_choisie"] is False and attrs["creneau_ignore"] is None

    # +30 deux fois : reprise à 23:30, le créneau de 22:30 est ignoré
    await scheduler.async_shift_override("salon", 30)
    until = await scheduler.async_shift_override("salon", 30)
    assert dt_util.as_local(until) == datetime(2026, 11, 10, 23, 30, tzinfo=PARIS)
    attrs = _attrs(hass)
    assert attrs["creneau_ignore"]["profil"] == "Eco" and attrs["reprise_profil"] == "Eco"
    assert dt_util.parse_datetime(hass.states.get("sensor.salon_prochain_changement").state) == until

    # Redémarrage pendant la dérogation : l'heure de reprise est conservée
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    calls["set_temperature"].clear()
    await _at(hass, freezer, datetime(2026, 11, 10, 22, 30, tzinfo=PARIS))
    assert calls["set_temperature"] == [] and _attrs(hass)["derogation"] is True
    await _at(hass, freezer, datetime(2026, 11, 10, 23, 30, tzinfo=PARIS))
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [18.0]   # Eco
    assert _attrs(hass)["derogation"] is False and _attrs(hass)["reprise"] is None


async def test_shift_limits_and_remote_default(hass: HomeAssistant, freezer):
    day = datetime(2026, 11, 10, 21, 30, tzinfo=PARIS)
    entry, _ = await _setup(hass, freezer, day)
    scheduler = entry.runtime_data
    assert await scheduler.async_shift_override("salon", 30) is None    # pas de dérogation
    # Groupe d'un seul split : la télécommande met tout le groupe en dérogation
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(SPLIT, "heat", {**ATTRS, "temperature": 23})
    await hass.async_block_till_done()
    attrs = _attrs(hass)
    assert attrs["derogation"] is True and attrs["derogations_splits"] == []
    assert attrs["reprise"] == datetime(2026, 11, 10, 22, 30, tzinfo=PARIS).isoformat()
    assert float(hass.states.get("sensor.salon_consigne").state) == 23.0  # consigne du groupe = celle du split
    # Un nouveau changement à la télécommande est suivi
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(SPLIT, "heat", {**ATTRS, "temperature": 22})
    await hass.async_block_till_done()
    assert float(hass.states.get("sensor.salon_consigne").state) == 22.0
    # -30 trois fois : jamais moins de 30 min à partir de maintenant
    for _ in range(3):
        until = await scheduler.async_shift_override("salon", -30)
    assert until == dt_util.utcnow() + timedelta(minutes=30)
    # +30 x 60 : jamais plus de 24 h
    for _ in range(60):
        until = await scheduler.async_shift_override("salon", 30)
    assert until == dt_util.utcnow() + timedelta(hours=24)
    # Reprendre maintenant efface la reprise choisie
    await hass.services.async_call("button", "press", {"entity_id": "button.salon_reprendre_la_programmation"}, blocking=True)
    assert _attrs(hass)["derogation"] is False and _attrs(hass)["reprise_choisie"] is False


def test_powerful_ending_by_itself_is_not_a_deviation():
    from homeassistant.core import State

    from custom_components.split_scheduler.scheduler import _deviates

    profile = {"hvac_mode": "heat", "temperature": 23.0, "preset_mode": "boost"}
    back_to_home = State(SPLIT, "heat", {**ATTRS, "temperature": 23, "preset_mode": "home"})
    assert _deviates(back_to_home, profile) is False
    wrong_preset = State(SPLIT, "heat", {**ATTRS, "temperature": 23, "preset_mode": "eco"})
    assert _deviates(wrong_preset, {**profile, "preset_mode": "home"}) is True
