/*
 * Carte « Programmation des splits » pour Home Assistant.
 *
 * Fournie et chargée automatiquement par l'intégration split_scheduler.
 * Configuration (éditeur visuel disponible) :
 *
 *   type: custom:split-scheduler-card
 *   title: Chauffage
 *   show_global_planning: true
 *   show_timeline: true
 *   groups:                      # vide = tous les groupes, réglages par défaut
 *     - group: <id du groupe>
 *       temperature_entity: sensor.salon_temperature   # remplace celle du split
 *       sensors: [sensor.salon_humidite]
 *       show_planning: true
 *       show_profiles: true
 *       manual: [temperature, fan_mode, swing_mode, hvac_mode]
 *       compressor: [avg_24h, avg_profile]   # démarrages du compresseur par heure
 */

const CARD_VERSION = "1.2.0";
const ICON_URL = new URL("icon.png", import.meta.url).href;

const GROUP_DEFAULTS = {
  temperature_entity: "",
  sensors: [],
  show_planning: true,
  show_profiles: true,
  manual: ["temperature", "fan_mode"],
  compressor: [],
};

const I18N = {
  fr: {
    card_name: "Programmation des splits",
    card_desc: "Groupes de splits : profil, planning, dérogations et réglages.",
    all_planning: "Planning de tous les groupes",
    setpoint: "Consigne",
    ambient: "Ambiance",
    split: "Split",
    today: "Aujourd'hui",
    next: "Prochain",
    no_change: "Aucun changement prévu",
    modify: "Modifier",
    hide: "Masquer les réglages",
    planning: "Planning",
    profile: "Profil",
    until: "jusqu'à",
    manual: "Réglage manuel",
    manual_all: "tous les splits du groupe",
    fan: "Ventilateur",
    swing: "Oscillation",
    mode: "Mode",
    programming: "Programmation",
    resume: "Reprendre",
    reactivate: "Réactiver",
    override_text: "Dérogation en cours.",
    override_until: "Reprise automatique à {time} ({profile}).",
    disabled_text: "Programmation désactivée : aucun changement automatique.",
    no_program_text: "Aucun programme pour ce groupe dans ce planning.",
    status: { scheduled: "Programmé", override: "Dérogation", disabled: "Désactivée", no_program: "Aucun programme" },
    hvac: { off: "Arrêt", heat: "Chauffage", cool: "Climatisation", heat_cool: "Chaud / froid", auto: "Automatique", dry: "Déshumidification", fan_only: "Ventilation seule" },
    not_loaded: "L'intégration « Programmation des splits » n'est pas chargée.",
    unknown_group: "Groupe introuvable",
    lower: "Baisser la consigne",
    raise: "Monter la consigne",
    // éditeur
    e_title: "Titre (facultatif)",
    e_global: "Afficher le choix du planning pour tous les groupes",
    e_timeline: "Afficher la frise du programme du jour",
    e_groups: "Groupes affichés",
    e_add: "Ajouter un groupe",
    e_temp: "Température ambiante affichée (vide : celle du split)",
    e_sensors: "Capteurs supplémentaires (sous l'état)",
    e_show_planning: "Partie « Modifier » : choix du planning du groupe",
    e_show_profiles: "Partie « Modifier » : choix d'un profil",
    e_manual: "Partie « Modifier » : réglages manuels",
    e_up: "Monter",
    e_down: "Descendre",
    e_remove: "Retirer",
    e_all: "Aucun groupe choisi : tous les groupes sont affichés avec les réglages par défaut.",
    m_temperature: "Consigne",
    m_fan_mode: "Vitesse du ventilateur",
    m_swing_mode: "Oscillation",
    m_hvac_mode: "Mode (chauffage, climatisation…)",
    compressor: "Compresseur",
    c_24h: "Compresseur (24 h)",
    c_profile: "Compresseur depuis {profile}",
    c_unit: "dém./h",
    c_detail: "{starts} démarrage(s) en {hours} h",
    e_compressor: "Démarrages du compresseur par heure (compresseur commun à tous les splits du groupe)",
    e_compressor_missing: "Aucun capteur de compresseur pour ce groupe : indiquez-le dans la configuration du groupe (Paramètres › Programmation des splits › Configurer › Groupes).",
    e_compressor_ok: "Tous les splits du groupe sont considérés comme reliés au même compresseur.",
    o_avg_24h: "Moyenne sur les 24 dernières heures",
    o_avg_profile: "Moyenne depuis le dernier changement de profil",
  },
  en: {
    card_name: "Split scheduler",
    card_desc: "Split groups: profile, planning, overrides and settings.",
    all_planning: "Planning of all groups",
    setpoint: "Target",
    ambient: "Room",
    split: "Split",
    today: "Today",
    next: "Next",
    no_change: "No scheduled change",
    modify: "Modify",
    hide: "Hide settings",
    planning: "Planning",
    profile: "Profile",
    until: "until",
    manual: "Manual setting",
    manual_all: "all splits of the group",
    fan: "Fan",
    swing: "Swing",
    mode: "Mode",
    programming: "Scheduling",
    resume: "Resume",
    reactivate: "Enable",
    override_text: "Override in progress.",
    override_until: "Schedule resumes at {time} ({profile}).",
    disabled_text: "Scheduling disabled: no automatic change.",
    no_program_text: "No program for this group in this planning.",
    status: { scheduled: "Scheduled", override: "Override", disabled: "Disabled", no_program: "No program" },
    hvac: { off: "Off", heat: "Heat", cool: "Cool", heat_cool: "Heat/Cool", auto: "Auto", dry: "Dry", fan_only: "Fan only" },
    not_loaded: "The Split scheduler integration is not loaded.",
    unknown_group: "Unknown group",
    lower: "Lower target",
    raise: "Raise target",
    e_title: "Title (optional)",
    e_global: "Show the planning selector for all groups",
    e_timeline: "Show today's program timeline",
    e_groups: "Displayed groups",
    e_add: "Add a group",
    e_temp: "Room temperature shown (empty: the split's)",
    e_sensors: "Extra sensors (below the status)",
    e_show_planning: "“Modify” part: group planning selector",
    e_show_profiles: "“Modify” part: profile selector",
    e_manual: "“Modify” part: manual settings",
    e_up: "Up",
    e_down: "Down",
    e_remove: "Remove",
    e_all: "No group selected: all groups are shown with default settings.",
    m_temperature: "Target temperature",
    m_fan_mode: "Fan speed",
    m_swing_mode: "Swing",
    m_hvac_mode: "Mode (heat, cool…)",
    compressor: "Compressor",
    c_24h: "Compressor (24 h)",
    c_profile: "Compressor since {profile}",
    c_unit: "starts/h",
    c_detail: "{starts} start(s) in {hours} h",
    e_compressor: "Compressor starts per hour (compressor shared by all splits of the group)",
    e_compressor_missing: "No compressor sensor for this group: set it in the group configuration (Settings › Split scheduler › Configure › Groups).",
    e_compressor_ok: "All splits of the group are assumed to share the same compressor.",
    o_avg_24h: "Average over the last 24 hours",
    o_avg_profile: "Average since the last profile change",
  },
};

