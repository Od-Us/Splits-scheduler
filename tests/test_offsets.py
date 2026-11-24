"""Décalage de consigne par split : envoyé au split, invisible à l'affichage."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from homeassistant.core import HomeAssistant

from custom_components.split_scheduler.const import DOMAIN, default_options, split_offset, with_positions

PARIS = ZoneInfo("Europe/Paris")
A, B = "climate.sejour", "climate.bureau"
ATTRS = {"hvac_modes": ["off", "heat", "cool", "dry"], "temperature": 20, "min_temp": 16,
         "max_temp": 32, "target_temp_step": 0.5, "supported_features": 1}
OFFSETS = {A: {"heat": 1.5, "cool": -1.0}}


def test_split_offset_by_mode():
    assert split_offset(OFFSETS, A, "heat") == 1.5
    assert split_offset(OFFSETS, A, "dry") == -1.0
    assert split_offset(OFFSETS, A, "fan_only") == 0.0
    assert split_offset(OFFSETS, B, "heat") == 0.0


async def _setup(hass, freezer, climates, program="confort"):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    calls = {n: async_mock_service(hass, "climate", n) for n in ("set_hvac_mode", "set_temperature")}
    freezer.move_to(datetime(2026, 11, 10, 21, 0, tzinfo=PARIS))
    for eid in climates:
        hass.states.async_set(eid, "heat", ATTRS)
    options = default_options()
    options["groups"] = {"g": {"name": "Séjour", "climates": climates}}
    options["split_offsets"] = OFFSETS
    options["plannings"]["normal"]["programs"] = {"g": {str(d): [["00:00", program]] for d in range(7)}}
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, calls


def _sent(calls, eid):
    return [c.data["temperature"] for c in calls["set_temperature"] if c.data["entity_id"] in (eid, [eid])]


async def test_offset_sent_but_not_an_override(hass: HomeAssistant, freezer):
    entry, calls = await _setup(hass, freezer, [A, B])
    assert _sent(calls, A) == [21.5]          # Confort 20 °C + 1,5
    assert _sent(calls, B) == []              # déjà à 20 °C
    assert hass.states.get("sensor.sejour_consigne").state == "20.0"   # affichage inchangé
    # Le split confirme 21,5 °C : ce n'est pas une dérogation
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(A, "heat", {**ATTRS, "temperature": 21.5})
    await hass.async_block_till_done()
    attrs = hass.states.get("select.sejour_profil").attributes
    assert attrs["derogations_splits"] == [] and attrs["derogation"] is False
    # Télécommande à 23 °C : dérogation, écart affiché sans le décalage (21,5 au lieu de 20)
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(A, "heat", {**ATTRS, "temperature": 23})
    await hass.async_block_till_done()
    ovr = hass.states.get("select.sejour_profil").attributes["derogations_splits"]
    assert ovr[0]["ecarts"] == [{"reglage": "temperature", "valeur": 21.5, "prevu": 20.0}]


async def test_cool_offset_and_single_split_manual(hass: HomeAssistant, freezer):
    entry, calls = await _setup(hass, freezer, [A], program="confort_ete")
    assert _sent(calls, A) == [25.0]          # Confort été 26 °C − 1
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(A, "cool", {**ATTRS, "temperature": 23})    # télécommande
    await hass.async_block_till_done()
    assert entry.runtime_data.states["g"].manual_settings["temperature"] == 24.0   # 23 + 1
    assert hass.states.get("sensor.sejour_consigne").state == "24.0"


async def test_offsets_form(hass: HomeAssistant, freezer):
    entry, _calls = await _setup(hass, freezer, [A, B])
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    await flow.async_configure(fid, {"next_step_id": "groups"})
    result = await flow.async_configure(fid, {"next_step_id": "split_offsets"})
    assert result["step_id"] == "split_offsets"
    labels = [str(k) for k in result["data_schema"].schema]
    assert labels == ["sejour · décalage chauffage", "sejour · décalage froid",
                      "bureau · décalage chauffage", "bureau · décalage froid"]
    await flow.async_configure(fid, {labels[0]: 1.5, labels[1]: 0, labels[2]: -0.7, labels[3]: 0})
    await flow.async_configure(fid, {"next_step_id": "init"})
    await flow.async_configure(fid, {"next_step_id": "save"})
    await hass.async_block_till_done()
    assert entry.options["split_offsets"] == {A: {"heat": 1.5}, B: {"heat": -0.5}}


async def test_changed_offset_is_sent_at_once(hass: HomeAssistant, freezer):
    entry, calls = await _setup(hass, freezer, [A, B])
    hass.states.async_set(A, "heat", {**ATTRS, "temperature": 21.5})
    await hass.async_block_till_done()
    options = {**entry.options, "split_offsets": {A: {"heat": 1.5}, B: {"heat": 1.0}}}
    hass.config_entries.async_update_entry(entry, options=options)
    await hass.async_block_till_done()
    assert _sent(calls, B) == [21.0]           # renvoyé sans attendre le créneau suivant
    assert _sent(calls, A) == [21.5]           # inchangé : pas renvoyé
