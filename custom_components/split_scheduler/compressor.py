"""Comptage des démarrages du compresseur (logique pure, sans Home Assistant).

Tous les splits d'un groupe sont considérés comme reliés au même compresseur
(même unité extérieure) : un seul capteur de compresseur est suivi par groupe,
par exemple le capteur « Compressor » (fréquence en Hz) publié par Faikout.
Un démarrage est un passage de 0 à une valeur positive ; les états
indisponibles ou non numériques sont ignorés.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# En dessous de cette durée d'observation, une moyenne horaire n'a pas de sens.
MIN_WINDOW = timedelta(minutes=5)
# Les démarrages sont conservés au plus 7 jours.
MAX_KEEP = timedelta(days=7)


def is_running(value: str | None) -> bool | None:
    """Compresseur en marche ? None si la valeur est inconnue."""
    try:
        return float(value) > 0  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


@dataclass
class Average:
    """Moyenne horaire des démarrages sur une période."""

    per_hour: float | None
    starts: int
    hours: float
    since: datetime


@dataclass
class StartLog:
    """Démarrages horodatés d'un compresseur."""

    since: datetime  # début de l'observation
    starts: list[datetime] = field(default_factory=list)
    running: bool | None = None

    def feed(self, when: datetime, value: str | None) -> bool:
        """Nouvelle valeur du capteur ; True si c'est un démarrage."""
        running = is_running(value)
        if running is None:
            return False
        started = running and self.running is False
        self.running = running
        if started:
            self.starts.append(when)
        return started

    def average(self, start: datetime, now: datetime) -> Average:
        """Démarrages par heure entre ``start`` (borné au début de l'observation) et ``now``."""
        begin = max(start, self.since)
        hours = max((now - begin).total_seconds() / 3600, 0.0)
        count = len(self.starts) - bisect_left(self.starts, begin)
        per_hour = round(count / hours, 1) if now - begin >= MIN_WINDOW else None
        return Average(per_hour, count, round(hours, 1), begin)

    def prune(self, keep_from: datetime, now: datetime) -> None:
        """Oublie les démarrages trop anciens (au plus 7 jours)."""
        limit = max(keep_from, now - MAX_KEEP)
        self.starts = self.starts[bisect_left(self.starts, limit):]
        if self.since < limit:
            self.since = limit

    def as_dict(self) -> dict:
        return {"since": self.since.isoformat(), "starts": [s.isoformat() for s in self.starts]}

    @classmethod
    def from_dict(cls, data: dict, parse) -> StartLog:
        since = parse(data.get("since"))
        starts = sorted(d for d in (parse(s) for s in data.get("starts", [])) if d)
        return cls(since=since, starts=starts) if since else None  # type: ignore[return-value]