const STATUS_COLORS = {
  scheduled: "var(--success-color, #43a047)",
  override: "var(--warning-color, #ffa000)",
  disabled: "var(--disabled-color, #9e9e9e)",
  no_program: "var(--disabled-color, #9e9e9e)",
};

const ICONS = {
  check: "M5 12l5 5 9-10",
  alert: "M12 8v5M12 16.5v.5M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z",
  pause: "M9 9v6M15 9v6",
  thermo: "M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z",
  drop: "M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z",
  gauge: "M4 16a8 8 0 1 1 16 0M12 16l4-5",
  down: "M6 9l6 6 6-6",
  up: "M6 15l6-6 6 6",
  wave: "M2 12c2-6 4-6 5 0s3 6 5 0 3-6 5 0 3 6 5 0",
};

function lang(hass) {
  return (hass?.locale?.language || hass?.language || "fr").startsWith("fr") ? "fr" : "en";
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function svg(path, size = 16) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${path}"></path></svg>`;
}

function toMinutes(hhmm) {
  return Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5));
}

const WEEKDAYS = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 };

/** Jour (0 = lundi), minutes et date du jour dans le fuseau de Home Assistant. */
function zonedNow(timeZone, date = new Date()) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone, weekday: "short", year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23",
    }).formatToParts(date).map((p) => [p.type, p.value]),
  );
  return {
    weekday: WEEKDAYS[parts.weekday],
    minutes: Number(parts.hour) * 60 + Number(parts.minute),
    day: `${parts.year}-${parts.month}-${parts.day}`,
  };
}

/** Segments [{from, to, profile}] du programme d'une journée (minutes). */
function daySegments(program, weekday) {
  let current = null;
  for (let back = 1; back <= 7 && current === null; back++) {
    const slots = program[String((weekday - back + 7) % 7)];
    if (slots && slots.length) current = slots[slots.length - 1][1];
  }
  const segments = [];
  let from = 0;
  for (const [hhmm, profile] of program[String(weekday)] || []) {
    const at = toMinutes(hhmm);
    if (at > from) segments.push({ from, to: at, profile: current });
    current = profile;
    from = at;
  }
  if (from < 1440) segments.push({ from, to: 1440, profile: current });
  return segments;
}

function mix(color, percent, base = "transparent") {
  return `color-mix(in srgb, ${color} ${percent}%, ${base})`;
}

// ---------------------------------------------------------------------------- carte

class SplitSchedulerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._expanded = new Set();
    this._pending = {};
    this._timers = {};
    this._signature = "";
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("change", (ev) => this._onChange(ev));
  }

  static getConfigElement() {
    return document.createElement("split-scheduler-card-editor");
  }

  static async getStubConfig(hass) {
    const config = { show_global_planning: true, show_timeline: true, groups: [] };
    try {
      const info = await hass.callWS({ type: "split_scheduler/info" });
      config.groups = info.groups.map((g) => ({ group: g.id, ...GROUP_DEFAULTS }));
    } catch (_err) {
      /* tous les groupes par défaut */
    }
    return config;
  }

  setConfig(config) {
    if (!config) throw new Error("Configuration invalide");
    this._config = { show_global_planning: true, show_timeline: true, groups: [], ...config };
    this._signature = "";
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._info && !this._loading) this._load();
    this._render();
  }

  getCardSize() {
    return 2 + 4 * (this._groupConfigs().length || 1);
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  connectedCallback() {
    // Le programme du jour avance : on rafraîchit le repère de l'heure et les données.
    this._tick = setInterval(() => {
      this._signature = "";
      this._render();
    }, 60000);
    this._reload = setInterval(() => this._load(), 300000);
  }

  disconnectedCallback() {
    clearInterval(this._tick);
    clearInterval(this._reload);
  }

  async _load() {
    if (!this._hass) return;
    this._loading = true;
    try {
      this._info = await this._hass.callWS({ type: "split_scheduler/info" });
      this._error = null;
    } catch (err) {
      this._error = err?.code === "not_loaded" ? "not_loaded" : err?.message || String(err);
    }
    this._loading = false;
    this._signature = "";
    this._render();
  }

  _t(key) {
    return I18N[lang(this._hass)][key] ?? key;
  }

  _groupConfigs() {
    const info = this._info;
    const wanted = this._config?.groups || [];
    if (!info) return [];
    const list = wanted.length ? wanted : info.groups.map((g) => ({ group: g.id }));
    return list.map((cfg) => ({ ...GROUP_DEFAULTS, ...cfg, info: info.groups.find((g) => g.id === cfg.group) }));
  }

  _state(entityId) {
    return entityId ? this._hass.states[entityId] : undefined;
  }

  _profile(name) {
    return this._info?.profiles.find((p) => p.name === name);
  }

  _fmt(value, digits = 1) {
    const n = Number(value);
    if (!Number.isFinite(n)) return "–";
    return new Intl.NumberFormat(this._hass?.locale?.language || this._hass?.language || "fr", {
      minimumFractionDigits: digits, maximumFractionDigits: digits,
    }).format(n);
  }

  _time(iso) {
    const tz = this._info?.time_zone || this._hass?.config?.time_zone;
    const date = new Date(iso);
    const loc = this._hass?.locale?.language || this._hass?.language || "fr";
    const hhmm = new Intl.DateTimeFormat(loc, { hour: "2-digit", minute: "2-digit", timeZone: tz }).format(date);
    if (zonedNow(tz, date).day === zonedNow(tz).day) return hhmm;
    const day = new Intl.DateTimeFormat(loc, { weekday: "short", timeZone: tz }).format(date);
    return `${day} ${hhmm}`;
  }

  /** Signature des états utiles : on ne redessine que si elle change. */
  _computeSignature() {
    const ids = [this._info?.global_planning];
    for (const g of this._groupConfigs()) {
      if (!g.info) continue;
      ids.push(...Object.values(g.info.entities), ...g.info.climates, g.temperature_entity, ...(g.sensors || []));
    }
    const parts = ids.filter(Boolean).map((id) => {
      const s = this._hass.states[id];
      return s ? `${id}:${s.last_updated}` : id;
    });
    return [JSON.stringify(this._config), this._error, JSON.stringify(this._pending), [...this._expanded].join(), lang(this._hass), ...parts].join("|");
  }

  _render() {
    if (!this._config || !this._hass) return;
    const signature = this._computeSignature();
    if (signature === this._signature) return;
    this._signature = signature;
    const focused = this.shadowRoot.activeElement?.id;
    this.shadowRoot.innerHTML = `<style>${CARD_CSS}</style>${this._renderBody()}`;
    if (focused) this.shadowRoot.getElementById(focused)?.focus();
  }

  _renderBody() {
    if (this._error) {
      const text = this._error === "not_loaded" ? this._t("not_loaded") : esc(this._error);
      return `<ha-card><div class="alert">${text}</div></ha-card>`;
    }
    if (!this._info) return `<ha-card><div class="loading"></div></ha-card>`;
    const groups = this._groupConfigs();
    return `
      <div class="wrap">
        ${this._renderHeader()}
        <div class="grid">${groups.map((g) => this._renderGroup(g)).join("")}</div>
      </div>`;
  }

  _renderHeader() {
    const cfg = this._config;
    const tz = this._info.time_zone;
    const loc = this._hass?.locale?.language || this._hass?.language || "fr";
    const now = new Intl.DateTimeFormat(loc, { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit", timeZone: tz }).format(new Date());
    const title = cfg.title
      ? `<div class="title"><img src="${ICON_URL}" alt=""><div><h1>${esc(cfg.title)}</h1><span class="muted">${esc(now)}</span></div></div>`
      : "";
    let global = "";
    const globalState = this._state(this._info.global_planning);
    if (cfg.show_global_planning && globalState) {
      global = `
        <div class="global" role="group" aria-label="${esc(this._t("all_planning"))}">
          <span class="caption">${esc(this._t("all_planning"))}</span>
          ${this._segmented(globalState.attributes.options || [], globalState.state, "global-planning", "", "large")}
        </div>`;
    }
    if (!title && !global) return "";
    return `<header class="head">${title}${global}</header>`;
  }

  _segmented(options, current, action, group, size = "") {
    return `<div class="seg ${size}">${options
      .map((o) => `<button type="button" class="${o === current ? "on" : ""}" aria-pressed="${o === current}" data-action="${action}" data-group="${esc(group)}" data-value="${esc(o)}">${esc(o)}</button>`)
      .join("")}</div>`;
  }

  _renderGroup(g) {
    if (!g.info) {
      return `<article class="group"><div class="alert">${esc(this._t("unknown_group"))} (${esc(g.group)})</div></article>`;
    }
    const e = g.info.entities;
    const status = this._state(e.status)?.state || "no_program";
    const profileState = this._state(e.profile);
    const planningState = this._state(e.planning);
    const nextState = this._state(e.next_change);
    const climate = this._state(g.info.climates[0]);
    const attrs = climate?.attributes || {};
    const profile = this._profile(profileState?.state);
    const color = profile?.color || "var(--disabled-color, #9e9e9e)";
    const mode = climate?.state;
    const hvac = I18N[lang(this._hass)].hvac;

    const pending = this._pending[g.group];
    const target = pending ?? attrs.temperature;
    let big;
    if (mode === "off") big = `<span class="big word">${esc(hvac.off)}</span>`;
    else if ((target === undefined || target === null) && attrs.target_temp_low != null && attrs.target_temp_high != null) {
      big = `<span class="big range">${this._fmt(attrs.target_temp_low)}–${this._fmt(attrs.target_temp_high)}<small> °C</small></span>`;
    } else if (target === undefined || target === null) big = `<span class="big word">–</span>`;
    else big = `<span class="big">${this._fmt(target)}<small> °C</small></span>`;

    const statusIcon = { scheduled: ICONS.check, override: ICONS.alert, disabled: ICONS.pause }[status] || ICONS.pause;
    const statusColor = STATUS_COLORS[status] || STATUS_COLORS.disabled;

    // Température ambiante : capteur choisi, sinon celle du split
    let ambient = "";
    const tempEntity = this._state(g.temperature_entity);
    if (tempEntity && !Number.isNaN(Number(tempEntity.state))) {
      ambient = this._chip(ICONS.thermo, this._t("ambient"), `${this._fmt(tempEntity.state)} ${esc(tempEntity.attributes.unit_of_measurement || "°C")}`);
    } else if (attrs.current_temperature !== undefined && attrs.current_temperature !== null) {
      ambient = this._chip(ICONS.thermo, this._t(g.temperature_entity ? "split" : "ambient"), `${this._fmt(attrs.current_temperature)} °C`);
    }
    const extra = (g.sensors || []).map((id) => this._sensorChip(id)).join("") + this._compressorChips(g);

    const nextIso = nextState && !["unknown", "unavailable"].includes(nextState.state) ? nextState.state : null;
    const nextProfile = nextState?.attributes?.prochain_profil;

    let banner = "";
    if (status === "override") {
      const until = nextIso ? " " + this._t("override_until").replace("{time}", esc(this._time(nextIso))).replace("{profile}", esc(nextProfile || "")) : "";
      banner = `<div class="banner warn"><span>${esc(this._t("override_text"))}${until}</span><button type="button" class="filled" data-action="resume" data-group="${esc(g.group)}">${esc(this._t("resume"))}</button></div>`;
    } else if (status === "disabled") {
      banner = `<div class="banner"><span>${esc(this._t("disabled_text"))}</span><button type="button" class="outlined" data-action="programming-on" data-group="${esc(g.group)}">${esc(this._t("reactivate"))}</button></div>`;
    } else if (status === "no_program") {
      banner = `<div class="banner"><span>${esc(this._t("no_program_text"))}</span></div>`;
    }

    const timeline = this._config.show_timeline && status !== "disabled" && status !== "no_program"
      ? this._renderTimeline(g, planningState?.state, nextIso, nextProfile) : "";

    const hasEdit = g.show_planning || g.show_profiles || (g.manual || []).length || e.programming;
    const open = this._expanded.has(g.group);
    const editToggle = hasEdit
      ? `<button type="button" class="expander" aria-expanded="${open}" data-action="expand" data-group="${esc(g.group)}">${esc(this._t(open ? "hide" : "modify"))} ${svg(open ? ICONS.up : ICONS.down, 18)}</button>`
      : "";

    return `
      <article class="group" aria-label="${esc(g.info.name)}">
        <div class="row between">
          <h2>${esc(g.info.name)}</h2>
          <span class="status" style="background:${mix(statusColor, 18)};color:${mix(statusColor, 70, "var(--primary-text-color)")}">${svg(statusIcon, 14)}${esc(I18N[lang(this._hass)].status[status] || status)}</span>
        </div>
        <div class="row between end">
          <div class="col"><span class="muted small">${esc(this._t("setpoint"))}</span>${big}</div>
          <div class="col right">
            ${profile ? `<span class="pchip" style="background:${mix(color, 20)};color:${mix(color, 55, "var(--primary-text-color)")}"><i style="background:${color}"></i>${esc(profile.name)}</span>` : ""}
            <span class="muted small">${esc(hvac[mode] || "")}</span>
          </div>
        </div>
        ${ambient || extra ? `<div class="chips">${ambient}${extra}</div>` : ""}
        ${banner}
        ${timeline}
        ${editToggle}
        ${open ? this._renderEdit(g, { profileState, planningState, climate, nextIso }) : ""}
      </article>`;
  }

  _chip(icon, label, value) {
    return `<span class="chip">${svg(icon, 16)}${label ? `${esc(label)} ` : ""}<strong>${value}</strong></span>`;
  }

  _compressorChips(g) {
    const wanted = g.compressor || [];
    const e = g.info.entities;
    const chips = [];
    for (const [key, entity] of [["avg_24h", e.starts_24h], ["avg_profile", e.starts_profile]]) {
      const s = wanted.includes(key) ? this._state(entity) : undefined;
      if (!s) continue;
      const a = s.attributes;
      const label = key === "avg_24h"
        ? this._t("c_24h")
        : this._t("c_profile").replace("{profile}", a.profil || "");
      const value = ["unknown", "unavailable"].includes(s.state) ? "–" : `${this._fmt(s.state)} ${this._t("c_unit")}`;
      const title = a.demarrages !== undefined
        ? this._t("c_detail").replace("{starts}", a.demarrages).replace("{hours}", this._fmt(a.duree_h)) : "";
      chips.push(`<span class="chip" title="${esc(title)}">${svg(ICONS.wave, 16)}${esc(label)} <strong>${esc(value)}</strong></span>`);
    }
    return chips.join("");
  }

  _sensorChip(entityId) {
    const s = this._state(entityId);
    if (!s) return this._chip(ICONS.gauge, entityId, "–");
    const dc = s.attributes.device_class;
    const icon = dc === "temperature" ? ICONS.thermo : dc === "humidity" ? ICONS.drop : ICONS.gauge;
    const value = typeof this._hass.formatEntityState === "function"
      ? this._hass.formatEntityState(s)
      : `${s.state} ${s.attributes.unit_of_measurement || ""}`;
    return this._chip(icon, s.attributes.friendly_name || entityId, esc(value));
  }

  _renderTimeline(g, planningName, nextIso, nextProfile) {
    const planning = this._info.plannings.find((p) => p.name === planningName);
    const program = planning?.programs?.[g.group] || {};
    const now = zonedNow(this._info.time_zone);
    const segments = daySegments(program, now.weekday);
    const bars = segments.map((s) => {
      const p = this._info.profiles.find((x) => x.id === s.profile);
      const width = ((s.to - s.from) / 14.4).toFixed(3);
      return `<span style="width:${width}%;background:${p ? p.color : "var(--divider-color)"}" title="${esc(p ? p.name : "")}"></span>`;
    }).join("");
    const next = nextIso
      ? `${esc(this._t("next"))} : <strong>${esc(this._time(nextIso))} ${esc(nextProfile || "")}</strong>`
      : esc(this._t("no_change"));
    return `
      <div class="timeline">
        <div class="row between small muted"><span>${esc(this._t("today"))}</span><span>${next}</span></div>
        <div class="bar">${bars}<b style="left:${((now.minutes / 1440) * 100).toFixed(2)}%"></b></div>
        <div class="ticks"><span>0 h</span><span>6 h</span><span>12 h</span><span>18 h</span><span>24 h</span></div>
      </div>`;
  }

  _renderEdit(g, { profileState, planningState, climate, nextIso }) {
    const parts = [];
    const gid = esc(g.group);
    if (g.show_planning && planningState) {
      parts.push(`<div class="col gap8"><span>${esc(this._t("planning"))}</span>${this._segmented(planningState.attributes.options || [], planningState.state, "planning", g.group, "full")}</div>`);
    }
    if (g.show_profiles && profileState) {
      const until = nextIso ? ` <span class="muted">(${esc(this._t("until"))} ${esc(this._time(nextIso))})</span>` : "";
      const chips = (profileState.attributes.options || []).map((name) => {
        const p = this._profile(name);
        const on = name === profileState.state;
        return `<button type="button" class="pbtn ${on ? "on" : ""}" aria-pressed="${on}" data-action="profile" data-group="${gid}" data-value="${esc(name)}" title="${esc(p?.summary || "")}"><i style="background:${p?.color || "var(--disabled-color)"}"></i>${esc(name)}</button>`;
      }).join("");
      parts.push(`<div class="col gap8"><span>${esc(this._t("profile"))}${until}</span><div class="wrapchips">${chips}</div></div>`);
    }
    const manual = g.manual || [];
    if (manual.length && climate) {
      const a = climate.attributes;
      const n = g.info.climates.length;
      const rows = [];
      if (manual.includes("temperature") && a.temperature !== undefined && climate.state !== "off") {
        const value = this._pending[g.group] ?? a.temperature;
        rows.push(`<div class="row between"><span>${esc(this._t("setpoint"))}</span><div class="stepper">
          <button type="button" class="round" aria-label="${esc(this._t("lower"))}" data-action="temp" data-group="${gid}" data-value="-1">−</button>
          <span class="val">${this._fmt(value)} °C</span>
          <button type="button" class="round" aria-label="${esc(this._t("raise"))}" data-action="temp" data-group="${gid}" data-value="1">+</button></div></div>`);
      }
      if (manual.includes("hvac_mode") && (a.hvac_modes || []).length) {
        const hvac = I18N[lang(this._hass)].hvac;
        rows.push(this._selectRow(`mode-${g.group}`, this._t("mode"), "hvac_mode", g.group, a.hvac_modes, climate.state, (m) => hvac[m] || m));
      }
      if (manual.includes("fan_mode") && (a.fan_modes || []).length) {
        rows.push(this._selectRow(`fan-${g.group}`, this._t("fan"), "fan_mode", g.group, a.fan_modes, a.fan_mode));
      }
      if (manual.includes("swing_mode") && (a.swing_modes || []).length) {
        rows.push(`<div class="row between"><span>${esc(this._t("swing"))}</span>${this._segmented(a.swing_modes, a.swing_mode, "swing_mode", g.group)}</div>`);
      }
      if (rows.length) {
        const who = n > 1 ? ` <span class="muted">(${esc(this._t("manual_all"))})</span>` : "";
        parts.push(`<div class="col gap10"><span>${esc(this._t("manual"))}${who}</span>${rows.join("")}</div>`);
      }
    }
    const sw = this._state(g.info.entities.programming);
    if (sw) {
      const on = sw.state === "on";
      parts.push(`<div class="row between sep"><span>${esc(this._t("programming"))}</span><button type="button" role="switch" class="switch ${on ? "on" : ""}" aria-checked="${on}" aria-label="${esc(this._t("programming"))}" data-action="programming-toggle" data-group="${gid}"><i></i></button></div>`);
    }
    return `<div class="edit">${parts.join("")}</div>`;
  }

  _selectRow(id, label, action, group, options, current, labelOf = (x) => x) {
    return `<div class="row between"><label for="${esc(id)}">${esc(label)}</label>
      <select id="${esc(id)}" data-action="${action}" data-group="${esc(group)}">${options
        .map((o) => `<option value="${esc(o)}" ${o === current ? "selected" : ""}>${esc(labelOf(o))}</option>`)
        .join("")}</select></div>`;
  }

  _group(gid) {
    return this._groupConfigs().find((g) => g.group === gid);
  }

  async _call(promise) {
    try {
      await promise;
    } catch (err) {
      this._error = err?.message || String(err);
      this._signature = "";
      this._render();
      setTimeout(() => { this._error = null; this._signature = ""; this._render(); }, 5000);
    }
  }

  _onClick(ev) {
    const el = ev.target.closest("button[data-action]");
    if (!el) return;
    const { action, group, value } = el.dataset;
    const g = group ? this._group(group) : null;
    const e = g?.info?.entities || {};
    const hass = this._hass;
    switch (action) {
      case "global-planning":
        this._call(hass.callService("select", "select_option", { entity_id: this._info.global_planning, option: value }));
        break;
      case "planning":
        this._call(hass.callService("select", "select_option", { entity_id: e.planning, option: value }));
        break;
      case "profile":
        this._call(hass.callService("select", "select_option", { entity_id: e.profile, option: value }));
        break;
      case "resume":
        this._call(hass.callService("button", "press", { entity_id: e.resume }));
        break;
      case "programming-on":
        this._call(hass.callService("switch", "turn_on", { entity_id: e.programming }));
        break;
      case "programming-toggle":
        this._call(hass.callService("switch", "toggle", { entity_id: e.programming }));
        break;
      case "expand":
        if (this._expanded.has(group)) this._expanded.delete(group);
        else this._expanded.add(group);
        this._render();
        break;
      case "temp":
        this._stepTemperature(g, Number(value));
        break;
      case "swing_mode":
        this._manual(group, { swing_mode: value });
        break;
      default:
    }
  }

  _onChange(ev) {
    const el = ev.target.closest("select[data-action]");
    if (!el) return;
    this._manual(el.dataset.group, { [el.dataset.action]: el.value });
  }

  _manual(group, settings) {
    this._call(this._hass.callWS({ type: "split_scheduler/manual", group_id: group, ...settings }));
  }

  /** +/- : on regroupe les appuis rapprochés en un seul envoi. */
  _stepTemperature(g, direction) {
    const climate = this._state(g.info.climates[0]);
    if (!climate) return;
    const a = climate.attributes;
    const step = Number(a.target_temp_step) || 0.5;
    const base = this._pending[g.group] ?? Number(a.temperature);
    let value = Math.round((base + direction * step) / step) * step;
    if (a.min_temp !== undefined) value = Math.max(value, Number(a.min_temp));
    if (a.max_temp !== undefined) value = Math.min(value, Number(a.max_temp));
    this._pending[g.group] = Number(value.toFixed(2));
    this._render();
    clearTimeout(this._timers[g.group]);
    this._timers[g.group] = setTimeout(async () => {
      await this._call(this._hass.callWS({ type: "split_scheduler/manual", group_id: g.group, temperature: this._pending[g.group] }));
      setTimeout(() => { delete this._pending[g.group]; this._render(); }, 8000);
    }, 1200);
  }
}

const CARD_CSS = `
  :host { display: block; }
  .wrap { display: flex; flex-direction: column; gap: 16px; padding: 8px; }
  .head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px 16px; }
  .title { display: flex; align-items: center; gap: 12px; }
  .title img { width: 44px; height: 44px; }
  h1 { margin: 0; font-size: 24px; font-weight: 500; color: var(--primary-text-color); }
  h2 { margin: 0; font-size: 19px; font-weight: 500; color: var(--primary-text-color); }
  .global { display: flex; flex-direction: column; gap: 6px; }
  .caption { font-size: 12px; letter-spacing: .3px; text-transform: uppercase; color: var(--secondary-text-color); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 330px), 1fr)); gap: 16px; align-items: start; }
  .group {
    background: var(--ha-card-background, var(--card-background-color, #fff));
    border-radius: var(--ha-card-border-radius, 12px);
    border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color, #e0e0e0));
    box-shadow: var(--ha-card-box-shadow, none);
    padding: 16px; display: flex; flex-direction: column; gap: 12px;
    color: var(--primary-text-color); font-size: 14px;
  }
  .row { display: flex; align-items: center; gap: 12px; }
  .between { justify-content: space-between; }
  .end { align-items: flex-end; }
  .col { display: flex; flex-direction: column; gap: 4px; }
  .col.right { align-items: flex-end; }
  .gap8 { gap: 8px; } .gap10 { gap: 10px; }
  .muted { color: var(--secondary-text-color); }
  .small { font-size: 12.5px; }
  .big { font-size: 48px; font-weight: 400; line-height: 1; letter-spacing: -1px; }
  .big small { font-size: 20px; letter-spacing: 0; color: var(--secondary-text-color); }
  .big.word { font-size: 30px; letter-spacing: 0; }
  .big.range { font-size: 36px; letter-spacing: -.5px; }
  .status { display: inline-flex; align-items: center; gap: 6px; height: 26px; padding: 0 10px; border-radius: 13px; font-size: 12.5px; font-weight: 500; white-space: nowrap; }
  .pchip { display: inline-flex; align-items: center; gap: 8px; height: 30px; padding: 0 12px; border-radius: 15px; font-size: 14.5px; font-weight: 500; }
  .pchip i, .pbtn i { width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { display: inline-flex; align-items: center; gap: 7px; min-height: 32px; padding: 0 10px; border-radius: 10px; background: var(--secondary-background-color, #f4f6f8); color: var(--secondary-text-color); font-size: 13px; }
  .chip strong { color: var(--primary-text-color); font-weight: 500; }
  .banner { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 12px; background: var(--secondary-background-color, #f1f3f4); font-size: 13.5px; line-height: 19px; }
  .banner span { flex: 1; }
  .banner.warn { background: ${mix("var(--warning-color, #ffa000)", 16)}; }
  .timeline { display: flex; flex-direction: column; gap: 5px; }
  .bar { position: relative; display: flex; height: 12px; border-radius: 6px; overflow: hidden; }
  .bar b { position: absolute; top: 0; bottom: 0; width: 3px; margin-left: -1px; background: var(--primary-text-color); border-radius: 2px; }
  .ticks { display: flex; justify-content: space-between; font-size: 11px; color: var(--secondary-text-color); }
  button { font: inherit; cursor: pointer; color: inherit; }
  .expander { display: flex; align-items: center; justify-content: center; gap: 6px; min-height: 44px; border: 0; border-top: 1px solid var(--divider-color); background: none; color: var(--primary-color); font-weight: 500; margin: 0 -4px -6px; }
  .edit { display: flex; flex-direction: column; gap: 16px; padding: 12px; border-radius: 12px; background: var(--secondary-background-color, #f7f8fa); }
  .seg { display: inline-flex; flex-wrap: wrap; gap: 2px; padding: 3px; border-radius: 18px; background: ${mix("var(--primary-text-color)", 8)}; }
  .seg button { min-height: 32px; min-width: 44px; padding: 0 12px; border: 0; border-radius: 16px; background: none; font-size: 13px; color: var(--primary-text-color); }
  .seg button.on { background: var(--card-background-color, #fff); color: var(--primary-color); font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,.2); }
  .seg.large button { min-height: 40px; padding: 0 16px; border-radius: 20px; font-size: 14px; }
  .seg.large { border-radius: 23px; }
  .seg.full { display: flex; flex-wrap: nowrap; }
  .seg.full button { flex: 1 1 0; min-width: 0; padding: 0 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  @media (max-width: 600px) {
    .global { width: 100%; }
    .global .seg { display: flex; }
    .global .seg button { flex: 1 1 auto; padding: 0 10px; }
  }
  .wrapchips { display: flex; flex-wrap: wrap; gap: 8px; }
  .pbtn { display: inline-flex; align-items: center; gap: 7px; min-height: 36px; padding: 0 12px; border-radius: 18px; border: 1px solid var(--divider-color); background: var(--card-background-color, #fff); font-size: 13px; }
  .pbtn.on { border: 2px solid var(--primary-color); background: ${mix("var(--primary-color)", 14, "var(--card-background-color, #fff)")}; }
  .stepper { display: flex; align-items: center; gap: 4px; }
  .round { width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--divider-color); background: var(--card-background-color, #fff); font-size: 22px; line-height: 1; }
  .val { min-width: 78px; text-align: center; font-size: 19px; font-weight: 500; }
  select { min-height: 40px; min-width: 140px; padding: 0 10px; border-radius: 10px; border: 1px solid var(--divider-color); background: var(--card-background-color, #fff); color: var(--primary-text-color); font: inherit; }
  .sep { padding-top: 10px; border-top: 1px solid var(--divider-color); }
  .switch { position: relative; width: 52px; height: 32px; border-radius: 16px; border: 2px solid var(--secondary-text-color); background: none; padding: 0; }
  .switch i { position: absolute; top: 6px; left: 6px; width: 16px; height: 16px; border-radius: 50%; background: var(--secondary-text-color); transition: all .15s; }
  .switch.on { background: var(--primary-color); border-color: var(--primary-color); }
  .switch.on i { left: 24px; top: 2px; width: 24px; height: 24px; background: #fff; }
  .filled { min-height: 40px; padding: 0 16px; border-radius: 20px; border: 0; background: var(--primary-color); color: var(--text-primary-color, #fff); font-weight: 500; white-space: nowrap; }
  .outlined { min-height: 40px; padding: 0 16px; border-radius: 20px; border: 1px solid var(--primary-color); background: none; color: var(--primary-color); font-weight: 500; white-space: nowrap; }
  .alert { padding: 16px; color: var(--error-color, #db4437); }
  .loading { height: 120px; }
  button:focus-visible, select:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
`;

// ---------------------------------------------------------------------------- éditeur

class SplitSchedulerCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._info && !this._loading) this._load();
    for (const form of this.shadowRoot.querySelectorAll("ha-form")) form.hass = hass;
  }

  setConfig(config) {
    this._config = { show_global_planning: true, show_timeline: true, groups: [], ...config };
    this._build();
  }

  async _load() {
    this._loading = true;
    try {
      this._info = await this._hass.callWS({ type: "split_scheduler/info" });
    } catch (_err) {
      this._info = { groups: [] };
    }
    this._loading = false;
    this._build();
  }

  _t(key) {
    return I18N[lang(this._hass)][key] ?? key;
  }

  _emit(config) {
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }

  _form(data, schema, onChange, helpers = {}) {
    const form = document.createElement("ha-form");
    form.hass = this._hass;
    form.data = data;
    form.schema = schema;
    form.computeLabel = (s) => this._t(s.label || s.name);
    form.computeHelper = (s) => helpers[s.name] || "";
    form.addEventListener("value-changed", (ev) => onChange(ev.detail.value));
    return form;
  }

  _build() {
    if (!this._config) return;
    const root = this.shadowRoot;
    const open = new Set([...root.querySelectorAll("details[open]")].map((d) => d.dataset.group));
    root.innerHTML = `<style>${EDITOR_CSS}</style>`;
    const cfg = this._config;

    root.append(this._form(
      { title: cfg.title || "", show_global_planning: cfg.show_global_planning, show_timeline: cfg.show_timeline },
      [
        { name: "title", label: "e_title", selector: { text: {} } },
        { name: "show_global_planning", label: "e_global", selector: { boolean: {} } },
        { name: "show_timeline", label: "e_timeline", selector: { boolean: {} } },
      ],
      (value) => {
        const next = { ...this._config, ...value };
        if (!next.title) delete next.title;
        this._emit(next);
      },
    ));

    const heading = document.createElement("h3");
    heading.textContent = this._t("e_groups");
    root.append(heading);

    const groups = cfg.groups || [];
    if (!groups.length) {
      const p = document.createElement("p");
      p.className = "hint";
      p.textContent = this._t("e_all");
      root.append(p);
    }
    const names = Object.fromEntries((this._info?.groups || []).map((g) => [g.id, g.name]));
    const manualOptions = ["temperature", "fan_mode", "swing_mode", "hvac_mode"].map((v) => ({ value: v, label: this._t(`m_${v}`) }));
    const compressorOptions = ["avg_24h", "avg_profile"].map((v) => ({ value: v, label: this._t(`o_${v}`) }));
    const infoById = Object.fromEntries((this._info?.groups || []).map((g) => [g.id, g]));

    groups.forEach((group, index) => {
      const details = document.createElement("details");
      details.dataset.group = group.group;
      if (open.has(group.group)) details.open = true;
      const summary = document.createElement("summary");
      summary.textContent = names[group.group] || group.group;
      details.append(summary);
      const data = { ...GROUP_DEFAULTS, ...group };
      details.append(this._form(
        data,
        [
          { name: "temperature_entity", label: "e_temp", selector: { entity: { filter: [{ domain: "sensor", device_class: "temperature" }, { domain: "climate" }, { domain: "sensor" }] } } },
          { name: "sensors", label: "e_sensors", selector: { entity: { multiple: true } } },
          { name: "show_planning", label: "e_show_planning", selector: { boolean: {} } },
          { name: "show_profiles", label: "e_show_profiles", selector: { boolean: {} } },
          { name: "manual", label: "e_manual", selector: { select: { multiple: true, mode: "list", options: manualOptions } } },
          { name: "compressor", label: "e_compressor", selector: { select: { multiple: true, mode: "list", options: compressorOptions } } },
        ],
        (value) => {
          const list = [...this._config.groups];
          const item = { group: group.group, ...value };
          if (!item.temperature_entity) delete item.temperature_entity;
          list[index] = item;
          this._emit({ ...this._config, groups: list });
        },
        { compressor: this._t(infoById[group.group]?.compressor ? "e_compressor_ok" : "e_compressor_missing") },
      ));
      const actions = document.createElement("div");
      actions.className = "actions";
      const button = (label, fn, disabled) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = this._t(label);
        b.disabled = disabled;
        b.addEventListener("click", fn);
        actions.append(b);
      };
      const move = (delta) => () => {
        const list = [...this._config.groups];
        const [item] = list.splice(index, 1);
        list.splice(index + delta, 0, item);
        this._emit({ ...this._config, groups: list });
        this._build();
      };
      button("e_up", move(-1), index === 0);
      button("e_down", move(1), index === groups.length - 1);
      button("e_remove", () => {
        this._emit({ ...this._config, groups: this._config.groups.filter((_, i) => i !== index) });
        this._build();
      }, false);
      details.append(actions);
      root.append(details);
    });

    const used = new Set(groups.map((g) => g.group));
    const free = (this._info?.groups || []).filter((g) => !used.has(g.id));
    if (free.length) {
      root.append(this._form(
        {},
        [{ name: "add", label: "e_add", selector: { select: { mode: "dropdown", options: free.map((g) => ({ value: g.id, label: g.name })) } } }],
        (value) => {
          if (!value.add) return;
          this._emit({ ...this._config, groups: [...groups, { group: value.add, ...GROUP_DEFAULTS }] });
          this._build();
        },
      ));
    }
  }
}

