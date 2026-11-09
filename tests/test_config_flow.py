"""Tests de la configuration depuis l'interface."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.split_scheduler.const import DOMAIN


async def _create_entry(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return result["result"]


async def test_create_entry_with_defaults(hass: HomeAssistant):
    entry = await _create_entry(hass)
    assert "Confort" in [p["name"] for p in entry.options["profiles"].values()]
    assert len(entry.options["plannings"]) == 3
    # Une seule instance
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT


async def test_options_full_path(hass: HomeAssistant):
    hass.states.async_set(
        "climate.bureau", "off", {"hvac_modes": ["off", "heat"], "fan_modes": ["auto", "night"]}
    )
    entry = await _create_entry(hass)
    flow = hass.config_entries.options
    result = await flow.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert "program_pick" not in result["menu_options"]  # pas encore de groupe
    fid = result["flow_id"]

    # Groupe
    result = await flow.async_configure(fid, {"next_step_id": "groups"})
    result = await flow.async_configure(fid, {"next_step_id": "group_add"})
    result = await flow.async_configure(fid, {"name": "Bureau", "climates": []})
    assert result["errors"] == {"climates": "climates_required"}
    result = await flow.async_configure(fid, {"name": "Bureau", "climates": ["climate.bureau"]})
    assert result["type"] is FlowResultType.MENU
    result = await flow.async_configure(fid, {"next_step_id": "init"})

    # Profil avec un mode ventilateur proposé par le split
    result = await flow.async_configure(fid, {"next_step_id": "profiles"})
    result = await flow.async_configure(fid, {"next_step_id": "profile_add"})
    fan = result["data_schema"].schema
    fan_selector = next(v for k, v in fan.items() if k == "fan_mode")
    assert fan_selector.config["options"] == ["auto", "night"]
    result = await flow.async_configure(fid, {"name": "eco", "hvac_mode": "heat"})
    assert result["errors"] == {"name": "name_taken"}
    result = await flow.async_configure(
        fid, {"name": "Nuit", "hvac_mode": "heat", "temperature": 17, "fan_mode": "night"}
    )
    result = await flow.async_configure(fid, {"next_step_id": "init"})

    # Programme
    planning_id = next(iter(entry.options["plannings"]))
    group_id = next(iter(hass.config_entries.options._progress[fid]._options["groups"]))
    result = await flow.async_configure(fid, {"next_step_id": "program_pick"})
    result = await flow.async_configure(fid, {"planning": planning_id, "group": group_id})
    assert result["step_id"] == "program_edit"
    result = await flow.async_configure(fid, {"mon": "06:30 Confort, 25:00 Eco"})
    assert result["errors"] == {"mon": "invalid_program"}
    assert "heure invalide" in result["description_placeholders"]["problems"]
    result = await flow.async_configure(
        fid,
        {"mon": "06:30 Confort, 22:00 nuit", "sat": "09:00 Confort", "copy_monday_to": ["tue", "fri"]},
    )
    assert result["type"] is FlowResultType.MENU

    # Suppression d'un profil utilisé : refusée
    result = await flow.async_configure(fid, {"next_step_id": "profiles"})
    result = await flow.async_configure(fid, {"next_step_id": "profile_delete"})
    nuit_id = next(
        pid for pid, p in hass.config_entries.options._progress[fid]._options["profiles"].items()
        if p["name"] == "Nuit"
    )
    result = await flow.async_configure(fid, {"profiles": [nuit_id]})
    assert result["errors"] == {"base": "profile_in_use"}
    assert result["description_placeholders"]["used"] == "Nuit"
    result = await flow.async_configure(fid, {"profiles": []})
    result = await flow.async_configure(fid, {"next_step_id": "init"})

    result = await flow.async_configure(fid, {"next_step_id": "save"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    program = entry.options["plannings"][planning_id]["programs"][group_id]
    assert program["0"] == [["06:30", "confort"], ["22:00", nuit_id]]
    assert program["1"] == program["4"] == program["0"]
    assert "2" not in program and program["5"] == [["09:00", "confort"]]
    nuit = entry.options["profiles"][nuit_id]
    assert nuit == {"name": "Nuit", "hvac_mode": "heat", "temperature": 17.0, "fan_mode": "night"}
    # Rechargée avec les nouvelles entités
    assert hass.states.get("select.bureau_profile") is not None
