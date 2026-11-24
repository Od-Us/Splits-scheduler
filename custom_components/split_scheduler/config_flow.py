"""Configuration depuis l'interface : groupes, profils, plannings et programmes."""

from __future__ import annotations

import copy
from typing import Any
import uuid

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_SWING_HORIZONTAL_MODE,
    ATTR_SWING_MODE,
    ATTR_TEMPERATURE,
    CONF_CLIMATES,
    CONF_ALLOWED,
    CONF_COMPRESSOR_MAX,
    CONF_COMPRESSORS,
    CONF_ENERGY,
    CONF_HEAT_PUMPS,
    CONF_MODEL,
    CONF_OFFSETS,
    OFFSET_COOL,
    OFFSET_HEAT,
    CONF_POWER,
    CONF_PRIORITY,
    CONF_ALWAYS_QUIET,
    CONF_OUTDOOR,
    CONF_SEND_NORMAL,
    CONF_SETTINGS,
    ATTR_OUTDOOR_DELTA,
    ATTR_QUIET,
    CONF_GROUPS,
    CONF_PLANNINGS,
    CONF_PROFILES,
    CONF_PROGRAMS,
    DOMAIN,
    HVAC_MODES,
    PROFILE_SETTINGS,
    TITLE,
    WEEKDAY_KEYS,
    allowed_profiles,
    default_options,
    describe_profile,
    ordered,
    with_positions,
    lang_of,
)
from .features import compressor_sensor, quiet_switch
from .heatpump import mode_side, program_conflicts
from .planning import ProgramError, format_day, normalize, parse_day, profiles_used
from .scheduler import detect_outdoor_sensor

# Réglage du profil -> attribut des thermostats listant les valeurs possibles
_MODE_LISTS = {
    ATTR_FAN_MODE: "fan_modes",
    ATTR_SWING_MODE: "swing_modes",
    ATTR_SWING_HORIZONTAL_MODE: "swing_horizontal_modes",
}


class SplitSchedulerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Création de l'unique entrée de l'intégration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(
                title=TITLE, data={}, options=with_positions(default_options())
            )
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SplitSchedulerOptionsFlow()


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def _picker(
    items: dict[str, dict], multiple: bool = False, mode: SelectSelectorMode = SelectSelectorMode.DROPDOWN
) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(value=iid, label=item["name"]) for iid, item in items.items()],
            multiple=multiple,
            mode=mode,
        )
    )


