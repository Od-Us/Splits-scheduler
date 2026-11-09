"""Logique pure des programmes hebdomadaires (sans dépendance à Home Assistant).

Un *programme* décrit, pour un groupe et un planning, les changements de
profil de la semaine. Il est stocké sous la forme :

    {"0": [["06:30", "confort"], ["08:30", "eco"]], "5": [...], ...}

où la clé est le jour (0 = lundi ... 6 = dimanche) et chaque créneau indique
l'heure à partir de laquelle un profil s'applique. Un profil reste actif
jusqu'au créneau suivant, éventuellement plusieurs jours plus tard : un jour
sans créneau prolonge donc simplement le profil de la veille.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
import unicodedata

Program = dict[str, list[list[str]]]

_SEPARATORS = re.compile(r"[,;\n]+")
# « 06:30 Confort », « 6h30 Confort », « 7h Eco », « 7 Eco », « 18.45 Boost »
_ITEM = re.compile(r"^(\d{1,2})\s*(?:[:hH.]\s*(\d{2})?)?\s+(\S.*)$")


class ProgramError(ValueError):
    """Texte de programme invalide (message destiné à l'utilisateur)."""


@dataclass(frozen=True)
class Occurrence:
    """Un créneau placé dans le temps."""

    start: datetime
    profile_id: str


def normalize(name: str) -> str:
    """Nom comparable : sans accents, sans casse, espaces réduits."""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.casefold().split())


def parse_day(text: str | None, profiles: dict[str, dict]) -> list[list[str]]:
    """Analyse la saisie d'une journée, par ex. « 06:30 Confort, 22:00 Eco ».

    Retourne les créneaux triés ``[["06:30", id_profil], ...]``.
    """
    lookup = {normalize(p["name"]): pid for pid, p in profiles.items()}
    slots: dict[str, str] = {}
    for raw in _SEPARATORS.split(text or ""):
        item = raw.strip()
        if not item:
            continue
        match = _ITEM.match(item)
        if match is None:
            raise ProgramError(f"« {item} » : format attendu « HH:MM Profil »")
        hour, minute = int(match[1]), int(match[2] or 0)
        if hour > 23 or minute > 59:
            raise ProgramError(f"« {item} » : heure invalide")
        name = match[3].strip()
        profile_id = lookup.get(normalize(name))
        if profile_id is None:
            raise ProgramError(f"« {item} » : profil « {name} » inconnu")
        key = f"{hour:02d}:{minute:02d}"
        if key in slots:
            raise ProgramError(f"{key} figure deux fois dans la même journée")
        slots[key] = profile_id
    return [[key, slots[key]] for key in sorted(slots)]


def format_day(slots: list[list[str]], profiles: dict[str, dict]) -> str:
    """Texte éditable d'une journée (inverse de :func:`parse_day`)."""
    return ", ".join(
        f"{hhmm} {profiles.get(pid, {}).get('name', pid)}" for hhmm, pid in slots
    )


def profiles_used(program: Program) -> set[str]:
    """Identifiants des profils cités dans un programme."""
    return {pid for slots in program.values() for _, pid in slots}


def _day_slots(program: Program, day: date) -> list[tuple[int, int, str]]:
    return sorted(
        (int(hhmm[:2]), int(hhmm[3:5]), pid)
        for hhmm, pid in program.get(str(day.weekday()), [])
    )


def _at(day: date, hour: int, minute: int, now: datetime) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=now.tzinfo)


def current_occurrence(program: Program, now: datetime) -> Occurrence | None:
    """Dernier créneau commencé à ``now`` (heure locale), sur 7 jours glissants."""
    for offset in range(8):
        day = now.date() - timedelta(days=offset)
        for hour, minute, pid in reversed(_day_slots(program, day)):
            start = _at(day, hour, minute, now)
            if start <= now:
                return Occurrence(start, pid)
    return None


def next_occurrence(program: Program, now: datetime) -> Occurrence | None:
    """Prochain créneau strictement après ``now`` (heure locale)."""
    for offset in range(8):
        day = now.date() + timedelta(days=offset)
        for hour, minute, pid in _day_slots(program, day):
            start = _at(day, hour, minute, now)
            if start > now:
                return Occurrence(start, pid)
    return None
