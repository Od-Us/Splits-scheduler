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
CONF_COMPRESSOR = "compressor"

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


# ---------------------------------------------------------------------- carte

CARD_FILENAME = "split-scheduler-card.js"
CARD_URL_BASE = "/split_scheduler_static"

# Couleurs des profils sur la carte (repérés par leur nom, sans accents ni casse)
_PROFILE_COLORS = (
    ("hors gel", "#4fc3f7"),
    ("eco absence", "#26a69a"),
    ("eco", "#43a047"),
    ("confort absence", "#fdd835"),
    ("confort", "#fb8c00"),
    ("boost", "#e53935"),
    ("arret", "#9e9e9e"),
    ("manuel", "#8e24aa"),
)
_EXTRA_COLORS = ("#3f51b5", "#ec407a", "#8d6e63", "#5c6bc0", "#00acc1", "#7cb342")


def profile_color(name: str) -> str:
    """Couleur d'un profil : d'après son nom, sinon une couleur stable."""
    from .planning import normalize  # import local : planning ne dépend pas de HA

    key = normalize(name)
    for prefix, color in _PROFILE_COLORS:
        if key.startswith(prefix):
            return color
    return _EXTRA_COLORS[sum(map(ord, key)) % len(_EXTRA_COLORS)]


_HVAC_LABELS = {
    "fr": {
        "off": "Arrêt",
        "heat": "Chauffage",
        "cool": "Climatisation",
        "heat_cool": "Chaud / froid",
        "auto": "Automatique",
        "dry": "Déshumidification",
        "fan_only": "Ventilation seule",
    },
    "en": {
        "off": "Off",
        "heat": "Heat",
        "cool": "Cool",
        "heat_cool": "Heat/Cool",
        "auto": "Auto",
        "dry": "Dry",
        "fan_only": "Fan only",
    },
}


def lang_of(language: str | None) -> str:
    return "fr" if (language or "").startswith("fr") else "en"


def describe_profile(profile: dict, language: str | None = "fr") -> str:
    """Résumé lisible des réglages, ex. « Chauffage · 20 °C · ventil. auto »."""
    lang = lang_of(language)
    parts: list[str] = []
    if (mode := profile.get(ATTR_HVAC_MODE)) is not None:
        parts.append(_HVAC_LABELS[lang].get(mode, mode))
    if (temp := profile.get(ATTR_TEMPERATURE)) is not None:
        parts.append(f"{temp:g} °C".replace(".", ",") if lang == "fr" else f"{temp:g} °C")
    fan, swing = profile.get(ATTR_FAN_MODE), profile.get(ATTR_SWING_MODE)
    if fan is not None:
        parts.append(("ventil. " if lang == "fr" else "fan ") + fan)
    if swing is not None:
        parts.append(("oscill. " if lang == "fr" else "swing ") + swing)
    if (hswing := profile.get(ATTR_SWING_HORIZONTAL_MODE)) is not None:
        parts.append(("oscill. horiz. " if lang == "fr" else "h-swing ") + hswing)
    if not parts:
        return "aucun réglage modifié" if lang == "fr" else "no setting changed"
    return " · ".join(parts)


# ---------------------------------------------------------------------- ordre d'affichage

# Home Assistant trie les clés des options à l'enregistrement : l'ordre voulu des
# groupes, profils et plannings est donc conservé dans un champ « pos ».
CONF_POS = "pos"


def _default_positions() -> dict[str, int]:
    defaults = default_options()
    return {
        key: index
        for kind in (CONF_PROFILES, CONF_PLANNINGS)
        for index, key in enumerate(defaults[kind])
    }


def ordered(items: dict[str, dict]) -> dict[str, dict]:
    """Éléments dans l'ordre voulu (« pos », sinon l'ordre des éléments fournis)."""
    defaults = _default_positions()
    indexed = list(enumerate(items.items()))
    indexed.sort(
        key=lambda e: (e[1][1].get(CONF_POS, defaults.get(e[1][0], 1000 + e[0])), e[0])
    )
    return {key: value for _, (key, value) in indexed}


def with_positions(options: dict) -> dict:
    """Numérote groupes, profils et plannings selon leur ordre actuel."""
    for kind in (CONF_GROUPS, CONF_PROFILES, CONF_PLANNINGS):
        for index, item in enumerate(options.get(kind, {}).values()):
            item[CONF_POS] = index
    return options
