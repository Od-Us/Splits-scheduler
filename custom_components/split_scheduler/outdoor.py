"""Adaptation de la consigne à la température extérieure (logique pure).

Un profil peut fixer un « écart maximal avec l'extérieur » :

- climatisation (et déshumidification) : la consigne ne descend pas à plus de
  cet écart sous la température extérieure ;
- chauffage : la consigne ne monte pas à plus de cet écart au-dessus.

La température extérieure utilisée est une moyenne pondérée dans le temps sur
60 minutes ; les périodes où le capteur est indisponible sont ignorées. Sans
aucune valeur valable sur la fenêtre, il n'y a pas d'adaptation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

WINDOW = timedelta(minutes=60)
# Intervalle minimal entre deux changements de consigne dus à l'extérieur
MIN_INTERVAL = timedelta(minutes=30)
# Pas d'adaptation si un changement de profil est prévu dans moins de :
QUIET_BEFORE_CHANGE = timedelta(minutes=30)
# Changement minimal de consigne justifiant un envoi
THRESHOLD = 0.5

COOLING_MODES = ("cool", "dry")
HEATING_MODES = ("heat",)


def to_float(value: str | float | None) -> float | None:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if number == number else None  # écarte NaN


def adapt_target(
    target: float | None, mode: str | None, max_delta: float | None, outdoor: float | None
) -> float | None:
    """Consigne adaptée à l'extérieur (avant arrondi et bornage au split)."""
    if target is None or max_delta is None or outdoor is None:
        return target
    if mode in COOLING_MODES:
        return max(target, outdoor - max_delta)
    if mode in HEATING_MODES:
        return min(target, outdoor + max_delta)
    return target


def round_half(value: float) -> float:
    """Arrondi au demi-degré (pas des splits S21)."""
    return round(value * 2) / 2


@dataclass
class OutdoorAverage:
    """Moyenne glissante, pondérée dans le temps, d'un capteur de température."""

    window: timedelta = WINDOW
    samples: list[tuple[datetime, float | None]] = field(default_factory=list)

    def add(self, when: datetime, value: str | float | None) -> None:
        number = to_float(value)
        if self.samples and self.samples[-1][0] > when:
            return  # valeur plus ancienne que la dernière connue
        self.samples.append((when, number))

    def mean(self, now: datetime) -> float | None:
        start = now - self.window
        total = covered = 0.0
        for index, (when, value) in enumerate(self.samples):
            end = self.samples[index + 1][0] if index + 1 < len(self.samples) else now
            begin = max(when, start)
            if value is None or end <= begin:
                continue
            seconds = (end - begin).total_seconds()
            total += value * seconds
            covered += seconds
        if covered <= 0:
            # Valeur reçue à l'instant même : elle fait foi
            last = self.samples[-1] if self.samples else None
            if last is not None and last[1] is not None and last[0] >= start:
                return round(last[1], 1)
            return None
        return round(total / covered, 1)

    def prune(self, now: datetime) -> None:
        """Garde la dernière valeur avant la fenêtre et celles qui suivent."""
        start = now - self.window
        while len(self.samples) > 1 and self.samples[1][0] <= start:
            self.samples.pop(0)
