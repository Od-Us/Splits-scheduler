"""Charge du compresseur (%) : fréquence maximale saisie ou observée sur 30 jours."""

from datetime import datetime
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from homeassistant.core import HomeAssistant

from custom_components.split_scheduler.compressor import robust_maximum
from custom_components.split_scheduler.const import DOMAIN, default_options, with_positions

from .test_compressor_integration import ATTRS, CLIMATE, COMP, PARIS


def test_robust_maximum_ignores_isolated_spikes():
    hours = [0, 0, 30, 41, 55, 62, 64, 63, 240]          # 240 : une seule heure, ignorée ; 0 : arrêt
    assert robust_maximum(hours, "Hz") == 63              # 3e plus forte heure : 240, 64, puis 63
    assert robust_maximum([64, 999, 63, 70], "Hz") == 63  # 999 Hz impossible
    assert robust_maximum([4200, 3900, 4100, 9000], "rpm") == 4100
    assert robust_maximum([50, 0, 60], "Hz") is None      # moins de 3 heures de marche


async def _setup(hass, freezer, group_extra=None, unit="Hz"):
    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    for svc in ("set_hvac_mode", "set_temperature"):
        async_mock_service(hass, "climate", svc)
    freezer.move_to(datetime(2026, 11, 10, 12, 0, tzinfo=PARIS))
    hass.states.async_set(CLIMATE, "heat", ATTRS)
    hass.states.async_set(COMP, "26", {"unit_of_measurement": unit})
    options = default_options()
    options["groups"] = {"salon": {"name": "Salon", "climates": [CLIMATE], "compressor": COMP, **(group_extra or {})}}
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_load_with_entered_maximum(hass: HomeAssistant, freezer):
    await _setup(hass, freezer, {"compressor_max": 75})
    load = hass.states.get("sensor.salon_charge_du_compresseur")
    assert load.state == "35"                                # 26 / 75
    assert load.attributes["frequence_max"] == 75.0 and load.attributes["source_max"] == "saisie"
    assert load.attributes["unite"] == "Hz"
    hass.states.async_set(COMP, "90", {"unit_of_measurement": "Hz"})   # au-delà du maximum : 100 %
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_charge_du_compresseur").state == "100"


async def test_load_with_observed_maximum_in_rpm(hass: HomeAssistant, freezer):
    with patch(
        "custom_components.split_scheduler.scheduler.SplitScheduler._async_hourly_maxima",
        return_value=[5200, 5100, 5000, 4000, 15000.5],
    ):
        await _setup(hass, freezer, unit="rpm")
    hass.states.async_set(COMP, "2500", {"unit_of_measurement": "rpm"})
    await hass.async_block_till_done()
    load = hass.states.get("sensor.salon_charge_du_compresseur")
    assert load.attributes["frequence_max"] == 5000.0 and load.attributes["source_max"] == "observee_30j"
    assert load.attributes["unite"] == "rpm" and load.state == "50"


async def test_load_unknown_without_history(hass: HomeAssistant, freezer):
    await _setup(hass, freezer)
    load = hass.states.get("sensor.salon_charge_du_compresseur")
    assert load.state == "unknown" and load.attributes["frequence_max"] is None
