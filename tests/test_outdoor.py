"""Adaptation de la consigne à l'extérieur : logique pure."""

from datetime import UTC, datetime, timedelta

from custom_components.split_scheduler.outdoor import OutdoorAverage, adapt_target, round_half

T0 = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)


def at(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


def test_adapt_target_rules():
    assert adapt_target(26, "cool", 10, 39) == 29          # canicule : relevée
    assert adapt_target(26, "cool", 10, 33) == 26          # écart respecté
    assert adapt_target(26, "dry", 5, 39) == 34
    assert adapt_target(20, "heat", 25, -10) == 15         # grand froid : abaissée
    assert adapt_target(20, "heat", 25, 0) == 20
    assert adapt_target(26, "fan_only", 10, 39) == 26      # pas d'adaptation
    assert adapt_target(26, "cool", None, 39) == 26        # écart non défini
    assert adapt_target(26, "cool", 10, None) == 26        # extérieur inconnu
    assert round_half(29.26) == 29.5 and round_half(29.2) == 29.0


def test_time_weighted_mean_ignores_unavailable():
    avg = OutdoorAverage()
    avg.add(at(-90), "36")
    avg.add(at(-30), "40")
    assert avg.mean(at(0)) == 38.0                          # 30 min à 36, 30 min à 40
    avg.add(at(10), "unavailable")
    assert avg.mean(at(40)) == 40.0                         # l'indisponibilité ne compte pas
    assert avg.mean(at(80)) is None                         # plus d'une heure sans valeur
    avg.prune(at(80))
    assert len(avg.samples) == 1


def test_value_received_now_counts():
    avg = OutdoorAverage()
    avg.add(at(0), "39")
    assert avg.mean(at(0)) == 39.0
