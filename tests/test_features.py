"""Fonctions Daikin (interrupteurs Faikout) : profils, envoi, dérogation."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_mock_service,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.split_scheduler.const import DOMAIN, default_options, with_positions

PARIS = ZoneInfo("Europe/Paris")
ATTRS = {"hvac_modes": ["off", "heat", "cool"], "temperature": 20, "min_temp": 16, "max_temp": 32,
         "target_temp_step": 0.5, "supported_features": 1, "swing_modes": ["off", "H", "V", "H+V"],
         "swing_mode": "off"}


def _faikout_split(hass, name: str, functions: tuple[str, ...]) -> tuple[str, dict[str, str]]:
    """Split Faikout simulé : thermostat et interrupteurs sur le même appareil (unique_id + suffixe)."""
    mqtt = MockConfigEntry(domain="mqtt")
    mqtt.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(config_entry_id=mqtt.entry_id, identifiers={("mqtt", name)})
    reg = er.async_get(hass)
    climate = reg.async_get_or_create("climate", "mqtt", name, device_id=device.id, suggested_object_id=name).entity_id
    hass.states.async_set(climate, "heat", ATTRS)
    switches = {}
    for suffix in functions:
        sw = reg.async_get_or_create("switch", "mqtt", f"{name}{suffix}", device_id=device.id,
                                     suggested_object_id=f"{name}_{suffix}").entity_id
        hass.states.async_set(sw, "off")
        switches[suffix] = sw
    return climate, switches


async def _setup(hass, freezer, climates, profile_extra):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    events = async_capture_events(hass, "call_service")   # le domaine switch a ses vrais services
    async_mock_service(hass, "climate", "set_temperature")
    async_mock_service(hass, "climate", "set_hvac_mode")
    freezer.move_to(datetime(2026, 11, 10, 21, 0, tzinfo=PARIS))
    options = default_options()
    options["profiles"]["confort"].update(profile_extra)
    options["groups"] = {"chambres": {"name": "Chambres", "climates": climates}}
    options["plannings"]["normal"]["programs"] = {"chambres": {str(d): [["06:00", "confort"]] for d in range(7)}}
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    calls = {
        name: [e for e in events if e.data["domain"] == "switch" and e.data["service"] == name]
        for name in ("turn_on", "turn_off")
    }
    return entry, calls


async def test_functions_sent_and_remote_change_is_override(hass: HomeAssistant, freezer):
    one, sw1 = _faikout_split(hass, "chambre_1", ("comfort", "streamer", "sensor", "quiet"))
    two, sw2 = _faikout_split(hass, "chambre_2", ("quiet",))   # sans capteur de présence
    entry, calls = await _setup(hass, freezer, [one, two], {"sensor_mode": True, "quiet_outdoor": True})
    on = sorted(c.data["service_data"]["entity_id"] for c in calls["turn_on"])
    assert on == sorted([sw1["sensor"], sw1["quiet"], sw2["quiet"]])   # chambre 2 : pas de capteur, ignoré
    info = entry.runtime_data.switches
    assert info[one] == {"comfort": sw1["comfort"], "streamer": sw1["streamer"],
                         "sensor_mode": sw1["sensor"], "quiet_outdoor": sw1["quiet"]}

    # Les splits suivent ; plus tard, le capteur de présence est coupé à la télécommande
    for sw in (sw1["sensor"], sw1["quiet"], sw2["quiet"]):
        hass.states.async_set(sw, "on")
    await hass.async_block_till_done()
    assert hass.states.get("sensor.chambres_statut").state == "scheduled"
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(sw1["sensor"], "off")
    await hass.async_block_till_done()
    (held,) = hass.states.get("select.chambres_profil").attributes["derogations_splits"]
    assert held["entity_id"] == one
    assert held["ecarts"] == [{"reglage": "sensor_mode", "valeur": False, "prevu": True}]


async def test_presence_setpoint_shift_is_an_override(hass: HomeAssistant, freezer):
    one, _ = _faikout_split(hass, "salon", ("sensor",))
    await _setup(hass, freezer, [one], {"sensor_mode": True})
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(one, "heat", {**ATTRS, "temperature": 18})   # consigne baissée par le capteur
    await hass.async_block_till_done()
    attrs = hass.states.get("select.chambres_profil").attributes
    assert attrs["derogation"] is True   # groupe d'un seul split : dérogation du groupe


async def test_comfort_with_vertical_swing_is_refused(hass: HomeAssistant):
    from homeassistant import config_entries

    hass.config.language = "fr"
    one, _ = _faikout_split(hass, "salon", ("comfort", "sensor"))
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    entry = (await hass.config_entries.flow.async_configure(result["flow_id"], {}))["result"]
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    await flow.async_configure(fid, {"next_step_id": "groups"})
    await flow.async_configure(fid, {"next_step_id": "group_add"})
    await flow.async_configure(fid, {"name": "Salon", "climates": [one]})
    await flow.async_configure(fid, {"next_step_id": "init"})
    await flow.async_configure(fid, {"next_step_id": "profiles"})
    result = await flow.async_configure(fid, {"next_step_id": "profile_add"})
    fields = {str(k) for k in result["data_schema"].schema}
    assert {"comfort", "sensor_mode"} <= fields and "streamer" not in fields   # seulement celles des splits
    result = await flow.async_configure(fid, {"name": "Nuit", "comfort": "on", "swing_mode": "V"})
    assert result["errors"] == {"comfort": "comfort_swing"}
    result = await flow.async_configure(fid, {"name": "Nuit", "comfort": "on", "sensor_mode": "off", "swing_mode": "H"})
    profiles = flow._progress[fid]._options["profiles"]
    nuit = next(p for p in profiles.values() if p["name"] == "Nuit")
    assert nuit["comfort"] is True and nuit["sensor_mode"] is False
