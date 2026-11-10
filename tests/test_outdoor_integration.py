"""Consigne adaptée à la température extérieure dans Home Assistant."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.split_scheduler.const import DOMAIN, default_options, with_positions

PARIS = ZoneInfo("Europe/Paris")
SPLIT = "climate.salon"
OUT = "sensor.exterieur"
ATTRS = {"hvac_modes": ["off", "heat", "cool"], "temperature": 24, "min_temp": 16,
         "max_temp": 32, "target_temp_step": 0.5, "supported_features": 1}


def _temps(calls):
    return [c.data["temperature"] for c in calls]


async def _setup(hass, freezer, start, program, outdoor="39"):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    calls = async_mock_service(hass, "climate", "set_temperature")
    async_mock_service(hass, "climate", "set_hvac_mode")
    freezer.move_to(start - timedelta(hours=1))
    hass.states.async_set(OUT, outdoor, {"unit_of_measurement": "°C"})
    freezer.move_to(start)
    hass.states.async_set(SPLIT, "cool", ATTRS)
    options = default_options()
    options["settings"] = {"outdoor_sensor": OUT}
    options["groups"] = {"salon": {"name": "Salon", "climates": [SPLIT]}}
    options["plannings"]["normal"]["programs"] = {"salon": {str(d): program for d in range(7)}}
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


async def test_heatwave_adapts_then_returns(hass: HomeAssistant, freezer):
    day = datetime(2026, 7, 15, 12, 0, tzinfo=PARIS)
    _, calls = await _setup(hass, freezer, day, [["06:00", "confort_ete"], ["22:00", "eco_ete"]])
    assert _temps(calls) == [29]                      # 39 °C dehors, écart 10 °C
    attrs = _attrs(hass)
    assert attrs["consigne_profil"] == 26 and attrs["consigne_appliquee"] == 29
    assert attrs["adaptation_exterieure"] is True and attrs["temperature_exterieure"] == 39

    # Le split confirme 29 °C : pas de fausse dérogation
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(SPLIT, "cool", {**ATTRS, "temperature": 29})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_statut").state == "scheduled"

    # L'extérieur baisse à 30 °C : rien avant 30 minutes depuis le dernier envoi
    await _at(hass, freezer, day + timedelta(minutes=10))
    hass.states.async_set(OUT, "30", {"unit_of_measurement": "°C"})
    calls.clear()
    await _at(hass, freezer, day + timedelta(minutes=25))
    assert calls == []
    # À 12:40, moyenne sur 1 h = 34,5 °C -> consigne 26 °C (écart respecté)
    await _at(hass, freezer, day + timedelta(minutes=40))
    assert _temps(calls) == [26]
    assert _attrs(hass)["adaptation_exterieure"] is False


async def test_no_adaptation_shortly_before_profile_change(hass: HomeAssistant, freezer):
    day = datetime(2026, 7, 15, 12, 0, tzinfo=PARIS)
    _, calls = await _setup(hass, freezer, day, [["06:00", "confort_ete"], ["13:20", "eco_ete"]], "30")
    assert _temps(calls) == [26]
    hass.states.async_set(OUT, "41", {"unit_of_measurement": "°C"})
    calls.clear()
    # 12:35 : 25 min à 30 °C et 35 min à 41 °C -> 36,4 °C -> 26,4 arrondi à 26,5
    await _at(hass, freezer, day + timedelta(minutes=35))
    assert _temps(calls) == [26.5]
    calls.clear()
    await _at(hass, freezer, day + timedelta(minutes=70))   # 13:10 : changement à 13:20
    assert calls == []


async def test_unavailable_outdoor_returns_to_profile(hass: HomeAssistant, freezer):
    day = datetime(2026, 7, 15, 12, 0, tzinfo=PARIS)
    _, calls = await _setup(hass, freezer, day, [["06:00", "confort_ete"]])
    assert _temps(calls) == [29]
    hass.states.async_set(OUT, "unavailable", {})
    calls.clear()
    await _at(hass, freezer, day + timedelta(minutes=40))   # encore 40 min de valeurs valables
    assert calls == []
    await _at(hass, freezer, day + timedelta(minutes=70))   # plus d'une heure sans valeur
    assert _temps(calls) == [26]


async def test_hand_setting_stops_adaptation(hass: HomeAssistant, freezer):
    day = datetime(2026, 7, 15, 12, 0, tzinfo=PARIS)
    entry, calls = await _setup(hass, freezer, day, [["06:00", "confort_ete"]])
    await entry.runtime_data.async_manual_settings("salon", {"temperature": 25})
    hass.states.async_set(OUT, "20", {"unit_of_measurement": "°C"})
    calls.clear()
    await _at(hass, freezer, day + timedelta(hours=2))
    assert calls == []
    assert _attrs(hass)["adaptation_exterieure"] is False


async def test_summer_profiles_added_once(hass: HomeAssistant):
    hass.config.language = "fr"
    options = default_options()
    for pid in ("confort_ete", "eco_ete"):
        options["profiles"].pop(pid)
    options.pop("migrations")
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    profiles = entry.options["profiles"]
    assert profiles["confort_ete"]["outdoor_max_delta"] == 10.0
    assert profiles["eco_ete"]["temperature"] == 28.0
    assert profiles["eco_ete"]["pos"] > profiles["manuel"]["pos"]
    # Supprimé par l'utilisateur : pas recréé
    trimmed = {**entry.options, "profiles": {k: v for k, v in profiles.items() if k != "eco_ete"}}
    hass.config_entries.async_update_entry(entry, options=trimmed)
    await hass.async_block_till_done()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert "eco_ete" not in entry.options["profiles"]


async def test_settings_step_detects_faikout_outside(hass: HomeAssistant):
    hass.config.language = "fr"
    source = MockConfigEntry(domain="mqtt")
    source.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=source.entry_id, identifiers={("mqtt", "faikout")}, name="Split salon"
    )
    reg = er.async_get(hass)
    reg.async_get_or_create("climate", "mqtt", "c", device_id=device.id, suggested_object_id="salon")
    reg.async_get_or_create("sensor", "mqtt", "o", device_id=device.id,
                            suggested_object_id="salon_outside", original_name="Outside")
    hass.states.async_set(SPLIT, "cool", ATTRS)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    entry = (await hass.config_entries.flow.async_configure(result["flow_id"], {}))["result"]
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    await flow.async_configure(fid, {"next_step_id": "groups"})
    await flow.async_configure(fid, {"next_step_id": "group_add"})
    await flow.async_configure(fid, {"name": "Salon", "climates": [SPLIT]})
    await flow.async_configure(fid, {"next_step_id": "init"})
    result = await flow.async_configure(fid, {"next_step_id": "settings"})
    key = next(k for k in result["data_schema"].schema if k == "outdoor_sensor")
    assert key.description["suggested_value"] == "sensor.salon_outside"
    await flow.async_configure(fid, {"outdoor_sensor": "sensor.salon_outside"})
    await flow.async_configure(fid, {"next_step_id": "save"})
    await hass.async_block_till_done()
    assert entry.options["settings"]["outdoor_sensor"] == "sensor.salon_outside"


async def test_profile_form_has_outdoor_gap(hass: HomeAssistant):
    hass.config.language = "fr"
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    entry = (await hass.config_entries.flow.async_configure(result["flow_id"], {}))["result"]
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    await flow.async_configure(fid, {"next_step_id": "profiles"})
    await flow.async_configure(fid, {"next_step_id": "profile_edit_pick"})
    result = await flow.async_configure(fid, {"profile": "confort_ete"})
    key = next(k for k in result["data_schema"].schema if k == "outdoor_max_delta")
    assert key.description["suggested_value"] == 10.0
    await flow.async_configure(
        fid, {"name": "Confort été", "hvac_mode": "cool", "temperature": 25, "outdoor_max_delta": 8}
    )
    await flow.async_configure(fid, {"next_step_id": "init"})
    await flow.async_configure(fid, {"next_step_id": "save"})
    await hass.async_block_till_done()
    profile = entry.options["profiles"]["confort_ete"]
    assert profile["outdoor_max_delta"] == 8.0 and profile["temperature"] == 25.0
