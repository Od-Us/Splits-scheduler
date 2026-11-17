"""Pompes à chaleur : compresseur partagé, split prioritaire, conflits de mode, consommation."""

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
from custom_components.split_scheduler.heatpump import (
    EnergyToday,
    find_conflicts,
    program_conflicts,
    shared_value,
)

PARIS = ZoneInfo("Europe/Paris")
ATTRS = {"hvac_modes": ["off", "heat", "cool", "dry", "fan_only"], "temperature": 20,
         "min_temp": 16, "max_temp": 32, "target_temp_step": 0.5, "supported_features": 1}
A, B, C = "climate.split_a", "climate.split_b", "climate.split_c"
CA, CB = "sensor.split_a_compressor", "sensor.split_b_compressor"


def test_conflicts_with_and_without_priority():
    assert find_conflicts({A: "heat", B: "cool", C: "fan_only"}, A) == {B: A}
    assert find_conflicts({A: "cool", B: "heat", C: "dry"}, A) == {B: A}   # déshumidification = froid
    assert find_conflicts({A: "off", B: "heat", C: "cool"}, A) == {B: None, C: None}
    assert find_conflicts({A: "heat", B: "heat", C: "off"}, None) == {}
    assert find_conflicts({A: "heat", B: "cool"}, None) == {A: None, B: None}


def test_shared_value_is_median():
    assert shared_value([40, 42, 0]) == 40
    assert shared_value([]) is None


def test_program_conflicts():
    side = {"chaud": "heat", "froid": "cool", "arret": None}.get
    own = {"0": [["06:00", "chaud"], ["22:00", "arret"]]}
    other = {"0": [["07:00", "froid"], ["09:00", "arret"]]}
    assert program_conflicts(own, other, side) == [(420, 540, "heat", "cool")]
    assert program_conflicts(own, {}, side) == []


def test_energy_counter_and_power():
    energy = EnergyToday()
    day = datetime(2026, 11, 10, 8, 0, tzinfo=PARIS)
    assert energy.from_counter(day, 1000.0) == 0.0
    assert energy.from_counter(day + timedelta(hours=2), 1003.5) == 3.5
    assert energy.from_counter(day + timedelta(days=1), 1004.0) == 0.0     # minuit : remise à zéro
    power = EnergyToday()
    power.from_power(day, 1000)
    assert power.from_power(day + timedelta(minutes=30), 500) == 0.5        # 1 kW pendant 30 min
    assert power.from_power(day + timedelta(minutes=90), 0) == 1.0


async def _setup(hass, freezer, pump_extra=None, groups=None):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    for svc in ("set_hvac_mode", "set_temperature"):
        async_mock_service(hass, "climate", svc)
    freezer.move_to(datetime(2026, 11, 10, 12, 0, tzinfo=PARIS))
    for eid in (A, B, C):
        hass.states.async_set(eid, "heat", ATTRS)
    hass.states.async_set(CA, "40", {"unit_of_measurement": "Hz"})
    hass.states.async_set(CB, "44", {"unit_of_measurement": "Hz"})
    options = default_options()
    options["groups"] = groups or {
        "sejour": {"name": "Séjour", "climates": [A]},
        "chambres": {"name": "Chambres", "climates": [B, C]},
    }
    options["heat_pumps"] = {
        "pac": {"name": "PAC", "climates": [A, B], "priority": A, "compressors": [CA, CB],
                "compressor_max": 80, **(pump_extra or {})},
    }
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_shared_compressor_and_conflicts(hass: HomeAssistant, freezer):
    entry = await _setup(hass, freezer)
    scheduler = entry.runtime_data
    assert hass.states.get("sensor.pac_compresseur").state == "42.0"
    assert hass.states.get("sensor.pac_charge_du_compresseur").state == "52"   # 42 / 80
    assert hass.states.get("sensor.pac_mode").state == "heat"
    # Le groupe Chambres a un split sans pompe (C) : sa pompe principale reste la PAC
    assert scheduler.group_pumps["chambres"] == ["pac"]
    assert hass.states.get("sensor.chambres_charge_du_compresseur").state == "52"

    # B passe en froid alors que le split prioritaire A chauffe : conflit signalé sur B
    hass.states.async_set(B, "cool", ATTRS)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.pac_mode").state == "conflict"
    conflicts = hass.states.get("select.chambres_profil").attributes["conflits_mode"]
    assert conflicts == [{"entity_id": B, "pompe": "PAC", "prioritaire": A}]
    assert hass.states.get("select.sejour_profil").attributes["conflits_mode"] == []
    # C (sans pompe) en froid : aucun conflit
    hass.states.async_set(B, "heat", ATTRS)
    hass.states.async_set(C, "cool", ATTRS)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.pac_mode").state == "heat"


