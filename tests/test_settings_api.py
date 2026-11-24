"""API de la carte de réglages : lecture, enregistrement, contrôles et droits."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from homeassistant.core import HomeAssistant

from custom_components.split_scheduler.const import DOMAIN, default_options, with_positions
from custom_components.split_scheduler.settings_api import validate_program

A = "climate.sejour"
ATTRS = {"hvac_modes": ["off", "heat", "cool"], "temperature": 20, "min_temp": 16, "max_temp": 32,
         "target_temp_step": 0.5, "supported_features": 1}


def test_validate_program_sorts_and_refuses():
    assert validate_program({"0": [["08:00", "eco"], ["06:30", "confort"]], "1": []}, ["eco", "confort"]) == {
        "0": [["06:30", "confort"], ["08:00", "eco"]]
    }
    for bad, msg in (({"7": [["06:00", "eco"]]}, "jour"), ({"0": [["25:00", "eco"]]}, "heure"),
                     ({"0": [["06:00", "boost"]]}, "non autorisé"), ({"0": [["06:00", "eco"], ["06:00", "eco"]]}, "deux lignes")):
        with pytest.raises(ValueError, match=msg):
            validate_program(bad, ["eco", "confort"])


async def _setup(hass, freezer):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    for n in ("set_hvac_mode", "set_temperature"):
        async_mock_service(hass, "climate", n)
    hass.states.async_set(A, "heat", ATTRS)
    options = default_options()
    options["groups"] = {"g": {"name": "Séjour", "climates": [A]}}
    options["plannings"]["vacances"]["allowed_profiles"] = ["hors_gel", "arret"]
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_get_and_save(hass: HomeAssistant, freezer, hass_ws_client):
    entry = await _setup(hass, freezer)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "split_scheduler/config/get"})
    cfg = (await client.receive_json())["result"]
    assert cfg["admin"] is True and cfg["groups"][0]["names"] == {A: "sejour"}
    assert {p["id"] for p in cfg["plannings"]} == {"normal", "vacances", "absence"}
    vacances = next(p for p in cfg["plannings"] if p["id"] == "vacances")
    assert vacances["allowed"] == ["hors_gel", "arret"]

    program = {"0": [["17:00", "confort"], ["06:30", "confort"], ["22:00", "eco"]]}
    await client.send_json({"id": 2, "type": "split_scheduler/config/save",
                            "programs": {"normal": {"g": program}},
                            "settings": {"outdoor_sensor": "sensor.dehors", "always_quiet": True}})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    assert entry.options["plannings"]["normal"]["programs"]["g"]["0"][0] == ["06:30", "confort"]
    assert entry.options["settings"]["outdoor_sensor"] == "sensor.dehors"
    assert entry.options["settings"]["always_quiet"] is True

    # Profil non autorisé dans le planning : refusé, rien n'est changé
    await client.send_json({"id": 3, "type": "split_scheduler/config/save",
                            "programs": {"vacances": {"g": {"0": [["08:00", "confort"]]}}}})
    reply = await client.receive_json()
    assert not reply["success"] and "non autorisé" in reply["error"]["message"]
    assert "g" not in entry.options["plannings"]["vacances"].get("programs", {})


async def test_save_requires_admin(hass: HomeAssistant, freezer, hass_ws_client, hass_read_only_access_token):
    await _setup(hass, freezer)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json({"id": 1, "type": "split_scheduler/config/get"})
    assert (await client.receive_json())["result"]["admin"] is False
    await client.send_json({"id": 2, "type": "split_scheduler/config/save", "programs": {}})
    reply = await client.receive_json()
    assert not reply["success"] and reply["error"]["code"] == "unauthorized"


async def test_save_collections(hass: HomeAssistant, freezer, hass_ws_client):
    entry = await _setup(hass, freezer)
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "split_scheduler/config/get"})
    cfg = (await client.receive_json())["result"]
    assert "hvac_mode" in cfg["modes"] and cfg["names"] == {A: "sejour"}
    profiles = [{k: v for k, v in p.items() if k not in ("color", "summary")} for p in cfg["profiles"]]
    profiles.append({"id": "nuit1", "name": "Nuit", "hvac_mode": "heat", "temperature": 17.5})
    groups = [{"id": "g", "name": "Séjour", "climates": [A]}, {"id": "g2", "name": "Bureau", "climates": ["climate.bureau"]}]
    pumps = [{"id": "pac1", "name": "PAC", "climates": [A, "climate.bureau"], "priority": A, "compressor_max": 80}]
    plannings = [{"id": p["id"], "name": p["name"], "allowed": p["allowed"] + ["nuit1"]} for p in cfg["plannings"]]
    await client.send_json({"id": 2, "type": "split_scheduler/config/save", "profiles": profiles,
                            "groups": groups, "heat_pumps": pumps, "plannings": plannings,
                            "offsets": {A: {"heat": 1.4, "cool": 0}},
                            "programs": {"normal": {"g2": {"0": [["06:00", "nuit1"]]}}}})
    reply = await client.receive_json()
    assert reply["success"], reply
    await hass.async_block_till_done()
    opts = entry.options
    assert opts["profiles"]["nuit1"]["temperature"] == 17.5
    assert opts["groups"]["g2"]["pos"] == 1 and opts["heat_pumps"]["pac1"]["priority"] == A
    assert opts["split_offsets"] == {A: {"heat": 1.5}}
    assert opts["plannings"]["normal"]["programs"]["g2"]["0"] == [["06:00", "nuit1"]]

    # Refus : profil utilisé supprimé, split dans deux pompes, noms en double
    for n, (change, msg) in enumerate((
        ({"profiles": [p for p in profiles if p["id"] != "nuit1"]}, "encore utilisé"),
        ({"heat_pumps": pumps + [{"id": "pac2", "name": "PAC 2", "climates": [A]}]}, "autre pompe"),
        ({"groups": groups + [{"id": "g3", "name": "séjour", "climates": [A]}]}, "déjà utilisé"),
    )):
        await client.send_json({"id": 10 + n, "type": "split_scheduler/config/save", **change})
        reply = await client.receive_json()
        assert not reply["success"] and msg in reply["error"]["message"], reply
    # Groupe supprimé : son programme disparaît
    await client.send_json({"id": 30, "type": "split_scheduler/config/save", "groups": groups[:1]})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    assert "g2" not in entry.options["plannings"]["normal"]["programs"]