const EDITOR_CSS = `
  :host { display: flex; flex-direction: column; gap: 12px; }
  h3 { margin: 12px 0 0; font-size: 15px; font-weight: 500; }
  .hint { margin: 0; color: var(--secondary-text-color); font-size: 13px; }
  details { border: 1px solid var(--divider-color); border-radius: 12px; padding: 0 12px; }
  details[open] { padding-bottom: 12px; }
  summary { min-height: 48px; display: flex; align-items: center; font-weight: 500; cursor: pointer; }
  .actions { display: flex; gap: 8px; margin-top: 12px; }
  .actions button { min-height: 36px; padding: 0 14px; border-radius: 18px; border: 1px solid var(--divider-color); background: none; color: var(--primary-color); font: inherit; cursor: pointer; }
  .actions button:disabled { opacity: .4; cursor: default; }
`;

if (!customElements.get("split-scheduler-card")) {
  customElements.define("split-scheduler-card", SplitSchedulerCard);
  customElements.define("split-scheduler-card-editor", SplitSchedulerCardEditor);
  window.customCards = window.customCards || [];
  const l = (navigator.language || "fr").startsWith("fr") ? "fr" : "en";
  window.customCards.push({
    type: "split-scheduler-card",
    name: I18N[l].card_name,
    description: I18N[l].card_desc,
    preview: false,
  });
  console.info(`%c split-scheduler-card %c ${CARD_VERSION} `, "background:#03a0f4;color:#fff;border-radius:3px 0 0 3px", "background:#444;color:#fff;border-radius:0 3px 3px 0");
}
