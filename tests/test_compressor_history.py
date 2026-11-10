"""Reconstitution des démarrages du compresseur depuis l'historique (recorder)."""

from datetime import datetime, timedelta

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from homeassistant.core import HomeAssistant

from custom_components.split_scheduler.const import DOMAIN, default_options, with_positions

from .test_compressor_integration import ATTRS, CLIMATE, COMP, PARIS


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock, enable_custom_integrations):
    """L'enregistreur doit être prêt avant Home Assistant."""
    yield


async def test_backfill_from_recorder_history(recorder_mock, hass: HomeAssistant, freezer):
    """À l'installation, les démarrages déjà enregistrés dans l'historique sont comptés."""
    from pytest_homeassistant_custom_component.components.recorder.common import (
        async_wait_recording_done,
    )

    hass.config.language = "fr"
    await hass.config.async_set_time_zone("Europe/Paris")
    freezer.move_to(datetime(2026, 11, 10, 10, 0, tzinfo=PARIS))
    hass.states.async_set(COMP, "0", {"unit_of_measurement": "Hz"})
    for _ in range(3):  # 3 démarrages en 1 h 30, avant l'installation
        freezer.tick(timedelta(minutes=10))
        hass.states.async_set(COMP, "40", {"unit_of_measurement": "Hz"})
        freezer.tick(timedelta(minutes=20))
        hass.states.async_set(COMP, "0", {"unit_of_measurement": "Hz"})
    await async_wait_recording_done(hass)

    for svc in ("set_hvac_mode", "set_temperature"):
        async_mock_service(hass, "climate", svc)
    hass.states.async_set(CLIMATE, "heat", ATTRS)
    options = default_options()
    options["groups"] = {"salon": {"name": "Salon", "climates": [CLIMATE], "compressor": COMP}}
    entry = MockConfigEntry(domain=DOMAIN, options=with_positions(options))
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.salon_demarrages_du_compresseur_par_heure_24_h")
    assert state.attributes["demarrages"] == 3
    assert float(state.state) == 2.0  # 3 démarrages en 1,5 h d'historique
