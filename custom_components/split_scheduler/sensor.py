"""Capteurs : statut et prochain changement de chaque groupe."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SplitSchedulerConfigEntry
from .const import STATUSES
from .entity import GroupEntity, HeatPumpEntity
from .scheduler import SplitScheduler


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SplitSchedulerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    scheduler = entry.runtime_data
    entities: list[SensorEntity] = []
    for gid in scheduler.groups:
        entities += [
            StatusSensor(scheduler, gid),
            NextChangeSensor(scheduler, gid),
            TargetSensor(scheduler, gid),
        ]
        if scheduler.main_pump(gid):
            entities += [
                CompressorStartsSensor(scheduler, gid, "compressor_starts_24h", 0),
                CompressorStartsSensor(scheduler, gid, "compressor_starts_profile", 1),
                CompressorLoadSensor(scheduler, gid),
            ]
    for hpid in scheduler.heat_pumps:
        entities.append(PumpModeSensor(scheduler, hpid))
        if scheduler.pump_sources.get(hpid):
            entities += [PumpCompressorSensor(scheduler, hpid), PumpLoadSensor(scheduler, hpid)]
        if scheduler.energy_today(hpid) is not None:
            entities.append(PumpEnergySensor(scheduler, hpid))
    async_add_entities(entities)


class StatusSensor(GroupEntity, SensorEntity):
    """Programmé, dérogation, programmation désactivée ou sans programme."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUSES
    _attr_icon = "mdi:list-status"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "status")

    @property
    def native_value(self) -> str:
        return self.scheduler.status(self.group_id)


class NextChangeSensor(GroupEntity, SensorEntity):
    """Date du prochain changement de profil programmé."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "next_change")

    @property
    def native_value(self) -> datetime | None:
        return self.group_state.next_change

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"prochain_profil": self.scheduler.profile_name(self.group_state.next_profile_id)}


class TargetSensor(GroupEntity, SensorEntity):
    """Consigne du groupe, enregistrée pour les courbes de la carte."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:thermostat"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "target")

    @property
    def native_value(self) -> float | None:
        return self.scheduler.group_target(self.group_id)


class CompressorLoadSensor(GroupEntity, SensorEntity):
    """Charge du compresseur : fréquence actuelle en % de la fréquence maximale."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:gauge"

    def __init__(self, scheduler: SplitScheduler, group_id: str) -> None:
        super().__init__(scheduler, group_id, "compressor_load")

    @property
    def native_value(self) -> float | None:
        return self.scheduler.compressor_load(self.group_id)[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.scheduler.compressor_load(self.group_id)[1]


class CompressorStartsSensor(GroupEntity, SensorEntity):
    """Démarrages du compresseur par heure, en moyenne.

    Tous les splits du groupe sont supposés reliés au même compresseur.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "/h"
    _attr_icon = "mdi:sine-wave"
    _attr_suggested_display_precision = 1

    def __init__(self, scheduler: SplitScheduler, group_id: str, key: str, index: int) -> None:
        super().__init__(scheduler, group_id, key)
        self._index = index  # 0 : 24 h glissantes, 1 : depuis le dernier changement de profil

    def _average(self):
        averages = self.scheduler.compressor_averages(self.group_id)
        return averages[self._index] if averages else None

    @property
    def native_value(self) -> float | None:
        average = self._average()
        return average.per_hour if average else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        average = self._average()
        attrs: dict[str, Any] = {
            "capteurs_compresseur": self.scheduler.pump_sources.get(
                self.scheduler.main_pump(self.group_id) or "", []
            ),
        }
        if average is not None:
            attrs.update(demarrages=average.starts, duree_h=average.hours, depuis=average.since.isoformat())
        if self._index == 1:
            attrs["profil"] = self.scheduler.profile_name(self.group_state.active_profile_id)
        return attrs


class PumpModeSensor(HeatPumpEntity, SensorEntity):
    """Côté de fonctionnement de la pompe à chaleur : chauffage, froid, conflit, arrêt."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["heat", "cool", "conflict", "idle"]
    _attr_icon = "mdi:heat-pump-outline"

    def __init__(self, scheduler: SplitScheduler, pump_id: str) -> None:
        super().__init__(scheduler, pump_id, "pump_mode")

    @property
    def native_value(self) -> str:
        return self.scheduler.pump_mode(self.pump_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        pump = self.scheduler.heat_pumps[self.pump_id]
        return {
            "splits": self.scheduler.pump_modes(self.pump_id),
            "split_prioritaire": pump.get("priority"),
            "conflits": self.scheduler.pump_conflicts(self.pump_id),
            "modele": pump.get("model"),
        }


class PumpCompressorSensor(HeatPumpEntity, SensorEntity):
    """Fréquence du compresseur : médiane des capteurs des splits reliés."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:heat-pump"

    def __init__(self, scheduler: SplitScheduler, pump_id: str) -> None:
        super().__init__(scheduler, pump_id, "pump_compressor")

    @property
    def native_value(self) -> float | None:
        return self.scheduler.pump_frequency(self.pump_id)

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.scheduler.pump_unit(self.pump_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"capteurs": self.scheduler.pump_sources.get(self.pump_id, [])}


class PumpLoadSensor(HeatPumpEntity, SensorEntity):
    """Charge du compresseur de la pompe à chaleur (%)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:gauge"

    def __init__(self, scheduler: SplitScheduler, pump_id: str) -> None:
        super().__init__(scheduler, pump_id, "pump_load")

    @property
    def native_value(self) -> float | None:
        return self.scheduler.pump_load(self.pump_id)[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.scheduler.pump_load(self.pump_id)[1]


class PumpEnergySensor(HeatPumpEntity, SensorEntity):
    """Consommation électrique du jour (depuis minuit)."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2

    def __init__(self, scheduler: SplitScheduler, pump_id: str) -> None:
        super().__init__(scheduler, pump_id, "pump_energy_today")

    @property
    def native_value(self) -> float | None:
        return self.scheduler.energy_today(self.pump_id)
