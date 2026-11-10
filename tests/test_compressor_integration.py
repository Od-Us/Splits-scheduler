"""Démarrages du compresseur dans Home Assistant (capteur Faikout simulé)."""

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
CLIMATE = "climate.salon"
COMP = "sensor.salon_compressor"
ATTRS = {"hvac_modes": ["off", "heat"], "temperature": 20, "min_temp": 16, "max_temp": 32,
         "target_temp_step": 0.5, "supported_features": 1}


async def _setup(hass, freezer, start):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    for svc in ("set_hvac_mode", "set_temperature"):
        async_mock_service(hass, "climate", svc)
    freezer.move_to(start)
    hass.states.async_set(CLIMATE, "heat", ATTRS)
    hass.states.async_set(COMP, "0", {"unit_of_measurement": "Hz"})
    options = default_options()
    options["groups"] = {"salon": {"name": "Salon", "climates": [CLIMATE], "compressor": COMP}}
    options["plannings"]["normal"]["programs"] = {
        "salon": {str(d): [["06:00", "confort"], ["22:00", "eco"]] for d in range(7)}
    }
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _cycle(hass, freezer, minutes_on=10, minutes_off=20):
    hass.states.async_set(COMP, "42", {"unit_of_measurement": "Hz"})
    freezer.tick(timedelta(minutes=minutes_on))
    hass.states.async_set(COMP, "0", {"unit_of_measurement": "Hz"})
    freezer.tick(timedelta(minutes=minutes_off))
    await hass.async_block_till_done()


async def _refresh(hass):
    """Déclenche la mise à jour périodique des moyennes."""
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=1))
    await hass.async_block_till_done()


async def test_starts_per_hour(hass: HomeAssistant, freezer):
    entry = await _setup(hass, freezer, datetime(2026, 11, 10, 12, 0, tzinfo=PARIS))
    day = "sensor.salon_demarrages_du_compresseur_par_heure_24_h"
    prof = "sensor.salon_demarrages_du_compresseur_par_heure_profil_actuel"
    assert hass.states.get(day) is not None and hass.states.get(prof) is not None
    for _ in range(4):  # 4 cycles de 30 minutes : 2 h, 4 démarrages
        await _cycle(hass, freezer)
    await _refresh(hass)
    assert float(hass.states.get(day).state) == 2.0
    attrs = hass.states.get(day).attributes
    assert attrs["demarrages"] == 4 and attrs["duree_h"] == 2.0
    assert attrs["capteur_compresseur"] == COMP
    assert hass.states.get(prof).attributes["profil"] == "Confort"

    # Changement de profil : la moyenne « profil » repart de zéro
    await hass.services.async_call(
        "select", "select_option", {"entity_id": "select.salon_profil", "option": "Boost"},
        blocking=True,
    )
    freezer.tick(timedelta(minutes=30))
    await _cycle(hass, freezer, 10, 20)  # 1 démarrage en 1 h depuis Boost
    await _refresh(hass)
    assert float(hass.states.get(prof).state) == 1.0
    assert hass.states.get(prof).attributes["profil"] == "Boost"
    assert float(hass.states.get(day).state) == round(5 / 3, 1)

    # Les démarrages survivent à un rechargement
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await _refresh(hass)
    assert hass.states.get(day).attributes["demarrages"] == 5


async def test_no_compressor_no_sensors(hass: HomeAssistant, freezer):
    hass.config.language = "fr"
    freezer.move_to(datetime(2026, 11, 10, 12, 0, tzinfo=PARIS))
    hass.states.async_set(CLIMATE, "heat", ATTRS)
    options = default_options()
    options["groups"] = {"salon": {"name": "Salon", "climates": [CLIMATE]}}
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert not [s for s in hass.states.async_entity_ids("sensor") if "compresseur" in s]


async def test_compressor_sensor_is_detected(hass: HomeAssistant):
    """Le capteur « Compressor » du même appareil Faikout est proposé tout seul."""
    hass.config.language = "fr"
    source = MockConfigEntry(domain="mqtt")
    source.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=source.entry_id, identifiers={("mqtt", "faikout_1")}, name="Split salon"
    )
    registry = er.async_get(hass)
    registry.async_get_or_create("climate", "mqtt", "salon_climate", device_id=device.id,
                                 suggested_object_id="salon")
    registry.async_get_or_create("sensor", "mqtt", "salon_comp", device_id=device.id,
                                 suggested_object_id="salon_compressor",
                                 original_name="Compressor")
    registry.async_get_or_create("sensor", "mqtt", "salon_temp", device_id=device.id,
                                 suggested_object_id="salon_temperature")
    hass.states.async_set(CLIMATE, "heat", ATTRS)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    entry = (await hass.config_entries.flow.async_configure(result["flow_id"], {}))["result"]
    flow = hass.config_entries.options
    fid = (await flow.async_init(entry.entry_id))["flow_id"]
    await flow.async_configure(fid, {"next_step_id": "groups"})
    result = await flow.async_configure(fid, {"next_step_id": "group_add"})
    assert "compressor" in result["data_schema"].schema
    await flow.async_configure(fid, {"name": "Salon", "climates": [CLIMATE]})
    await flow.async_configure(fid, {"next_step_id": "init"})
    await flow.async_configure(fid, {"next_step_id": "save"})
    await hass.async_block_till_done()
    group = next(iter(entry.options["groups"].values()))
    assert group["compressor"] == COMP

