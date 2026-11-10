"""Édition du programme ligne par ligne et API de la carte."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.split_scheduler.const import DOMAIN

SALON = "climate.salon"
ATTRS = {
    "hvac_modes": ["off", "heat", "cool"], "fan_modes": ["auto", "night"],
    "swing_modes": ["off", "H+V"], "min_temp": 16, "max_temp": 32,
    "target_temp_step": 0.5, "temperature": 19, "fan_mode": "auto", "swing_mode": "off",
    "current_temperature": 18.5, "supported_features": 441,
}


async def _entry_with_group(hass: HomeAssistant):
    hass.config.language = "fr"
    hass.states.async_set(SALON, "heat", ATTRS)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    entry = result["result"]
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    await flow.async_configure(fid, {"next_step_id": "groups"})
    await flow.async_configure(fid, {"next_step_id": "group_add"})
    await flow.async_configure(fid, {"name": "Salon", "climates": [SALON]})
    await flow.async_configure(fid, {"next_step_id": "init"})
    return entry, flow, fid


def _choices(result):
    selector = result["data_schema"].schema["choice"]
    return {o["value"]: o["label"] for o in selector.config["options"]}


async def test_line_by_line_editing(hass: HomeAssistant):
    entry, flow, fid = await _entry_with_group(hass)
    group_id = next(iter(flow._progress[fid]._options["groups"]))
    result = await flow.async_configure(fid, {"next_step_id": "program_pick"})
    result = await flow.async_configure(fid, {"planning": "normal", "group": group_id})
    assert result["type"] is FlowResultType.MENU and result["step_id"] == "program_week"
    assert result["menu_options"][:7] == [f"day_{d}" for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")]
    assert result["description_placeholders"]["mon"] == "Aucun changement"

    # Lundi : ajout de deux lignes (la seconde « insérée » avant la première)
    result = await flow.async_configure(fid, {"next_step_id": "day_mon"})
    assert result["step_id"] == "program_day"
    assert set(_choices(result)) == {"add", "copy", "back"}
    result = await flow.async_configure(fid, {"choice": "add"})
    assert result["step_id"] == "program_line" and "delete" not in result["data_schema"].schema
    labels = {o["value"]: o["label"] for o in result["data_schema"].schema["profile"].config["options"]}
    assert labels["confort"] == "Confort — Chauffage · 20 °C"
    result = await flow.async_configure(fid, {"time": "22:30:00", "profile": "eco"})
    result = await flow.async_configure(fid, {"choice": "add"})
    result = await flow.async_configure(fid, {"time": "06:30:00", "profile": "confort"})
    choices = _choices(result)
    assert list(choices)[:2] == ["line:06:30", "line:22:30"]
    assert choices["line:06:30"] == "06:30  Confort — Chauffage · 20 °C"
    assert "clear" in choices

    # Doublon d'heure refusé, puis modification d'une ligne
    result = await flow.async_configure(fid, {"choice": "line:22:30"})
    assert "delete" in result["data_schema"].schema
    result = await flow.async_configure(fid, {"time": "06:30:00", "profile": "eco"})
    assert result["errors"] == {"time": "time_taken"}
    result = await flow.async_configure(fid, {"time": "22:00:00", "profile": "eco_absence"})
    assert list(_choices(result))[:2] == ["line:06:30", "line:22:00"]

    # Copie du lundi vers mardi et mercredi, puis suppression d'une ligne du lundi
    result = await flow.async_configure(fid, {"choice": "copy"})
    result = await flow.async_configure(fid, {"days": ["tue", "wed"]})
    result = await flow.async_configure(fid, {"choice": "line:22:00"})
    result = await flow.async_configure(fid, {"time": "22:00:00", "profile": "eco_absence", "delete": True})
    assert list(_choices(result))[:1] == ["line:06:30"] and "line:22:00" not in _choices(result)

    result = await flow.async_configure(fid, {"choice": "back"})
    assert result["description_placeholders"]["mon"] == "06:30 Confort"
    assert result["description_placeholders"]["tue"] == "06:30 Confort · 22:00 Eco absence"
    assert result["description_placeholders"]["thu"] == (
        "Aucun changement — Eco absence depuis mercredi 22:00"
    )

    # Copie depuis la semaine, puis vider un jour
    result = await flow.async_configure(fid, {"next_step_id": "program_copy"})
    result = await flow.async_configure(fid, {"source": "tue", "days": ["sat", "sun"]})
    assert result["step_id"] == "program_week"
    result = await flow.async_configure(fid, {"next_step_id": "day_wed"})
    result = await flow.async_configure(fid, {"choice": "clear"})
    result = await flow.async_configure(fid, {"choice": "back"})
    result = await flow.async_configure(fid, {"next_step_id": "init"})
    result = await flow.async_configure(fid, {"next_step_id": "save"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    program = entry.options["plannings"]["normal"]["programs"][group_id]
    week = [["06:30", "confort"], ["22:00", "eco_absence"]]
    assert program == {"0": [["06:30", "confort"]], "1": week, "5": week, "6": week}


async def test_card_websocket_api(hass: HomeAssistant, hass_ws_client):
    entry, flow, fid = await _entry_with_group(hass)
    await flow.async_configure(fid, {"next_step_id": "save"})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "split_scheduler/info"})
    info = (await client.receive_json())["result"]
    group = info["groups"][0]
    assert group["name"] == "Salon" and group["climates"] == [SALON]
    assert group["entities"]["profile"] == "select.salon_profil"
    assert group["entities"]["programming"] == "switch.salon_programmation"
    assert info["global_planning"].startswith("select.")
    confort = next(p for p in info["profiles"] if p["id"] == "confort")
    assert confort["color"] == "#fb8c00"
    assert [p["name"] for p in info["plannings"]][:1] == ["Normal"]

    calls = []

    async def record(call):
        calls.append((call.service, dict(call.data)))

    for service in ("set_temperature", "set_fan_mode"):
        hass.services.async_register("climate", service, record)
    await client.send_json_auto_id(
        {"type": "split_scheduler/manual", "group_id": group["id"], "temperature": 21.3, "fan_mode": "night"}
    )
    assert (await client.receive_json())["success"]
    assert ("set_temperature", {"entity_id": SALON, "temperature": 21.5}) in calls
    assert ("set_fan_mode", {"entity_id": SALON, "fan_mode": "night"}) in calls

    await client.send_json_auto_id({"type": "split_scheduler/manual", "group_id": "nope", "temperature": 20})
    assert not (await client.receive_json())["success"]


async def test_card_is_served(hass: HomeAssistant, hass_client):
    await _entry_with_group(hass)
    client = await hass_client()
    resp = await client.get("/split_scheduler_static/split-scheduler-card.js")
    assert resp.status == 200
    assert "customElements.define" in await resp.text()
    resp = await client.get("/split_scheduler_static/icon.png")
    assert resp.status == 200


async def test_order_survives_sorted_storage(hass: HomeAssistant):
    """Home Assistant trie les clés des options : l'ordre doit être conservé."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.split_scheduler.const import default_options, with_positions

    hass.config.language = "fr"
    hass.states.async_set(SALON, "heat", ATTRS)
    options = default_options()
    options["groups"] = {"zz": {"name": "Salon", "climates": [SALON]}, "aa": {"name": "Bureau", "climates": [SALON]}}
    options["profiles"]["0nuit"] = {"name": "Nuit", "hvac_mode": "heat", "temperature": 17.0}
    with_positions(options)
    # Ancienne entrée sans positions pour les profils : ordre des profils fournis
    for profile in options["profiles"].values():
        profile.pop("pos")
    stored = {
        kind: dict(sorted(items.items())) if isinstance(items, dict) else items
        for kind, items in options.items()
    }
    entry = MockConfigEntry(domain=DOMAIN, options=stored)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("select.salon_planning").attributes["options"] == [
        "Normal", "Vacances", "Absence prolongée",
    ]
    assert hass.states.get("select.salon_planning").state == "Normal"
    assert hass.states.get("select.salon_profil").attributes["options"] == [
        "Hors gel", "Eco", "Eco absence", "Confort", "Confort absence", "Boost",
        "Confort été", "Eco été", "Arrêt", "Manuel", "Nuit",
    ]
    scheduler = entry.runtime_data
    assert [g["name"] for g in scheduler.groups.values()] == ["Salon", "Bureau"]
