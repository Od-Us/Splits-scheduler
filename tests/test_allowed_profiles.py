"""Profils autorisés selon le type de planning."""

import json
from pathlib import Path

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.split_scheduler.const import (
    DOMAIN,
    default_options,
    with_positions,
)

SPLIT = "climate.salon"
ATTRS = {"hvac_modes": ["off", "heat", "cool"], "temperature": 20, "supported_features": 1}


async def _entry(hass: HomeAssistant):
    hass.config.language = "fr"
    for svc in ("set_hvac_mode", "set_temperature"):
        async_mock_service(hass, "climate", svc)
    hass.states.async_set(SPLIT, "heat", ATTRS)
    options = default_options()
    options["groups"] = {"salon": {"name": "Salon", "climates": [SPLIT]}}
    options["plannings"]["normal"]["programs"] = {"salon": {"0": [["06:00", "confort"]]}}
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    return entry, flow, fid


def _labels(result, key):
    return [o["value"] for o in result["data_schema"].schema[key].config["options"]]


async def test_planning_allowed_profiles(hass: HomeAssistant):
    entry, flow, fid = await _entry(hass)
    await flow.async_configure(fid, {"next_step_id": "plannings"})
    await flow.async_configure(fid, {"next_step_id": "planning_edit_pick"})
    result = await flow.async_configure(fid, {"planning": "normal"})
    key = next(k for k in result["data_schema"].schema if k == "allowed_profiles")
    assert len(key.default()) == 10  # tous cochés au départ

    winter = ["hors_gel", "eco", "eco_absence", "confort", "boost", "arret", "manuel"]
    # Confort est utilisé dans le programme : impossible de le décocher
    result = await flow.async_configure(fid, {"name": "Normal", "allowed_profiles": ["eco"]})
    assert result["errors"] == {"allowed_profiles": "allowed_in_use"}
    assert result["description_placeholders"]["used"] == "Confort"
    result = await flow.async_configure(fid, {"name": "Normal", "allowed_profiles": []})
    assert result["errors"] == {"allowed_profiles": "allowed_required"}
    await flow.async_configure(fid, {"name": "Normal", "allowed_profiles": winter})
    await flow.async_configure(fid, {"next_step_id": "init"})

    # Édition d'une ligne : seuls les profils autorisés sont proposés
    await flow.async_configure(fid, {"next_step_id": "program_pick"})
    await flow.async_configure(fid, {"planning": "normal", "group": "salon"})
    await flow.async_configure(fid, {"next_step_id": "day_tue"})
    result = await flow.async_configure(fid, {"choice": "add"})
    assert _labels(result, "profile") == winter
    await flow.async_configure(fid, {"time": "08:00", "profile": "eco"})
    await flow.async_configure(fid, {"choice": "back"})
    # Saisie rapide : profil non autorisé refusé
    await flow.async_configure(fid, {"next_step_id": "program_edit"})
    result = await flow.async_configure(fid, {"mon": "06:00 Confort été"})
    assert result["errors"] == {"mon": "invalid_program"}
    assert "non autorisé" in result["description_placeholders"]["problems"]
    await flow.async_configure(fid, {"mon": "06:00 Confort"})
    await flow.async_configure(fid, {"next_step_id": "init"})

    # Nouveau profil : autorisé partout ; profil supprimé : retiré des listes
    await flow.async_configure(fid, {"next_step_id": "profiles"})
    await flow.async_configure(fid, {"next_step_id": "profile_add"})
    await flow.async_configure(fid, {"name": "Nuit", "hvac_mode": "heat", "temperature": 17})
    await flow.async_configure(fid, {"next_step_id": "profile_delete"})
    await flow.async_configure(fid, {"profiles": ["boost"]})
    await flow.async_configure(fid, {"next_step_id": "init"})
    await flow.async_configure(fid, {"next_step_id": "save"})
    await hass.async_block_till_done()

    allowed = entry.options["plannings"]["normal"]["allowed_profiles"]
    nuit = next(pid for pid, p in entry.options["profiles"].items() if p["name"] == "Nuit")
    assert nuit in allowed and "boost" not in allowed and "confort_ete" not in allowed
    assert "allowed_profiles" not in entry.options["plannings"]["vacances"]  # inchangé : tous

    # Le sélecteur de profil suit le planning du groupe
    options = hass.states.get("select.salon_profil").attributes["options"]
    assert "Confort été" not in options and "Nuit" in options
    await hass.services.async_call(
        "select", "select_option", {"entity_id": "select.salon_planning", "option": "Vacances"},
        blocking=True,
    )
    assert "Confort été" in hass.states.get("select.salon_profil").attributes["options"]


async def test_websocket_lists_devices_and_allowed(hass: HomeAssistant, hass_ws_client):
    entry, flow, fid = await _entry(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "split_scheduler/info"})
    info = (await client.receive_json())["result"]
    assert info["groups"][0]["devices"] == {SPLIT: None}
    # version installée, comparée par la carte à la sienne (cache du navigateur)
    manifest = Path(__file__).parents[1] / "custom_components/split_scheduler/manifest.json"
    assert info["version"] == json.loads(manifest.read_text())["version"]
    normal = next(p for p in info["plannings"] if p["id"] == "normal")
    assert len(normal["allowed_profiles"]) == 10
