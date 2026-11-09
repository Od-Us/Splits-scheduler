"""Constantes de l'intégration « Programmation des splits »."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "split_scheduler"
TITLE = "Programmation des splits"

PLATFORMS: list[Platform] = [
    Platform.SELECT,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BUTTON,
]

# Clés des options de l'entrée de configuration
CONF_GROUPS = "groups"
CONF_PROFILES = "profiles"
CONF_PLANNINGS = "plannings"
CONF_CLIMATES = "climates"
CONF_PROGRAMS = "programs"

# Réglages possibles d'un profil (absents = « ne pas modifier »)
ATTR_HVAC_MODE = "hvac_mode"
ATTR_TEMPERATURE = "temperature"
ATTR_FAN_MODE = "fan_mode"
ATTR_SWING_MODE = "swing_mode"
ATTR_SWING_HORIZONTAL_MODE = "swing_horizontal_mode"
PROFILE_SETTINGS = (
    ATTR_HVAC_MODE,
    ATTR_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_SWING_MODE,
    ATTR_SWING_HORIZONTAL_MODE,
)

HVAC_MODES = ["off", "heat", "cool", "heat_cool", "auto", "dry", "fan_only"]

# Index = datetime.weekday() (0 = lundi)
WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# Après l'application d'un profil, les changements d'état des splits pendant
# ce délai sont considérés comme la conséquence de nos propres commandes.
GRACE_PERIOD = timedelta(minutes=2)
TEMPERATURE_TOLERANCE = 0.3

STORAGE_VERSION = 1

# Statuts d'un groupe
STATUS_SCHEDULED = "scheduled"
STATUS_OVERRIDE = "override"
STATUS_DISABLED = "disabled"
STATUS_NO_PROGRAM = "no_program"
STATUSES = [STATUS_SCHEDULED, STATUS_OVERRIDE, STATUS_DISABLED, STATUS_NO_PROGRAM]


def default_options() -> dict:
    """Profils et plannings proposés à l'installation (modifiables ensuite)."""
    return {
        CONF_GROUPS: {},
        CONF_PROFILES: {
            "hors_gel": {"name": "Hors gel", ATTR_HVAC_MODE: "heat", ATTR_TEMPERATURE: 10.0},
            "eco": {"name": "Eco", ATTR_HVAC_MODE: "heat", ATTR_TEMPERATURE: 18.0},
            "eco_absence": {"name": "Eco absence", ATTR_HVAC_MODE: "heat", ATTR_TEMPERATURE: 16.0},
            "confort": {"name": "Confort", ATTR_HVAC_MODE: "heat", ATTR_TEMPERATURE: 20.0},
            "confort_absence": {
                "name": "Confort absence",
                ATTR_HVAC_MODE: "heat",
                ATTR_TEMPERATURE: 19.0,
            },
            "boost": {"name": "Boost", ATTR_HVAC_MODE: "heat", ATTR_TEMPERATURE: 23.0},
            "arret": {"name": "Arrêt", ATTR_HVAC_MODE: "off"},
            "manuel": {"name": "Manuel"},
        },
        CONF_PLANNINGS: {
            "normal": {"name": "Normal", CONF_PROGRAMS: {}},
            "vacances": {"name": "Vacances", CONF_PROGRAMS: {}},
            "absence": {"name": "Absence prolongée", CONF_PROGRAMS: {}},
        },
    }