class SplitSchedulerOptionsFlow(OptionsFlow):
    """Menus de gestion. Les modifications sont enregistrées par « Enregistrer »."""

    def __init__(self) -> None:
        self._options: dict[str, Any] | None = None
        self._edit_id: str | None = None
        self._program_target: tuple[str, str] | None = None
        self._day = 0
        self._line: str | None = None

    @property
    def opts(self) -> dict[str, Any]:
        """Copie de travail des options."""
        if self._options is None:
            self._options = copy.deepcopy(dict(self.config_entry.options))
            for key in (CONF_GROUPS, CONF_PROFILES, CONF_PLANNINGS, CONF_HEAT_PUMPS):
                self._options[key] = ordered(self._options.get(key, {}))
        return self._options

    def _name_taken(self, kind: str, name: str, own_id: str | None) -> bool:
        wanted = normalize(name)
        return any(
            normalize(item["name"]) == wanted
            for iid, item in self.opts[kind].items()
            if iid != own_id
        )

    # ------------------------------------------------------------------ menu principal

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        menu = ["settings", "heat_pumps", "groups", "plannings", "profiles"]
        if self.opts[CONF_GROUPS] and self.opts[CONF_PLANNINGS]:
            menu.append("program_pick")
        menu.append("save")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Réglages généraux : capteur de température extérieure (commun à tous les groupes)."""
        settings = self.opts.setdefault(CONF_SETTINGS, {})
        if user_input is not None:
            if user_input.get(CONF_OUTDOOR):
                settings[CONF_OUTDOOR] = user_input[CONF_OUTDOOR]
            else:
                settings.pop(CONF_OUTDOOR, None)  # vide : détection automatique
            for key in (CONF_SEND_NORMAL, CONF_ALWAYS_QUIET):
                settings[key] = bool(user_input.get(key, False))
            return await self.async_step_init()
        climates = [eid for g in self.opts[CONF_GROUPS].values() for eid in g[CONF_CLIMATES]]
        suggested = settings.get(CONF_OUTDOOR) or detect_outdoor_sensor(self.hass, climates)
        schema = self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    vol.Optional(CONF_OUTDOOR): EntitySelector(EntitySelectorConfig(domain="sensor")),
                    vol.Optional(CONF_SEND_NORMAL, default=False): BooleanSelector(),
                    vol.Optional(CONF_ALWAYS_QUIET, default=False): BooleanSelector(),
                }
            ),
            {
                CONF_OUTDOOR: suggested,
                CONF_SEND_NORMAL: settings.get(CONF_SEND_NORMAL, False),
                CONF_ALWAYS_QUIET: settings.get(CONF_ALWAYS_QUIET, False),
            },
        )
        return self.async_show_form(step_id="settings", data_schema=schema)

    async def async_step_save(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_create_entry(data=with_positions(self.opts))

    def _submenu(self, step_id: str, kind: str) -> ConfigFlowResult:
        prefix = step_id[:-1]  # groups -> group_…
        menu = [f"{prefix}_add"]
        if self.opts[kind]:
            menu += [f"{prefix}_edit_pick", f"{prefix}_delete"]
            if kind == CONF_GROUPS:
                menu.insert(2, "split_offsets")  # décalage des consignes des splits
        menu.append("init")
        return self.async_show_menu(step_id=step_id, menu_options=menu)

    # ------------------------------------------------------------------ pompes à chaleur

    async def async_step_heat_pumps(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self._submenu("heat_pumps", CONF_HEAT_PUMPS)

    async def async_step_heat_pump_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_heat_pump_form("heat_pump_add", user_input, None)

    async def async_step_heat_pump_edit_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._edit_id = user_input["heat_pump"]
            return await self.async_step_heat_pump_edit()
        return self.async_show_form(
            step_id="heat_pump_edit_pick",
            data_schema=vol.Schema({vol.Required("heat_pump"): _picker(self.opts[CONF_HEAT_PUMPS])}),
        )

    async def async_step_heat_pump_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_heat_pump_form("heat_pump_edit", user_input, self._edit_id)

    async def _async_heat_pump_form(
        self, step_id: str, user_input: dict[str, Any] | None, pump_id: str | None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"detected": "—"}
        values = self.opts[CONF_HEAT_PUMPS].get(pump_id, {}) if pump_id else {}
        if user_input is not None:
            name = user_input.get("name", "").strip()
            climates = user_input.get(CONF_CLIMATES, [])
            priority = user_input.get(CONF_PRIORITY)
            taken = {
                eid
                for pid, pump in self.opts[CONF_HEAT_PUMPS].items()
                if pid != pump_id
                for eid in pump.get(CONF_CLIMATES, [])
            }
            if not name:
                errors["name"] = "name_required"
            elif self._name_taken(CONF_HEAT_PUMPS, name, pump_id):
                errors["name"] = "name_taken"
            elif not climates:
                errors[CONF_CLIMATES] = "climates_required"
            elif taken & set(climates):
                errors[CONF_CLIMATES] = "climate_other_pump"
            elif priority and priority not in climates:
                errors[CONF_PRIORITY] = "priority_not_member"
            else:
                pump: dict[str, Any] = {"name": name, CONF_CLIMATES: climates}
                if user_input.get(CONF_MODEL, "").strip():
                    pump[CONF_MODEL] = user_input[CONF_MODEL].strip()
                if priority:
                    pump[CONF_PRIORITY] = priority
                if user_input.get(CONF_COMPRESSORS):
                    pump[CONF_COMPRESSORS] = list(user_input[CONF_COMPRESSORS])
                if user_input.get(CONF_COMPRESSOR_MAX):
                    pump[CONF_COMPRESSOR_MAX] = float(user_input[CONF_COMPRESSOR_MAX])
                for key in (CONF_POWER, CONF_ENERGY):
                    if user_input.get(key):
                        pump[key] = user_input[key]
                self.opts[CONF_HEAT_PUMPS][pump_id or _new_id()] = pump
                return await self.async_step_heat_pumps()
            values = user_input
        detected = [s for eid in values.get(CONF_CLIMATES, []) if (s := compressor_sensor(self.hass, eid))]
        if detected:
            placeholders["detected"] = ", ".join(detected)
        schema = vol.Schema(
            {
                vol.Required("name", default=values.get("name", "")): TextSelector(),
                vol.Optional(CONF_MODEL): TextSelector(),
                vol.Required(CONF_CLIMATES, default=values.get(CONF_CLIMATES, [])): EntitySelector(
                    EntitySelectorConfig(domain="climate", multiple=True)
                ),
                vol.Optional(CONF_PRIORITY): EntitySelector(EntitySelectorConfig(domain="climate")),
                vol.Optional(CONF_COMPRESSORS): EntitySelector(
                    EntitySelectorConfig(domain="sensor", multiple=True)
                ),
                vol.Optional(CONF_COMPRESSOR_MAX): NumberSelector(
                    NumberSelectorConfig(min=1, max=15000, step=1, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_POWER): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_ENERGY): EntitySelector(
                    EntitySelectorConfig(domain="sensor")
                ),
            }
        )
        schema = self.add_suggested_values_to_schema(
            schema, {key: values.get(key) for key in (
                CONF_MODEL, CONF_PRIORITY, CONF_COMPRESSORS, CONF_COMPRESSOR_MAX, CONF_POWER, CONF_ENERGY
            )},
        )
        return self.async_show_form(
            step_id=step_id, data_schema=schema, errors=errors, description_placeholders=placeholders
        )

    async def async_step_heat_pump_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            for pid in user_input.get("heat_pumps", []):
                self.opts[CONF_HEAT_PUMPS].pop(pid, None)
            return await self.async_step_heat_pumps()
        return self.async_show_form(
            step_id="heat_pump_delete",
            data_schema=vol.Schema(
                {vol.Optional("heat_pumps", default=[]): _picker(self.opts[CONF_HEAT_PUMPS], multiple=True)}
            ),
        )

    # ------------------------------------------------------------------ groupes

    async def async_step_groups(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._submenu("groups", CONF_GROUPS)

    async def async_step_group_add(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_group_form("group_add", user_input, None)

    async def async_step_group_edit_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._edit_id = user_input["group"]
            return await self.async_step_group_edit()
        return self.async_show_form(
            step_id="group_edit_pick",
            data_schema=vol.Schema({vol.Required("group"): _picker(self.opts[CONF_GROUPS])}),
        )

    async def async_step_group_edit(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_group_form("group_edit", user_input, self._edit_id)

    async def _async_group_form(
        self, step_id: str, user_input: dict[str, Any] | None, group_id: str | None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        values = self.opts[CONF_GROUPS].get(group_id, {}) if group_id else {}
        if user_input is not None:
            name = user_input.get("name", "").strip()
            climates = user_input.get(CONF_CLIMATES, [])
            if not name:
                errors["name"] = "name_required"
            elif self._name_taken(CONF_GROUPS, name, group_id):
                errors["name"] = "name_taken"
            elif not climates:
                errors[CONF_CLIMATES] = "climates_required"
            else:
                group = {"name": name, CONF_CLIMATES: climates}
                # la position est renumérotée à l'enregistrement
                self.opts[CONF_GROUPS][group_id or _new_id()] = group
                return await self.async_step_groups()
            values = user_input
        schema = vol.Schema(
            {
                vol.Required("name", default=values.get("name", "")): TextSelector(),
                vol.Required(CONF_CLIMATES, default=values.get(CONF_CLIMATES, [])): EntitySelector(
                    EntitySelectorConfig(domain="climate", multiple=True)
                ),
            }
        )
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    def _offset_fields(self, climates: list[str]) -> dict[str, tuple[str, str]]:
        """Champs du formulaire des décalages : libellé lisible -> (split, côté)."""
        names: dict[str, str] = {}
        for eid in climates:
            state = self.hass.states.get(eid)
            name = state.name if state else eid
            names[eid] = name if list(names.values()).count(name) == 0 else f"{name} ({eid})"
        heat, cool = _TXT[self._lang]["offset_heat"], _TXT[self._lang]["offset_cool"]
        fields: dict[str, tuple[str, str]] = {}
        for eid in climates:
            fields[f"{names[eid]} · {heat}"] = (eid, OFFSET_HEAT)
            fields[f"{names[eid]} · {cool}"] = (eid, OFFSET_COOL)
        return fields

    async def async_step_split_offsets(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Décalage de la consigne envoyée à chaque split (chauffage, froid)."""
        offsets = self.opts.setdefault(CONF_OFFSETS, {})
        climates = list(dict.fromkeys(
            eid for group in self.opts[CONF_GROUPS].values() for eid in group[CONF_CLIMATES]
        ))
        fields = self._offset_fields(climates)
        if user_input is not None:
            for label, (eid, side) in fields.items():
                value = round(float(user_input.get(label) or 0) * 2) / 2   # pas de 0,5 °C
                split = dict(offsets.get(eid, {}))
                if value:
                    split[side] = value
                else:
                    split.pop(side, None)
                if split:
                    offsets[eid] = split
                else:
                    offsets.pop(eid, None)
            return await self.async_step_groups()
        selector = NumberSelector(
            NumberSelectorConfig(min=-3, max=3, step=0.5, mode=NumberSelectorMode.BOX,
                                 unit_of_measurement="°C")
        )
        schema = vol.Schema({
            vol.Optional(label, default=float(offsets.get(eid, {}).get(side, 0.0))): selector
            for label, (eid, side) in fields.items()
        })
        return self.async_show_form(step_id="split_offsets", data_schema=schema)

    async def async_step_group_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            for gid in user_input.get("groups", []):
                self.opts[CONF_GROUPS].pop(gid, None)
                for planning in self.opts[CONF_PLANNINGS].values():
                    planning.get(CONF_PROGRAMS, {}).pop(gid, None)
            return await self.async_step_groups()
        return self.async_show_form(
            step_id="group_delete",
            data_schema=vol.Schema(
                {vol.Optional("groups", default=[]): _picker(self.opts[CONF_GROUPS], multiple=True)}
            ),
        )

    # ------------------------------------------------------------------ profils

    async def async_step_profiles(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._submenu("profiles", CONF_PROFILES)

    async def async_step_profile_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_profile_form("profile_add", user_input, None)

    async def async_step_profile_edit_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._edit_id = user_input["profile"]
            return await self.async_step_profile_edit()
        return self.async_show_form(
            step_id="profile_edit_pick",
            data_schema=vol.Schema({vol.Required("profile"): _picker(self.opts[CONF_PROFILES])}),
        )

    async def async_step_profile_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_profile_form("profile_edit", user_input, self._edit_id)

    def _climate_states(self) -> list:
        """États des thermostats des groupes (ou de toute la maison s'il n'y en a pas)."""
        climates = {eid for g in self.opts[CONF_GROUPS].values() for eid in g[CONF_CLIMATES]}
        states = [self.hass.states.get(eid) for eid in sorted(climates)]
        return [st for st in states if st] or self.hass.states.async_all("climate")

    def _known_modes(self, list_attr: str) -> list[str]:
        """Valeurs annoncées par les thermostats (ex. fan_modes de Faikout)."""
        found: list[str] = []
        for state in self._climate_states():
            for value in state.attributes.get(list_attr) or []:
                if value not in found:
                    found.append(str(value))
        return found

    async def _async_profile_form(
        self, step_id: str, user_input: dict[str, Any] | None, profile_id: str | None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        values = self.opts[CONF_PROFILES].get(profile_id, {}) if profile_id else {}
        if user_input is not None:
            name = user_input.get("name", "").strip()
            if not name:
                errors["name"] = "name_required"
            elif self._name_taken(CONF_PROFILES, name, profile_id):
                errors["name"] = "name_taken"
            else:
                profile: dict[str, Any] = {"name": name}
                for setting in PROFILE_SETTINGS:
                    value = user_input.get(setting)
                    if value not in (None, ""):
                        profile[setting] = (
                            float(value) if setting == ATTR_TEMPERATURE else str(value)
                        )
                if user_input.get(ATTR_QUIET) in ("on", "off"):
                    profile[ATTR_QUIET] = user_input[ATTR_QUIET] == "on"
                if user_input.get(ATTR_OUTDOOR_DELTA) not in (None, ""):
                    profile[ATTR_OUTDOOR_DELTA] = float(user_input[ATTR_OUTDOOR_DELTA])
                new_id = profile_id or _new_id()
                if profile_id is None:  # nouveau profil : autorisé dans tous les plannings
                    for planning in self.opts[CONF_PLANNINGS].values():
                        if CONF_ALLOWED in planning:
                            planning[CONF_ALLOWED].append(new_id)
                self.opts[CONF_PROFILES][new_id] = profile
                return await self.async_step_profiles()
            values = user_input

        # Seuls les modes annoncés par les splits (Faikout : pas de « auto »)
        known = self._known_modes("hvac_modes")
        hvac_modes = [m for m in HVAC_MODES if m in known or m == values.get(ATTR_HVAC_MODE)]
        fields: dict[Any, Any] = {
            vol.Required("name"): TextSelector(),
            vol.Optional(ATTR_HVAC_MODE): SelectSelector(
                SelectSelectorConfig(
                    options=hvac_modes if known else HVAC_MODES,
                    translation_key="hvac_mode",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(ATTR_TEMPERATURE): NumberSelector(
                NumberSelectorConfig(
                    min=5, max=35, step=0.5, mode=NumberSelectorMode.BOX, unit_of_measurement="°C"
                )
            ),
        }
        fields[vol.Optional(ATTR_OUTDOOR_DELTA)] = NumberSelector(
            NumberSelectorConfig(
                min=1, max=30, step=0.5, mode=NumberSelectorMode.BOX, unit_of_measurement="°C"
            )
        )
        # Unité extérieure silencieuse : si au moins un split a l'interrupteur Faikout
        if values.get(ATTR_QUIET) is not None or any(
            quiet_switch(self.hass, eid) for g in self.opts[CONF_GROUPS].values() for eid in g[CONF_CLIMATES]
        ):
            fields[vol.Optional(ATTR_QUIET)] = SelectSelector(
                SelectSelectorConfig(
                    options=["on", "off"], translation_key="quiet_state", mode=SelectSelectorMode.DROPDOWN
                )
            )
        for setting, list_attr in _MODE_LISTS.items():
            fields[vol.Optional(setting)] = SelectSelector(
                SelectSelectorConfig(
                    options=self._known_modes(list_attr),
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        shown = dict(values)
        if isinstance(shown.get(ATTR_QUIET), bool):
            shown[ATTR_QUIET] = "on" if shown[ATTR_QUIET] else "off"
        schema = self.add_suggested_values_to_schema(vol.Schema(fields), shown)
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            errors=errors,
            description_placeholders={"limits": self._temperature_limits()},
        )

    def _temperature_limits(self) -> str:
        """Plage de consigne acceptée par tous les splits, ex. « 16 à 32 °C, pas de 0.5 °C »."""
        lows, highs, steps = [], [], set()
        for state in self._climate_states():
            attrs = state.attributes
            if attrs.get("min_temp") is not None and attrs.get("max_temp") is not None:
                lows.append(float(attrs["min_temp"]))
                highs.append(float(attrs["max_temp"]))
            if attrs.get("target_temp_step"):
                steps.add(float(attrs["target_temp_step"]))
        if not lows:
            return "?"
        text = f"{max(lows):g} à {min(highs):g} °C"
        if steps:
            text += f", pas de {max(steps):g} °C"
        return text

    async def async_step_profile_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"used": ""}
        if user_input is not None:
            selected = set(user_input.get("profiles", []))
            used = {
                self.opts[CONF_PROFILES][pid]["name"]
                for planning in self.opts[CONF_PLANNINGS].values()
                for program in planning.get(CONF_PROGRAMS, {}).values()
                for pid in profiles_used(program) & selected
            }
            if used:
                errors["base"] = "profile_in_use"
                placeholders["used"] = ", ".join(sorted(used))
            elif len(selected) >= len(self.opts[CONF_PROFILES]):
                errors["base"] = "keep_one_profile"
            else:
                for pid in selected:
                    self.opts[CONF_PROFILES].pop(pid, None)
                    for planning in self.opts[CONF_PLANNINGS].values():
                        if pid in planning.get(CONF_ALLOWED, []):
                            planning[CONF_ALLOWED].remove(pid)
                return await self.async_step_profiles()
        return self.async_show_form(
            step_id="profile_delete",
            data_schema=vol.Schema(
                {
                    vol.Optional("profiles", default=[]): _picker(
                        self.opts[CONF_PROFILES], multiple=True
                    )
                }
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

    # ------------------------------------------------------------------ plannings

    async def async_step_plannings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self._submenu("plannings", CONF_PLANNINGS)

    async def async_step_planning_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_planning_form("planning_add", user_input, None)

    async def async_step_planning_edit_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._edit_id = user_input["planning"]
            return await self.async_step_planning_edit()
        return self.async_show_form(
            step_id="planning_edit_pick",
            data_schema=vol.Schema({vol.Required("planning"): _picker(self.opts[CONF_PLANNINGS])}),
        )

    async def async_step_planning_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_planning_form("planning_edit", user_input, self._edit_id)

    async def _async_planning_form(
        self, step_id: str, user_input: dict[str, Any] | None, planning_id: str | None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"used": ""}
        profiles = self.opts[CONF_PROFILES]
        current = self.opts[CONF_PLANNINGS].get(planning_id, {}) if planning_id else {}
        name = current.get("name", "")
        allowed = allowed_profiles(current, profiles)
        if user_input is not None:
            name = user_input.get("name", "").strip()
            copy_from = user_input.get("copy_from")
            allowed = [pid for pid in profiles if pid in user_input.get(CONF_ALLOWED, [])]
            used = {
                pid
                for program in current.get(CONF_PROGRAMS, {}).values()
                for pid in profiles_used(program)
            }
            if planning_id is None and copy_from in self.opts[CONF_PLANNINGS]:
                source = self.opts[CONF_PLANNINGS][copy_from]
                used = {
                    pid for program in source.get(CONF_PROGRAMS, {}).values()
                    for pid in profiles_used(program)
                }
            if not name:
                errors["name"] = "name_required"
            elif self._name_taken(CONF_PLANNINGS, name, planning_id):
                errors["name"] = "name_taken"
            elif not allowed:
                errors[CONF_ALLOWED] = "allowed_required"
            elif missing := sorted(profiles[pid]["name"] for pid in used - set(allowed) if pid in profiles):
                errors[CONF_ALLOWED] = "allowed_in_use"
                placeholders["used"] = ", ".join(missing)
            else:
                if planning_id is None:
                    source = self.opts[CONF_PLANNINGS].get(copy_from, {})
                    self.opts[CONF_PLANNINGS][_new_id()] = {
                        "name": name,
                        CONF_PROGRAMS: copy.deepcopy(source.get(CONF_PROGRAMS, {})),
                        CONF_ALLOWED: allowed,
                    }
                else:
                    current["name"] = name
                    current[CONF_ALLOWED] = allowed
                return await self.async_step_plannings()
        fields: dict[Any, Any] = {
            vol.Required("name", default=name): TextSelector(),
            vol.Required(CONF_ALLOWED, default=allowed): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=pid, label=self._profile_label(pid))
                        for pid in profiles
                    ],
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                )
            ),
        }
        if planning_id is None and self.opts[CONF_PLANNINGS]:
            fields[vol.Optional("copy_from")] = _picker(self.opts[CONF_PLANNINGS])
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_planning_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = set(user_input.get("plannings", []))
            if len(selected) >= len(self.opts[CONF_PLANNINGS]):
                errors["base"] = "keep_one_planning"
            else:
                for pid in selected:
                    self.opts[CONF_PLANNINGS].pop(pid, None)
                return await self.async_step_plannings()
        return self.async_show_form(
            step_id="planning_delete",
            data_schema=vol.Schema(
                {
                    vol.Optional("plannings", default=[]): _picker(
                        self.opts[CONF_PLANNINGS], multiple=True
                    )
                }
            ),
            errors=errors,
        )

    # ------------------------------------------------------------------ programmes hebdomadaires

    async def async_step_program_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._program_target = (user_input["planning"], user_input["group"])
            return await self.async_step_program_week()
        # Par défaut : le dernier couple choisi, sinon le premier planning et le premier groupe
        planning, group = self._program_target or (
            next(iter(self.opts[CONF_PLANNINGS])),
            next(iter(self.opts[CONF_GROUPS])),
        )
        if planning not in self.opts[CONF_PLANNINGS] or group not in self.opts[CONF_GROUPS]:
            planning, group = next(iter(self.opts[CONF_PLANNINGS])), next(iter(self.opts[CONF_GROUPS]))
        return self.async_show_form(
            step_id="program_pick",
            data_schema=vol.Schema(
                {
                    vol.Required("planning", default=planning): _picker(self.opts[CONF_PLANNINGS]),
                    vol.Required("group", default=group): _picker(self.opts[CONF_GROUPS]),
                }
            ),
        )

    async def async_step_program_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._program_target is not None
        planning_id, group_id = self._program_target
        planning = self.opts[CONF_PLANNINGS][planning_id]
        profiles = self.opts[CONF_PROFILES]
        programs = planning.setdefault(CONF_PROGRAMS, {})
        errors: dict[str, str] = {}
        problems: list[str] = []

        if user_input is not None:
            program: dict[str, list[list[str]]] = {}
            for index, day in enumerate(WEEKDAY_KEYS):
                try:
                    slots = parse_day(user_input.get(day), profiles)
                    allowed = allowed_profiles(planning, profiles)
                    if refused := [profiles[pid]["name"] for _, pid in slots if pid not in allowed]:
                        raise ProgramError(
                            f"profil « {refused[0]} » non autorisé dans le planning {planning['name']}"
                        )
                except ProgramError as err:
                    errors[day] = "invalid_program"
                    problems.append(str(err))
                    continue
                if slots:
                    program[str(index)] = slots
            if not errors:
                for day in user_input.get("copy_monday_to", []):
                    index = str(WEEKDAY_KEYS.index(day))
                    if "0" in program:
                        program[index] = copy.deepcopy(program["0"])
                    else:
                        program.pop(index, None)
                programs[group_id] = program
                return await self.async_step_program_week()
            suggested = dict(user_input)
        else:
            current = programs.get(group_id, {})
            suggested = {
                day: format_day(current.get(str(index), []), profiles)
                for index, day in enumerate(WEEKDAY_KEYS)
            }

        fields: dict[Any, Any] = {
            vol.Optional(day): TextSelector(TextSelectorConfig(multiline=False))
            for day in WEEKDAY_KEYS
        }
        fields[vol.Optional("copy_monday_to")] = SelectSelector(
            SelectSelectorConfig(
                options=WEEKDAY_KEYS[1:],
                translation_key="weekday",
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        )
        schema = self.add_suggested_values_to_schema(vol.Schema(fields), suggested)
        return self.async_show_form(
            step_id="program_edit",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "planning": planning["name"],
                "group": self.opts[CONF_GROUPS][group_id]["name"],
                "profiles": ", ".join(p["name"] for p in profiles.values()),
                "problems": "\n".join(f"- {p}" for p in problems),
            },
        )

    # ------------------------------------------------------------------ édition ligne par ligne

    @property
    def _lang(self) -> str:
        return lang_of(self.hass.config.language)

    def _program(self) -> dict[str, list[list[str]]]:
        """Programme (copie de travail) du planning et du groupe choisis."""
        assert self._program_target is not None
        planning_id, group_id = self._program_target
        programs = self.opts[CONF_PLANNINGS][planning_id].setdefault(CONF_PROGRAMS, {})
        return programs.setdefault(group_id, {})

    def _target_placeholders(self) -> dict[str, str]:
        assert self._program_target is not None
        planning_id, group_id = self._program_target
        return {
            "group": self.opts[CONF_GROUPS][group_id]["name"],
            "planning": self.opts[CONF_PLANNINGS][planning_id]["name"],
            "day": _DAY_NAMES[self._lang][self._day],
        }

    def _heat_pump_warnings(self) -> str:
        """Plages où ce programme chauffe pendant que le split prioritaire de la même pompe
        à chaleur refroidit (ou l'inverse), dans le même planning."""
        assert self._program_target is not None
        planning_id, group_id = self._program_target
        programs = self.opts[CONF_PLANNINGS][planning_id].get(CONF_PROGRAMS, {})
        profiles, lang = self.opts[CONF_PROFILES], self._lang
        txt = _TXT[lang]
        own_climates = set(self.opts[CONF_GROUPS][group_id][CONF_CLIMATES])

        def side_of(pid: str | None) -> str | None:
            return mode_side(profiles.get(pid, {}).get(ATTR_HVAC_MODE)) if pid else None

        lines: list[str] = []
        for pump in self.opts.get(CONF_HEAT_PUMPS, {}).values():
            members = set(pump.get(CONF_CLIMATES, []))
            if not own_climates & members:
                continue
            references = [pump[CONF_PRIORITY]] if pump.get(CONF_PRIORITY) else sorted(members - own_climates)
            for gid, group in self.opts[CONF_GROUPS].items():
                split = next((eid for eid in references if eid in group[CONF_CLIMATES]), None)
                if gid == group_id or split is None or split in own_climates:
                    continue
                state = self.hass.states.get(split)
                split_name = state.name if state else split
                for start, end, mine, theirs in program_conflicts(
                    programs.get(group_id, {}), programs.get(gid, {}), side_of
                )[:4]:
                    day = _DAY_NAMES[lang][start // 1440][:3]
                    lines.append(
                        txt["hp_conflict" if pump.get(CONF_PRIORITY) else "hp_conflict_shared"].format(
                            day=day,
                            start=f"{start % 1440 // 60:02d}:{start % 60:02d}",
                            end="24:00" if end % 1440 == 0 and end > start else f"{end % 1440 // 60:02d}:{end % 60:02d}",
                            mine=txt[f"side_{mine}"],
                            theirs=txt[f"side_{theirs}"],
                            split=split_name,
                            group=group["name"],
                            pump=pump["name"],
                        )
                    )
        if not lines:
            return ""
        return "\n\n" + txt["hp_conflict_title"] + "\n" + "\n".join(f"- {line}" for line in lines[:8])

    def _allowed_here(self) -> list[str]:
        """Profils autorisés dans le planning dont on édite le programme."""
        assert self._program_target is not None
        planning = self.opts[CONF_PLANNINGS][self._program_target[0]]
        return allowed_profiles(planning, self.opts[CONF_PROFILES])

    def _profile_label(self, profile_id: str) -> str:
        profile = self.opts[CONF_PROFILES].get(profile_id, {"name": profile_id})
        summary = describe_profile(profile, self._lang)
        if normalize(summary) == normalize(profile["name"]):
            return profile["name"]  # « Arrêt » plutôt que « Arrêt — Arrêt »
        return f"{profile['name']} — {summary}"

    def _inherited(self, day: int) -> tuple[int, str, str] | None:
        """Dernier créneau avant le début du jour ``day`` (jour, heure, profil)."""
        program = self._program()
        for back in range(1, 8):
            previous = (day - back) % 7
            if slots := program.get(str(previous)):
                return previous, slots[-1][0], slots[-1][1]
        return None

    def _set_day(self, day: int, slots: dict[str, str]) -> None:
        program = self._program()
        if slots:
            program[str(day)] = [[hhmm, slots[hhmm]] for hhmm in sorted(slots)]
        else:
            program.pop(str(day), None)

    async def async_step_program_week(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        lang, program, profiles = self._lang, self._program(), self.opts[CONF_PROFILES]
        placeholders = self._target_placeholders()
        for index, day in enumerate(WEEKDAY_KEYS):
            if slots := program.get(str(index)):
                placeholders[day] = format_day(slots, profiles).replace(", ", " · ")
            elif (inherited := self._inherited(index)) is not None:
                from_day, hhmm, pid = inherited
                name = profiles.get(pid, {}).get("name", pid)
                placeholders[day] = _TXT[lang]["inherited"].format(
                    profile=name, day=_DAY_NAMES[lang][from_day].lower(), time=hhmm
                )
            else:
                placeholders[day] = _TXT[lang]["empty_week"]
        placeholders["warnings"] = self._heat_pump_warnings()
        return self.async_show_menu(
            step_id="program_week",
            menu_options=[f"day_{day}" for day in WEEKDAY_KEYS]
            + ["program_copy", "program_copy_groups", "program_edit", "init"],
            description_placeholders=placeholders,
        )

    async def _async_open_day(self, day: int) -> ConfigFlowResult:
        self._day = day
        return await self.async_step_program_day()

    async def async_step_day_mon(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_open_day(0)

    async def async_step_day_tue(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_open_day(1)

    async def async_step_day_wed(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_open_day(2)

    async def async_step_day_thu(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_open_day(3)

    async def async_step_day_fri(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_open_day(4)

    async def async_step_day_sat(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_open_day(5)

    async def async_step_day_sun(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_open_day(6)

    async def async_step_program_day(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Lignes d'une journée : choisir une ligne à modifier, ou une action."""
        txt = _TXT[self._lang]
        slots = self._program().get(str(self._day), [])
        if user_input is not None:
            choice = user_input.get("choice", "add")
            if choice.startswith("line:"):
                self._line = choice[5:]
                return await self.async_step_program_line()
            if choice == "add":
                self._line = None
                return await self.async_step_program_line()
            if choice == "copy":
                return await self.async_step_program_day_copy()
            if choice == "clear":
                self._set_day(self._day, {})
                return await self.async_step_program_day()
            return await self.async_step_program_week()

        options = [
            SelectOptionDict(value=f"line:{hhmm}", label=f"{hhmm}  {self._profile_label(pid)}")
            for hhmm, pid in slots
        ]
        actions = ["add", "copy"] + (["clear"] if slots else []) + ["back"]
        options += [SelectOptionDict(value=a, label=txt[f"action_{a}"]) for a in actions]
        inherited = self._inherited(self._day)
        placeholders = self._target_placeholders()
        if inherited is not None:
            profile = self.opts[CONF_PROFILES].get(inherited[2], {}).get("name", inherited[2])
            placeholders["start"] = txt["start"].format(profile=profile)
        else:
            placeholders["start"] = txt["start_none"]
        return self.async_show_form(
            step_id="program_day",
            data_schema=vol.Schema(
                {
                    vol.Required("choice", default="add"): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                    )
                }
            ),
            description_placeholders=placeholders,
        )

    async def async_step_program_line(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ajout ou modification d'une ligne : heure et profil."""
        txt = _TXT[self._lang]
        slots = dict(self._program().get(str(self._day), []))
        editing = self._line if self._line in slots else None
        errors: dict[str, str] = {}
        if user_input is not None:
            if editing is not None and user_input.get("delete"):
                slots.pop(editing)
                self._set_day(self._day, slots)
                return await self.async_step_program_day()
            hhmm = _normalize_time(str(user_input.get("time", "")))
            profile_id = user_input.get("profile")
            if hhmm is None:
                errors["time"] = "time_required"
            elif profile_id not in self._allowed_here():
                errors["profile"] = "profile_required"
            elif hhmm != editing and hhmm in slots:
                errors["time"] = "time_taken"
            else:
                if editing is not None:
                    slots.pop(editing)
                slots[hhmm] = profile_id
                self._set_day(self._day, slots)
                return await self.async_step_program_day()

        fields: dict[Any, Any] = {
            vol.Required("time"): TextSelector(TextSelectorConfig(type=TextSelectorType.TIME)),
            vol.Required("profile"): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=pid, label=self._profile_label(pid))
                        for pid in self._allowed_here()
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            ),
        }
        if editing is not None:
            fields[vol.Optional("delete", default=False)] = BooleanSelector()
        suggested = (
            dict(user_input)
            if user_input is not None
            else ({"time": editing, "profile": slots[editing]} if editing else {})
        )
        placeholders = self._target_placeholders()
        placeholders["line"] = (
            txt["line_edit"].format(time=editing) if editing else txt["line_new"]
        )
        return self.async_show_form(
            step_id="program_line",
            data_schema=self.add_suggested_values_to_schema(vol.Schema(fields), suggested),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_program_day_copy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Copier le jour en cours vers d'autres jours."""
        if user_input is not None:
            self._copy_day(self._day, user_input.get("days", []))
            return await self.async_step_program_day()
        others = [day for i, day in enumerate(WEEKDAY_KEYS) if i != self._day]
        return self.async_show_form(
            step_id="program_day_copy",
            data_schema=vol.Schema(
                {vol.Optional("days", default=[]): _weekday_picker(others, multiple=True)}
            ),
            description_placeholders=self._target_placeholders(),
        )

    async def async_step_program_copy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Depuis la semaine : copier un jour choisi vers d'autres jours."""
        if user_input is not None:
            self._copy_day(WEEKDAY_KEYS.index(user_input["source"]), user_input.get("days", []))
            return await self.async_step_program_week()
        return self.async_show_form(
            step_id="program_copy",
            data_schema=vol.Schema(
                {
                    vol.Required("source", default="mon"): _weekday_picker(WEEKDAY_KEYS),
                    vol.Optional("days", default=[]): _weekday_picker(WEEKDAY_KEYS, multiple=True),
                }
            ),
            description_placeholders=self._target_placeholders(),
        )

    async def async_step_program_copy_groups(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Copier tout le programme de la semaine vers d'autres groupes et/ou plannings."""
        assert self._program_target is not None
        source_planning, source_group = self._program_target
        errors: dict[str, str] = {}
        placeholders = self._target_placeholders()
        if user_input is not None:
            plannings = user_input.get("plannings") or []
            groups = user_input.get("groups") or []
            targets = [
                (plid, gid)
                for plid in plannings
                for gid in groups
                if (plid, gid) != (source_planning, source_group)
            ]
            used = {pid for slots in self._program().values() for _, pid in slots}
            refused = []
            for plid in plannings:
                allowed = allowed_profiles(self.opts[CONF_PLANNINGS][plid], self.opts[CONF_PROFILES])
                missing = sorted(used - set(allowed))
                if missing:
                    names = ", ".join(self.opts[CONF_PROFILES].get(pid, {}).get("name", pid) for pid in missing)
                    refused.append(f"{self.opts[CONF_PLANNINGS][plid]['name']} ({names})")
            if not targets:
                errors["base"] = "copy_target_required"
            elif refused:
                errors["base"] = "copy_not_allowed"
                placeholders["refused"] = " ; ".join(refused)
            else:
                week = copy.deepcopy(self._program())
                for plid, gid in targets:
                    programs = self.opts[CONF_PLANNINGS][plid].setdefault(CONF_PROGRAMS, {})
                    programs[gid] = copy.deepcopy(week)
                return await self.async_step_program_week()
        defaults = user_input or {"plannings": [source_planning], "groups": []}
        return self.async_show_form(
            step_id="program_copy_groups",
            data_schema=vol.Schema(
                {
                    vol.Optional("plannings", default=defaults.get("plannings", [])): _picker(
                        self.opts[CONF_PLANNINGS], multiple=True, mode=SelectSelectorMode.LIST
                    ),
                    vol.Optional("groups", default=defaults.get("groups", [])): _picker(
                        self.opts[CONF_GROUPS], multiple=True, mode=SelectSelectorMode.LIST
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"refused": "", **placeholders},
        )

    def _copy_day(self, source: int, days: list[str]) -> None:
        slots = dict(self._program().get(str(source), []))
        for day in days:
            target = WEEKDAY_KEYS.index(day)
            if target != source:
                self._set_day(target, dict(slots))


def _normalize_time(value: str) -> str | None:
    """« 8:30 », « 08:30 » ou « 08:30:00 » -> « 08:30 » ; None si invalide."""
    parts = value.strip().split(":")
    if len(parts) < 2 or not all(p.isdigit() for p in parts[:2]):
        return None
    hour, minute = int(parts[0]), int(parts[1])
    if hour > 23 or minute > 59:
        return None
    return f"{hour:02d}:{minute:02d}"


def _weekday_picker(days: list[str], multiple: bool = False) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=days,
            translation_key="weekday",
            multiple=multiple,
            mode=SelectSelectorMode.LIST,
        )
    )


_DAY_NAMES = {
    "fr": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}

_TXT = {
    "fr": {
        "inherited": "Aucun changement — {profile} depuis {day} {time}",
        "empty_week": "Aucun changement",
        "action_add": "Ajouter une ligne",
        "action_copy": "Copier ce jour vers d'autres jours",
        "action_clear": "Vider la journée",
        "action_back": "Retour à la semaine",
        "start": "À minuit, le profil actif est **{profile}** (dernière ligne des jours précédents).",
        "start_none": "Ce programme ne contient encore aucune ligne.",
        "line_new": "nouvelle ligne",
        "line_edit": "ligne de {time}",
        "offset_heat": "décalage chauffage",
        "offset_cool": "décalage froid",
        "hp_conflict_title": "⚠️ **Conflit avec la pompe à chaleur** — ces splits resteront en veille :",
        "hp_conflict": "{day} {start}–{end} : {mine} ici, {theirs} pour **{split}** ({group}, prioritaire sur {pump})",
        "hp_conflict_shared": "{day} {start}–{end} : {mine} ici, {theirs} pour **{split}** ({group}, même pompe {pump}) — définissez un split prioritaire",
        "side_heat": "chauffage",
        "side_cool": "froid",
    },
    "en": {
        "inherited": "No change — {profile} since {day} {time}",
        "empty_week": "No change",
        "action_add": "Add a line",
        "action_copy": "Copy this day to other days",
        "action_clear": "Clear the day",
        "action_back": "Back to the week",
        "start": "At midnight the active profile is **{profile}** (last line of previous days).",
        "start_none": "This program has no line yet.",
        "line_new": "new line",
        "line_edit": "line at {time}",
        "offset_heat": "heating offset",
        "offset_cool": "cooling offset",
        "hp_conflict_title": "⚠️ **Heat pump conflict** — these splits will stay idle:",
        "hp_conflict": "{day} {start}–{end}: {mine} here, {theirs} for **{split}** ({group}, priority on {pump})",
        "hp_conflict_shared": "{day} {start}–{end}: {mine} here, {theirs} for **{split}** ({group}, same pump {pump}) — set a priority split",
        "side_heat": "heating",
        "side_cool": "cooling",
    },
}
