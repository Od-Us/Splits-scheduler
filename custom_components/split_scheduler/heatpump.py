"""Pompes à chaleur (unités extérieures) : logique pure, sans Home Assistant.

Une pompe à chaleur alimente plusieurs splits par un même compresseur. Elle ne peut
pas chauffer et refroidir en même temps : si un split prioritaire est défini (réglage
de l'unité extérieure), son mode s'impose ; les autres splits en mode opposé restent
en veille.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import median

# Côté « chaud » ou « froid » d'un mode de split ; ventilation, arrêt et automatique : aucun.
_SIDES = {"heat": "heat", "cool": "cool", "dry": "cool"}


def mode_side(mode: str | None) -> str | None:
    """« heat », « cool » ou None (ventilation, arrêt, automatique, inconnu)."""
    return _SIDES.get(mode or "")


def find_conflicts(modes: dict[str, str | None], priority: str | None) -> dict[str, str | None]:
    """Splits en conflit de mode : {split: split prioritaire en cause (ou None)}.

    Avec un split prioritaire en chaud ou en froid : les splits du côté opposé.
    Sinon (pas de prioritaire, ou prioritaire en ventilation / arrêt) : si les deux côtés
    sont présents, tous les splits en chaud ou en froid.
    """
    sides = {eid: mode_side(mode) for eid, mode in modes.items()}
    reference = sides.get(priority) if priority else None
    if reference is not None:
        return {eid: priority for eid, side in sides.items() if side and side != reference}
    present = {side for side in sides.values() if side}
    if len(present) < 2:
        return {}
    return {eid: None for eid, side in sides.items() if side}


def shared_value(values: list[float]) -> float | None:
    """Valeur commune du compresseur à partir des capteurs de ses splits : la médiane."""
    return round(median(values), 1) if values else None


@dataclass
class EnergyToday:
    """Consommation du jour (kWh) : différence d'un compteur cumulé depuis minuit, sinon
    intégration d'une puissance (W) dans le temps."""

    day: str | None = None
    kwh: float = 0.0
    baseline: float | None = None      # compteur cumulé à minuit (kWh)
    last_power: float | None = None    # dernière puissance connue (W)
    last_time: datetime | None = None

    def _new_day(self, now: datetime) -> None:
        key = now.date().isoformat()
        if key != self.day:
            self.day, self.kwh, self.baseline = key, 0.0, None

    def from_counter(self, now: datetime, total_kwh: float) -> float:
        self._new_day(now)
        if self.baseline is None or total_kwh < self.baseline:   # premier relevé ou remise à zéro
            self.baseline = total_kwh - self.kwh
        self.kwh = round(total_kwh - self.baseline, 3)
        return self.kwh

    def from_power(self, now: datetime, watts: float | None) -> float:
        if self.last_power is not None and self.last_time is not None and now > self.last_time:
            if now.date() == self.last_time.date():
                self.kwh += self.last_power * (now - self.last_time).total_seconds() / 3_600_000
        self._new_day(now)
        self.last_power, self.last_time = watts, now
        return round(self.kwh, 3)

    def as_dict(self) -> dict:
        return {"day": self.day, "kwh": self.kwh, "baseline": self.baseline}

    @classmethod
    def from_dict(cls, data: dict | None) -> EnergyToday:
        data = data or {}
        return cls(day=data.get("day"), kwh=float(data.get("kwh") or 0.0), baseline=data.get("baseline"))


WEEK = 7 * 1440


def _changes(program: dict) -> list[tuple[int, str]]:
    """Changements d'un programme hebdomadaire en minutes depuis lundi 00:00."""
    out = []
    for day, slots in (program or {}).items():
        for hhmm, pid in slots:
            hour, minute = hhmm.split(":")
            out.append((int(day) * 1440 + int(hour) * 60 + int(minute), pid))
    return sorted(out)


def _active(changes: list[tuple[int, str]], minute: int) -> str | None:
    if not changes:
        return None
    current = changes[-1][1]  # la dernière ligne de la semaine se poursuit lundi
    for start, pid in changes:
        if start > minute:
            break
        current = pid
    return current


def program_conflicts(own: dict, other: dict, side_of) -> list[tuple[int, int, str, str]]:
    """Plages de la semaine où deux programmes demandent des côtés opposés.

    ``side_of(profile_id)`` donne « heat », « cool » ou None. Résultat :
    [(début, fin, côté du programme édité, côté de l'autre)], en minutes depuis lundi.
    """
    a, b = _changes(own), _changes(other)
    points = sorted({0, *(t for t, _ in a), *(t for t, _ in b)})
    result: list[list] = []
    for index, start in enumerate(points):
        end = points[index + 1] if index + 1 < len(points) else WEEK
        mine, theirs = side_of(_active(a, start)), side_of(_active(b, start))
        if mine and theirs and mine != theirs:
            if result and result[-1][1] == start and result[-1][2:] == [mine, theirs]:
                result[-1][1] = end
            else:
                result.append([start, end, mine, theirs])
    return [tuple(item) for item in result]
