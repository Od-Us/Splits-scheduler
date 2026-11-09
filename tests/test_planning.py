"""Tests de la logique des programmes hebdomadaires."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from custom_components.split_scheduler.planning import (
    ProgramError,
    current_occurrence,
    format_day,
    next_occurrence,
    parse_day,
)

PROFILES = {
    "confort": {"name": "Confort"},
    "eco": {"name": "Eco"},
    "hg": {"name": "Hors gel"},
    "ea": {"name": "Éco absence"},
}
PARIS = ZoneInfo("Europe/Paris")


def at(day: int, hour: int, minute: int = 0) -> datetime:
    """Novembre 2026 : le lundi 9 est un lundi."""
    return datetime(2026, 11, day, hour, minute, tzinfo=PARIS)


def test_parse_formats_and_sorting():
    assert parse_day("22:30 Eco, 6h30 confort; 7h hors  GEL\n12 eco absence", PROFILES) == [
        ["06:30", "confort"],
        ["07:00", "hg"],
        ["12:00", "ea"],
        ["22:30", "eco"],
    ]
    assert parse_day("", PROFILES) == []
    assert parse_day(None, PROFILES) == []


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("Confort", "format attendu"),
        ("25:00 Eco", "heure invalide"),
        ("06:30 Inconnu", "inconnu"),
        ("06:30 Eco, 6h30 Confort", "deux fois"),
    ],
)
def test_parse_errors(text, message):
    with pytest.raises(ProgramError, match=message):
        parse_day(text, PROFILES)


def test_format_roundtrip():
    slots = parse_day("06:30 Confort, 22:00 Hors gel", PROFILES)
    assert format_day(slots, PROFILES) == "06:30 Confort, 22:00 Hors gel"
    assert parse_day(format_day(slots, PROFILES), PROFILES) == slots


PROGRAM = {
    "0": [["06:30", "confort"], ["22:00", "eco"]],  # lundi
    "4": [["06:30", "confort"], ["23:00", "eco"]],  # vendredi
    # samedi et dimanche vides : Eco jusqu'au lundi 06:30
}


def test_current_and_next_same_day():
    occ = current_occurrence(PROGRAM, at(9, 12))
    assert (occ.profile_id, occ.start) == ("confort", at(9, 6, 30))
    nxt = next_occurrence(PROGRAM, at(9, 12))
    assert (nxt.profile_id, nxt.start) == ("eco", at(9, 22))


def test_boundary_is_inclusive_for_current():
    assert current_occurrence(PROGRAM, at(9, 22)).profile_id == "eco"
    assert next_occurrence(PROGRAM, at(9, 22)).start == at(13, 6, 30)


def test_empty_days_extend_previous_profile_across_week():
    # Dimanche 15 : le dernier créneau est vendredi 23:00
    occ = current_occurrence(PROGRAM, at(15, 10))
    assert (occ.profile_id, occ.start) == ("eco", at(13, 23))
    assert next_occurrence(PROGRAM, at(15, 10)).start == at(16, 6, 30)
    # Lundi 9 à 05:00 : on remonte au vendredi précédent
    assert current_occurrence(PROGRAM, at(9, 5)).start == datetime(2026, 11, 6, 23, tzinfo=PARIS)


def test_single_slot_week_and_empty_program():
    program = {"2": [["10:00", "hg"]]}
    assert current_occurrence(program, at(11, 10)).start == at(11, 10)
    assert next_occurrence(program, at(11, 10)).start == at(18, 10)
    assert current_occurrence({}, at(11, 10)) is None
    assert next_occurrence({}, at(11, 10)) is None
