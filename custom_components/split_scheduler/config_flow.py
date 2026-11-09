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
)

from .const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_SWING_HORIZONTAL_MODE,
    ATTR_SWING_MODE,
    ATTR_TEMPERATURE,
    CONF_CLIMATES,
    CONF_GROUPS,
    CONF_PLANNINGS,
    CONF_PROFILES,
    CONF_PROGRAMS,
    DOMAIN,
    HVAC_MODES,
    PROFILE_SETTINGS,
    TITLE,
    WEEKDAY_KEYS,
    default_options,
)
from .planning import ProgramError, format_day, normalize, parse_day, profiles_used

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
            return self.async_create_entry(title=TITLE, data={}, options=default_options())
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SplitSchedulerOptionsFlow()


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def _picker(items: dict[str, dict], multiple: bool = False) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(value=iid, label=item["name"]) for iid, item in items.items()],
            multiple=multiple,
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


class SplitSchedulerOptionsFlow(OptionsFlow):
    """Menus de gestion. Les modifications sont enregistrées par « Enregistrer »."""

    def __init__(self) -> None:
        self._options: dict[str, Any] | None = None
        self._edit_id: str | None = None
        self._program_target: tuple[str, str] | None = None

    @property
    def opts(self) -> dict[str, Any]:
        """Copie de travail des options."""
        if self._options is None:
            self._options = copy.deepcopy(dict(self.config_entry.options))
            for key in (CONF_GROUPS, CONF_PROFILES, CONF_PLANNINGS):
                self._options.setdefault(key, {})
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
        menu = ["groups", "profiles", "plannings"]
        if self.opts[CONF_GROUPS] and self.opts[CONF_PLANNINGS]:
            menu.append("program_pick")
        menu.append("save")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_save(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_create_entry(data=self.opts)

    def _submenu(self, step_id: str, kind: str) -> ConfigFlowResult:
        prefix = step_id[:-1]  # groups -> group_…
        menu = [f"{prefix}_add"]
        if self.opts[kind]:
            menu += [f"{prefix}_edit_pick", f"{prefix}_delete"]
        menu.append("init")
        return self.async_show_menu(step_id=step_id, menu_options=menu)

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
                self.opts[CONF_GROUPS][group_id or _new_id()] = {
                    "name": name,
                    CONF_CLIMATES: climates,
                }
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
                self.opts[CONF_PROFILES][profile_id or _new_id()] = profile
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
        for setting, list_attr in _MODE_LISTS.items():
            fields[vol.Optional(setting)] = SelectSelector(
                SelectSelectorConfig(
                    options=self._known_modes(list_attr),
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        schema = self.add_suggested_values_to_schema(vol.Schema(fields), values)
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
        current = self.opts[CONF_PLANNINGS].get(planning_id, {}) if planning_id else {}
        name = current.get("name", "")
        if user_input is not None:
            name = user_input.get("name", "").strip()
            copy_from = user_input.get("copy_from")
            if not name:
                errors["name"] = "name_required"
            elif self._name_taken(CONF_PLANNINGS, name, planning_id):
                errors["name"] = "name_taken"
            else:
                if planning_id is None:
                    source = self.opts[CONF_PLANNINGS].get(copy_from, {})
                    self.opts[CONF_PLANNINGS][_new_id()] = {
                        "name": name,
                        CONF_PROGRAMS: copy.deepcopy(source.get(CONF_PROGRAMS, {})),
                    }
                else:
                    current["name"] = name
                return await self.async_step_plannings()
        fields: dict[Any, Any] = {vol.Required("name", default=name): TextSelector()}
        if planning_id is None and self.opts[CONF_PLANNINGS]:
            fields[vol.Optional("copy_from")] = _picker(self.opts[CONF_PLANNINGS])
        return self.async_show_form(step_id=step_id, data_schema=vol.Schema(fields), errors=errors)

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
            return await self.async_step_program_edit()
        return self.async_show_form(
            step_id="program_pick",
            data_schema=vol.Schema(
                {
                    vol.Required("planning"): _picker(self.opts[CONF_PLANNINGS]),
                    vol.Required("group"): _picker(self.opts[CONF_GROUPS]),
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
                return await self.async_step_init()
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
