"""Unité extérieure silencieuse (interrupteur Faikout « quiet ») ; préréglage retiré."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_mock_service,
)

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.split_scheduler.const import DOMAIN, default_options, with_positions

PARIS = ZoneInfo("Europe/Paris")
ATTRS = {"hvac_modes": ["off", "heat", "cool"], "temperature": 20, "min_temp": 16, "max_temp": 32,
         "target_temp_step": 0.5, "supported_features": 1}


def _faikout_split(hass, name: str, quiet: bool = True) -> tuple[str, str | None]:
    """Split Faikout simulé : thermostat et, si demandé, interrupteur « quiet » sur le même appareil."""
    mqtt = MockConfigEntry(domain="mqtt")
    mqtt.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(config_entry_id=mqtt.entry_id, identifiers={("mqtt", name)})
    reg = er.async_get(hass)
    climate = reg.async_get_or_create("climate", "mqtt", name, device_id=device.id, suggested_object_id=name).entity_id
    hass.states.async_set(climate, "heat", ATTRS)
    switch = None
    if quiet:
        switch = reg.async_get_or_create("switch", "mqtt", f"{name}quiet", device_id=device.id,
                                         suggested_object_id=f"{name}_quiet_outdoor").entity_id
        hass.states.async_set(switch, "off")
    return climate, switch


async def _setup(hass, freezer, climates, confort_extra=None, options_extra=None):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    events = async_capture_events(hass, "call_service")   # le domaine switch a ses vrais services
    async_mock_service(hass, "climate", "set_temperature")
    async_mock_service(hass, "climate", "set_hvac_mode")
    freezer.move_to(datetime(2026, 11, 10, 21, 0, tzinfo=PARIS))
    options = default_options()
    options["profiles"]["confort"].update(confort_extra or {})
    options["groups"] = {"chambres": {"name": "Chambres", "climates": climates}}
    options["plannings"]["normal"]["programs"] = {"chambres": {str(d): [["06:00", "confort"], ["22:30", "eco"]] for d in range(7)}}
    options.update(options_extra or {})
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, events


def _switch_calls(events, service):
    return [e.data["service_data"]["entity_id"] for e in events
            if e.data["domain"] == "switch" and e.data["service"] == service]


async def test_profile_sets_quiet_on_splits_that_have_it(hass: HomeAssistant, freezer):
    one, q1 = _faikout_split(hass, "chambre_1")
    two, _ = _faikout_split(hass, "chambre_2", quiet=False)
    entry, events = await _setup(hass, freezer, [one, two], {"quiet_outdoor": True})
    assert _switch_calls(events, "turn_on") == [q1]                 # chambre 2 : pas d'interrupteur, ignorée
    attrs = hass.states.get("select.chambres_profil").attributes
    assert attrs["silence_exterieur"] == {one: {"interrupteur": q1, "etat": "off"},
                                          two: {"interrupteur": None, "etat": None}}


async def test_quiet_never_counts_as_override(hass: HomeAssistant, freezer):
    one, q1 = _faikout_split(hass, "chambre_1")
    two, q2 = _faikout_split(hass, "chambre_2")
    entry, events = await _setup(hass, freezer, [one, two], {"quiet_outdoor": True})
    scheduler = entry.runtime_data
    for sw in (q1, q2):
        hass.states.async_set(sw, "on")
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(q1, "off")                                # télécommande
    await hass.async_block_till_done()
    assert hass.states.get("sensor.chambres_statut").state == "scheduled"
    # Depuis la carte : envoyé à tous les splits, pas de dérogation
    assert await scheduler.async_set_quiet("chambres", False) == []
    assert sorted(_switch_calls(events, "turn_off")) == [q2]        # q1 déjà coupé
    assert hass.states.get("sensor.chambres_statut").state == "scheduled"
    assert hass.states.get("select.chambres_profil").attributes["derogation"] is False
    # Interrupteur sans réponse : signalé
    hass.states.async_set(q2, "unavailable")
    assert await scheduler.async_set_quiet("chambres", True) == [two]


async def test_quiet_field_in_profile_form(hass: HomeAssistant):
    hass.config.language = "fr"
    one, _ = _faikout_split(hass, "salon")
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
    assert "quiet_outdoor" in fields and "preset_mode" not in fields
    await flow.async_configure(fid, {"name": "Nuit", "hvac_mode": "heat", "temperature": 18, "quiet_outdoor": "on"})
    profiles = flow._progress[fid]._options["profiles"]
    nuit = next(p for p in profiles.values() if p["name"] == "Nuit")
    assert nuit["quiet_outdoor"] is True


async def test_presets_removed_from_existing_profiles(hass: HomeAssistant, freezer):
    one, _ = _faikout_split(hass, "chambre_1", quiet=False)
    entry, _ = await _setup(hass, freezer, [one], {"preset_mode": "eco"}, {"migrations": ["summer_profiles"]})
    assert "preset_mode" not in entry.options["profiles"]["confort"]
    assert "remove_presets" in entry.options["migrations"]
