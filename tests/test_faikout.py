"""Splits Faikout (port S21) : attributs typiques."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.split_scheduler.const import DOMAIN, default_options

PARIS = ZoneInfo("Europe/Paris")
SALON = "climate.salon"
FAIKOUT_S21 = {
    "hvac_modes": ["heat_cool", "off", "cool", "heat", "dry", "fan_only"],
    "min_temp": 16,
    "max_temp": 32,
    "target_temp_step": 0.5,
    "fan_modes": ["auto", "night", "low", "lowMedium", "medium", "mediumHigh", "high"],
    "preset_modes": ["none", "boost", "home"],
    "swing_modes": ["off", "H", "V", "H+V"],
    "current_temperature": 21.0,
    "temperature_unit": "°C",
    "temperature": 22,
    "fan_mode": "night",
    "preset_mode": "home",
    "swing_mode": "off",
    "icon": "mdi:thermostat",
    "friendly_name": "Split salon",
    "supported_features": 441,
}
SERVICES = (
    "set_hvac_mode", "set_temperature", "set_fan_mode", "set_swing_mode", "set_preset_mode",
)


async def _setup(hass, freezer, program):
    await hass.config.async_set_time_zone("Europe/Paris")
    calls = {name: async_mock_service(hass, "climate", name) for name in SERVICES}
    hass.states.async_set(SALON, "off", FAIKOUT_S21)
    options = default_options()
    options["profiles"]["doux"] = {
        "name": "Doux", "hvac_mode": "heat", "temperature": 20.3,
        "fan_mode": "lowMedium", "swing_mode": "H+V",
    }
    options["groups"] = {"salon": {"name": "Salon", "climates": [SALON]}}
    options["plannings"]["normal"]["programs"] = {"salon": program}
    freezer.move_to(datetime(2026, 11, 9, 12, 0, tzinfo=PARIS))
    entry = MockConfigEntry(domain=DOMAIN, options=options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return calls


async def test_faikout_profile_values(hass: HomeAssistant, freezer):
    calls = await _setup(hass, freezer, {"0": [["06:00", "doux"]]})
    assert [c.data["hvac_mode"] for c in calls["set_hvac_mode"]] == ["heat"]
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [20.5]  # pas de 0,5
    assert [c.data["fan_mode"] for c in calls["set_fan_mode"]] == ["lowMedium"]
    assert [c.data["swing_mode"] for c in calls["set_swing_mode"]] == ["H+V"]
    assert calls["set_preset_mode"] == []  # le préréglage « home » n'est pas touché

    # Retour d'état de Faikout quelques minutes plus tard : pas de fausse dérogation
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(
        SALON, "heat",
        {**FAIKOUT_S21, "temperature": 20.5, "fan_mode": "lowMedium", "swing_mode": "H+V"},
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_status").state == "scheduled"


async def test_frost_protection_is_raised_to_16(hass: HomeAssistant, freezer):
    calls = await _setup(hass, freezer, {"0": [["06:00", "hors_gel"]]})
    assert [c.data["temperature"] for c in calls["set_temperature"]] == [16]
    freezer.tick(timedelta(minutes=5))
    hass.states.async_set(SALON, "heat", {**FAIKOUT_S21, "temperature": 16})
    await hass.async_block_till_done()
    assert hass.states.get("sensor.salon_status").state == "scheduled"


async def test_profile_form_matches_faikout(hass: HomeAssistant):
    hass.states.async_set(SALON, "off", FAIKOUT_S21)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    entry = result["result"]
    flow = hass.config_entries.options
    result = await flow.async_init(entry.entry_id)
    fid = result["flow_id"]
    await flow.async_configure(fid, {"next_step_id": "profiles"})
    result = await flow.async_configure(fid, {"next_step_id": "profile_add"})
    fields = {str(k): v for k, v in result["data_schema"].schema.items()}
    assert fields["hvac_mode"].config["options"] == [
        "off", "heat", "cool", "heat_cool", "dry", "fan_only",
    ]  # pas de « auto »
    assert fields["fan_mode"].config["options"] == FAIKOUT_S21["fan_modes"]
    assert fields["swing_mode"].config["options"] == ["off", "H", "V", "H+V"]
    assert fields["swing_horizontal_mode"].config["options"] == []
    assert result["description_placeholders"]["limits"] == "16 à 32 °C, pas de 0.5 °C"