async def test_energy_from_power(hass: HomeAssistant, freezer):
    power = "sensor.pac_puissance"
    hass.states.async_set(power, "1200", {"unit_of_measurement": "W"})
    await _setup(hass, freezer, {"power_sensor": power})
    energy = "sensor.pac_consommation_du_jour"
    assert hass.states.get(energy).state == "0.0"
    for _ in range(30):   # 30 min à 1,2 kW
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass, dt_util.utcnow())
        await hass.async_block_till_done()
    assert float(hass.states.get(energy).state) == 0.6


async def test_energy_from_counter(hass: HomeAssistant, freezer):
    meter = "sensor.pac_energie"
    hass.states.async_set(meter, "1500.0", {"unit_of_measurement": "kWh"})
    await _setup(hass, freezer, {"energy_sensor": meter})
    hass.states.async_set(meter, "1502.25", {"unit_of_measurement": "kWh"})
    await hass.async_block_till_done()
    assert float(hass.states.get("sensor.pac_consommation_du_jour").state) == 2.25


async def test_migration_of_group_compressors(hass: HomeAssistant, freezer):
    hass.config.language = "fr"
    freezer.move_to(datetime(2026, 11, 10, 12, 0, tzinfo=PARIS))
    for eid in (A, B):
        hass.states.async_set(eid, "heat", ATTRS)
    options = default_options()
    options["migrations"] = ["summer_profiles", "remove_presets"]
    options.pop("heat_pumps")
    options["groups"] = {
        "sejour": {"name": "Séjour", "climates": [A], "compressor": CA, "compressor_max": 70},
        "chambres": {"name": "Chambres", "climates": [B], "compressor": CB},
    }
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    pumps = entry.options["heat_pumps"]
    assert list(pumps.values())[0]["climates"] == [A, B]
    assert list(pumps.values())[0]["compressors"] == [CA, CB]
    assert list(pumps.values())[0]["compressor_max"] == 70
    assert all("compressor" not in g for g in entry.options["groups"].values())


async def test_heat_pump_form_and_program_warning(hass: HomeAssistant, freezer):
    entry = await _setup(hass, freezer)
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    result = await flow.async_configure(fid, {"next_step_id": "heat_pumps"})
    result = await flow.async_configure(fid, {"next_step_id": "heat_pump_add"})
    result = await flow.async_configure(fid, {"name": "PAC 2", "climates": [B, C]})
    assert result["errors"] == {"climates": "climate_other_pump"}
    result = await flow.async_configure(fid, {"name": "PAC 2", "climates": [C], "priority": A})
    assert result["errors"] == {"priority": "priority_not_member"}
    await flow.async_configure(fid, {"name": "PAC 2", "climates": [C], "model": "Unité 2"})
    await flow.async_configure(fid, {"next_step_id": "init"})

    # Programme : Séjour (A, prioritaire) en froid le lundi 14:00–16:00, Chambres en chauffage
    opts = flow._progress[fid].opts
    opts["profiles"]["froid"] = {"name": "Froid", "hvac_mode": "cool", "temperature": 25.0}
    opts["plannings"]["normal"]["allowed"] = [*opts["plannings"]["normal"].get("allowed", []), "froid"]
    programs = opts["plannings"]["normal"]["programs"]
    programs["sejour"] = {"0": [["06:00", "confort"], ["14:00", "froid"], ["16:00", "confort"]]}
    programs["chambres"] = {"0": [["06:00", "confort"]]}
    result = await flow.async_configure(fid, {"next_step_id": "program_pick"})
    result = await flow.async_configure(fid, {"planning": "normal", "group": "chambres"})
    warnings = result["description_placeholders"]["warnings"]
    assert "Lun 14:00–16:00" in warnings and "chauffage ici, froid" in warnings
    # Le programme du split prioritaire lui-même n'a pas d'avertissement
    await flow.async_configure(fid, {"next_step_id": "init"})
    await flow.async_configure(fid, {"next_step_id": "program_pick"})
    result = await flow.async_configure(fid, {"planning": "normal", "group": "sejour"})
    assert result["description_placeholders"]["warnings"] == ""
