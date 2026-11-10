"""Comptage des démarrages du compresseur."""

from datetime import UTC, datetime, timedelta

from custom_components.split_scheduler.compressor import StartLog, is_running

T0 = datetime(2026, 11, 10, 8, 0, tzinfo=UTC)


def at(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


def test_is_running():
    assert is_running("42") is True
    assert is_running("0") is False and is_running("0.0") is False
    assert is_running("unavailable") is None and is_running(None) is None


def test_counts_only_off_to_on_transitions():
    log = StartLog(since=T0)
    assert not log.feed(at(0), "30")          # état de départ : pas un démarrage
    assert not log.feed(at(10), "45")         # variation de fréquence
    assert not log.feed(at(20), "0")
    assert not log.feed(at(21), "unavailable")  # ignoré
    assert log.feed(at(30), "38")             # 1er démarrage
    assert not log.feed(at(40), "0")
    assert log.feed(at(50), "40")             # 2e démarrage
    assert log.starts == [at(30), at(50)]


def test_average_per_hour_and_window():
    log = StartLog(since=T0, running=False)
    for minute in (10, 70, 130):
        log.feed(at(minute), "40")
        log.feed(at(minute + 20), "0")
    avg = log.average(at(180) - timedelta(hours=24), at(180))   # observé depuis 3 h
    assert (avg.per_hour, avg.starts, avg.hours) == (1.0, 3, 3.0)
    assert log.average(at(60), at(180)).per_hour == 1.0          # 2 démarrages en 2 h
    assert log.average(at(178), at(180)).per_hour is None         # moins de 5 minutes


def test_prune_keeps_requested_period():
    log = StartLog(since=T0, starts=[at(0), at(60), at(120)])
    log.prune(at(30), at(200))
    assert log.starts == [at(60), at(120)] and log.since == at(30)
    restored = StartLog.from_dict(log.as_dict(), datetime.fromisoformat)
    assert restored.starts == log.starts and restored.since == log.since
