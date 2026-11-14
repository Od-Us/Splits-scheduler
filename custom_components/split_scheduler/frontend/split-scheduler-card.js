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
 *       thermometers:                 # thermomètre de chaque split (sinon sa température)
 *         climate.salon: sensor.salon_temperature
 *       sensors: [sensor.salon_humidite]
 *       sensor_names: { sensor.salon_humidite: Humidité }   # libellés (facultatif)
 *       show_planning: true
 *       show_profiles: true
 *       manual: [temperature, fan_mode, swing_mode, hvac_mode]
 *       compressor: [avg_24h, avg_profile]   # démarrages du compresseur par heure
 *       compressor_timeline: true            # frise des marches du compresseur
 *       chart: [ambient, setpoint, outdoor]  # courbes du jour (au choix)
 */

const CARD_VERSION = "1.11.1";
const ICON_URL = new URL("icon.png", import.meta.url).href;

const GROUP_DEFAULTS = {
  sensors: [],
  show_planning: true,
  show_profiles: true,
  manual: ["temperature", "fan_mode"],
  compressor: [],
  compressor_timeline: false,
  show_daikin: true,
  chart: [],
};

/** Courbes demandées : liste [ambient, setpoint, outdoor] (anciennes valeurs « both »… acceptées). */
function chartSeries(chart) {
  if (Array.isArray(chart)) return chart.filter((c) => ["ambient", "setpoint", "outdoor"].includes(c));
  return { ambient: ["ambient"], setpoint: ["setpoint"], both: ["ambient", "setpoint"] }[chart] || [];
}

const HISTORY_TTL = 300000; // historique relu toutes les 5 minutes

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
    e_sensor_names: "Libellés des capteurs supplémentaires (vide = nom du capteur)",
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
    c_detail: "{n} démarrage en {hours} h|{n} démarrages en {hours} h",
    e_compressor: "Démarrages du compresseur par heure (compresseur commun à tous les splits du groupe)",
    e_compressor_missing: "Aucun capteur de compresseur pour ce groupe : indiquez-le dans la configuration du groupe (Paramètres › Programmation des splits › Configurer › Groupes).",
    e_compressor_ok: "Tous les splits du groupe sont considérés comme reliés au même compresseur.",
    o_avg_24h: "Moyenne sur les 24 dernières heures",
    o_avg_profile: "Moyenne depuis le dernier changement de profil",
    t_compressor: "Compresseur",
    t_starts: "{n} démarrage|{n} démarrages",
    t_running: "En marche",
    t_ambient: "Ambiance",
    t_setpoint: "Consigne",
    e_compressor_timeline: "Frise des démarrages du compresseur (sous celle des profils)",
    e_daikin: "Partie « Modifier » : boutons des fonctions Daikin (si les splits du groupe en ont)",
    feat_unavailable: "indisponible",
    feat_failed: "{f} : pas de réponse de {s}. Vérifiez l'option « HA switches » du module Faikout.",
    feat_wait: "en attente du split…",
    e_chart: "Courbes du jour",
    ch_none: "Aucune",
    ch_ambient: "Température ambiante",
    ch_setpoint: "Consigne",
    ch_both: "Ambiance et consigne",
    ch_outdoor: "Température extérieure",
    t_outdoor: "Extérieur",
    outdoor: "Extérieur",
    outdoor_avg: "(moy. 1 h)",
    adapted: "Adaptée",
    profile_target: "Profil : {t} °C",
    adapt_cool: "Forte chaleur : consigne relevée à {e} °C (extérieur {o} °C − écart max {d} °C). Elle redescend vers {p} °C quand l'extérieur baisse.",
    adapt_heat: "Grand froid : consigne abaissée à {e} °C (extérieur {o} °C + écart max {d} °C). Elle remonte vers {p} °C quand l'extérieur se radoucit.",
    n_splits: "{n} split|{n} splits",
    unreachable: "Injoignable depuis {t}",
    measured: "mesurée",
    open_split: "Ouvrir le thermostat",
    history: "{g} — historique",
    p_day: "Jour", p_3d: "3 jours", p_week: "Semaine",
    prev: "Période précédente", next_p: "Période suivante",
    close: "Fermer",
    available_since: "Historique disponible depuis le {d}",
    loading: "Chargement de l'historique…",
    no_data: "Aucune donnée sur cette période.",
    no_data_at: "Aucune donnée à cet instant.",
    resume_at: "Reprise",
    resume_now: "Reprendre maintenant",
    stale: "Version {v} installée, mais ce navigateur affiche encore la carte {c} (cache).",
    ovr_n_splits: "Dérogation · {n} splits",
    t_setpoint_group: "Consigne du groupe",
    t_ambient_mean: "Ambiance (moyenne)",
    t_setpoint_held: "Consigne en dérogation",
    t_ambient_held: "Ambiance en dérogation",
    mean_n: "moy. {n} splits",
    held_since: "{s} — dérogation",
    e_thermo: "Thermomètre de chaque split (vide : température mesurée par le split). L'ambiance affichée est la moyenne des splits qui suivent le programme.",
    e_thermo_of: "{s} — thermomètre",
    t_dashed: "Dérogations",
    others_follow: "l'autre split suit le programme|les {n} autres splits suivent le programme",
    instead: "{v} au lieu de {p}",
    diff_targets: "Consignes différentes : {a} à {b} °C",
    diff_modes: "Modes différents",
    split_resume: "Remettre ce split au programme",
    confirm_title: "Changer de planning ?",
    confirm_group: "Le groupe « {g} » passe au planning « {p} ». Ses splits reçoivent aussitôt le profil prévu par ce planning ; les dérogations en cours sont annulées.",
    confirm_all: "Tous les groupes ({n}) passent au planning « {p} ». Tous les splits reçoivent aussitôt le profil prévu par ce planning ; les dérogations en cours sont annulées.",
    cancel: "Annuler",
    confirm_ok: "Changer",
    reload: "Recharger",
    earlier: "Reprise 30 minutes plus tôt",
    later: "Reprise 30 minutes plus tard",
    skipped: "{t} {p} ignoré · ensuite {n}",
    then: "Ensuite {n}",
    preset: "Préréglage",
    m_preset_mode: "Préréglage (Normal, ECONO, Powerful)",
    presets: { home: "Normal", none: "Normal", eco: "ECONO", boost: "Powerful" },
    features: { comfort: "Flux confort", streamer: "Streamer", sensor_mode: "Présence", quiet_outdoor: "Ext. silencieux", powerful: "Powerful" },
    feature_long: { comfort: "Flux d'air confort", streamer: "Purification Streamer", sensor_mode: "Capteur de présence", quiet_outdoor: "Unité extérieure silencieuse", powerful: "Powerful" },
    on_off: ["désactivée", "activée"],
    daikin: "Fonctions Daikin",
    profiles_band: "Profils",
    compressor_band: "Compresseur",
    starts_period: "{n} démarrage sur la période · {r} démarrage/h en moyenne|{n} démarrages sur la période · {r} démarrage/h en moyenne",
    running: "en marche",
    stopped: "à l'arrêt",
    now_label: "maintenant",
    touch_hint: "Touchez la courbe pour déplacer le curseur",
    adapted_short: "adaptée",
    open_detail: "Ouvrir la vue détaillée",
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
    e_sensor_names: "Extra sensor labels (empty = sensor name)",
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
    c_detail: "{n} start in {hours} h|{n} starts in {hours} h",
    e_compressor: "Compressor starts per hour (compressor shared by all splits of the group)",
    e_compressor_missing: "No compressor sensor for this group: set it in the group configuration (Settings › Split scheduler › Configure › Groups).",
    e_compressor_ok: "All splits of the group are assumed to share the same compressor.",
    o_avg_24h: "Average over the last 24 hours",
    o_avg_profile: "Average since the last profile change",
    t_compressor: "Compressor",
    t_starts: "{n} start|{n} starts",
    t_running: "Running",
    t_ambient: "Room",
    t_setpoint: "Target",
    e_compressor_timeline: "Compressor starts timeline (below the profile timeline)",
    e_daikin: "“Modify” section: Daikin function buttons (if the group's splits have them)",
    feat_unavailable: "unavailable",
    feat_failed: "{f}: no answer from {s}. Check the “HA switches” option of the Faikout module.",
    feat_wait: "waiting for the split…",
    e_chart: "Today's charts",
    ch_none: "None",
    ch_ambient: "Room temperature",
    ch_setpoint: "Target",
    ch_both: "Room and target",
    ch_outdoor: "Outdoor temperature",
    t_outdoor: "Outdoor",
    outdoor: "Outdoor",
    outdoor_avg: "(1 h avg.)",
    adapted: "Adapted",
    profile_target: "Profile: {t} °C",
    adapt_cool: "Heatwave: target raised to {e} °C (outdoor {o} °C − max gap {d} °C). It goes back to {p} °C as the outdoor temperature drops.",
    adapt_heat: "Severe cold: target lowered to {e} °C (outdoor {o} °C + max gap {d} °C). It goes back to {p} °C as it gets milder.",
    n_splits: "{n} split|{n} splits",
    unreachable: "Unreachable since {t}",
    measured: "measured",
    open_split: "Open the thermostat",
    history: "{g} — history",
    p_day: "Day", p_3d: "3 days", p_week: "Week",
    prev: "Previous period", next_p: "Next period",
    close: "Close",
    available_since: "History available since {d}",
    loading: "Loading history…",
    no_data: "No data for this period.",
    no_data_at: "No data at this time.",
    resume_at: "Resumes",
    resume_now: "Resume now",
    stale: "Version {v} is installed, but this browser still shows card {c} (cache).",
    ovr_n_splits: "Override · {n} splits",
    t_setpoint_group: "Group target",
    t_ambient_mean: "Ambient (average)",
    t_setpoint_held: "Overridden target",
    t_ambient_held: "Overridden ambient",
    mean_n: "avg. {n} splits",
    held_since: "{s} — override",
    e_thermo: "Thermometer of each split (empty: temperature measured by the split). The ambient shown is the average of the splits following the schedule.",
    e_thermo_of: "{s} — thermometer",
    t_dashed: "Overrides",
    others_follow: "the other split follows the schedule|the {n} other splits follow the schedule",
    instead: "{v} instead of {p}",
    diff_targets: "Different targets: {a} to {b} °C",
    diff_modes: "Different modes",
    split_resume: "Put this split back on schedule",
    confirm_title: "Change planning?",
    confirm_group: "Group “{g}” switches to planning “{p}”. Its splits immediately receive the profile of this planning; current overrides are cancelled.",
    confirm_all: "All groups ({n}) switch to planning “{p}”. All splits immediately receive the profile of this planning; current overrides are cancelled.",
    cancel: "Cancel",
    confirm_ok: "Change",
    reload: "Reload",
    earlier: "Resume 30 minutes earlier",
    later: "Resume 30 minutes later",
    skipped: "{t} {p} skipped · then {n}",
    then: "Then {n}",
    preset: "Preset",
    m_preset_mode: "Preset (Normal, ECONO, Powerful)",
    presets: { home: "Normal", none: "Normal", eco: "ECONO", boost: "Powerful" },
    features: { comfort: "Comfort air", streamer: "Streamer", sensor_mode: "Presence", quiet_outdoor: "Quiet outdoor", powerful: "Powerful" },
    feature_long: { comfort: "Comfort airflow", streamer: "Streamer purification", sensor_mode: "Presence sensor", quiet_outdoor: "Quiet outdoor unit", powerful: "Powerful" },
    on_off: ["off", "on"],
    daikin: "Daikin functions",
    profiles_band: "Profiles",
    compressor_band: "Compressor",
    starts_period: "{n} start in the period · {r} starts/h on average|{n} starts in the period · {r} starts/h on average",
    running: "running",
    stopped: "stopped",
    now_label: "now",
    touch_hint: "Touch the chart to move the cursor",
    adapted_short: "adapted",
    open_detail: "Open the detailed view",
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
  ext: "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
  resume: "M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4M10 9v6l5-3z",
  left: "M15 6l-6 6 6 6",
  right: "M9 6l6 6-6 6",
  close: "M6 6l12 12M18 6L6 18",
  wave: "M2 12c2-6 4-6 5 0s3 6 5 0 3-6 5 0 3 6 5 0",
  sun: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5",
  adapt_down: "M12 3v10M8 9l4 4 4-4M5 21h14",
  adapt_up: "M12 21V11M8 15l4-4 4 4M5 3h14",
  info: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 11v5M12 8v.5",
};

function lang(hass) {
  return (hass?.locale?.language || hass?.language || "fr").startsWith("fr") ? "fr" : "en";
}

/** « un|plusieurs » selon n, avec {n} remplacé. */
function plural(text, n) {
  const [one, many] = String(text).split("|");
  return ((n === 1 || many === undefined ? one : many) || "").replaceAll("{n}", n);
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
function zonedNow(timeZone, date = new Date(Date.now())) {
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
    this._splitsOpen = new Set();
    this._history = {};
    this._historyLoading = new Set();
    this._historyStamp = 0;
    this._pending = {};
    this._timers = {};
    this._signature = "";
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("keydown", (ev) => {
      if ((ev.key === "Enter" || ev.key === " ") && ev.target.matches?.("[role=button][data-action]")) {
        ev.preventDefault();
        this._onClick(ev);
      }
    });
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
    this._reload = setInterval(() => { this._load(); this._ensureHistory(); }, 300000);
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
      ids.push(...Object.values(g.info.entities), ...g.info.climates, ...Object.values(thermometers(g, this._hass.states)), ...(g.sensors || []),
        ...Object.values(g.info.features || {}).flatMap((m) => Object.values(m)));
    }
    const parts = ids.filter(Boolean).map((id) => {
      const s = this._hass.states[id];
      return s ? `${id}:${s.last_updated}` : id;
    });
    return [JSON.stringify(this._config), this._error, this._confirm ? "confirm" : "", JSON.stringify(this._featPending || {}), JSON.stringify(this._featMsg || {}), JSON.stringify(this._pending), [...this._expanded].join(), [...this._splitsOpen].join(), lang(this._hass), this._historyStamp, ...parts].join("|");
  }

  _render() {
    if (!this._config || !this._hass) return;
    if (this._info) this._ensureHistory();
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
        ${this._renderConfirm()}
        ${this._renderStale()}
        ${this._renderHeader()}
        <div class="grid">${groups.map((g) => this._renderGroup(g)).join("")}</div>
      </div>`;
  }

  /** Le navigateur a gardé une ancienne carte alors que l'intégration a été mise à jour. */
  _renderStale() {
    const installed = this._info?.version;
    if (!installed || installed === CARD_VERSION) return "";
    return `<div class="banner warn"><span>${esc(this._t("stale").replace("{v}", installed).replace("{c}", CARD_VERSION))}</span>
      <button type="button" class="filled" data-action="reload">${esc(this._t("reload"))}</button></div>`;
  }

  _renderHeader() {
    const cfg = this._config;
    const tz = this._info.time_zone;
    const loc = this._hass?.locale?.language || this._hass?.language || "fr";
    const now = new Intl.DateTimeFormat(loc, { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit", timeZone: tz }).format(new Date(Date.now()));
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
    const pa0 = profileState?.attributes || {};
    const groupOverride = pa0.derogation === true;
    const splitOvr = groupOverride ? [] : (pa0.derogations_splits || []);
    const held = new Set(splitOvr.map((o) => o.entity_id));
    const ready = (id) => { const st = this._state(id); return st && !["unavailable", "unknown"].includes(st.state); };
    // Référence : premier split qui suit le programme (sinon le premier)
    const followers = g.info.climates.filter((id) => !held.has(id) && ready(id));
    const climate = this._state(followers[0] || g.info.climates[0]);
    const attrs = climate?.attributes || {};
    const profile = this._profile(profileState?.state);
    const color = profile?.color || "var(--disabled-color, #9e9e9e)";
    const mode = climate?.state;
    const hvac = I18N[lang(this._hass)].hvac;

    const pending = this._pending[g.group];
    // Grande consigne : celle du groupe (capteur « Consigne »), sinon celle du split de référence
    const groupTarget = Number(this._state(e.target)?.state);
    const target = pending ?? (Number.isFinite(groupTarget) ? groupTarget : attrs.temperature);
    let big;
    if (mode === "off") big = `<span class="big word">${esc(hvac.off)}</span>`;
    else if ((target === undefined || target === null) && attrs.target_temp_low != null && attrs.target_temp_high != null) {
      big = `<span class="big range">${this._fmt(attrs.target_temp_low)}–${this._fmt(attrs.target_temp_high)}<small> °C</small></span>`;
    } else if (target === undefined || target === null) big = `<span class="big word">–</span>`;
    else big = `<span class="big">${this._fmt(target)}<small> °C</small></span>`;

    // Écarts : splits en dérogation, et splits qui ne sont pas d'accord entre eux
    const deviations = [];
    for (const o of splitOvr) {
      const st = this._state(o.entity_id);
      const t = (o.ecarts || []).find((x) => x.reglage === "temperature");
      const m = (o.ecarts || []).find((x) => x.reglage === "hvac_mode");
      const what = m ? (hvac[m.valeur] || m.valeur) : t ? `${this._fmt(t.valeur)} °C` : null;
      if (what) deviations.push(`${this._splitName(o.entity_id, st)} : ${what}`);
    }
    const running = followers.map((id) => this._state(id)).filter((st) => st.state !== "off");
    const temps = [...new Set(running.map((st) => st.attributes.temperature).filter((v) => v != null).map(Number))];
    const modes = new Set(followers.map((id) => this._state(id).state));
    if (modes.size > 1) deviations.push(this._t("diff_modes"));
    else if (temps.length > 1) {
      deviations.push(this._t("diff_targets").replace("{a}", this._fmt(Math.min(...temps))).replace("{b}", this._fmt(Math.max(...temps))));
    }
    let statusText = I18N[lang(this._hass)].status[status] || status;
    if (status === "override" && !groupOverride && splitOvr.length && g.info.climates.length > 1) {
      statusText = splitOvr.length === 1
        ? `${statusText} · ${this._splitName(splitOvr[0].entity_id)}`
        : this._t("ovr_n_splits").replace("{n}", splitOvr.length);
    }

    const statusIcon = { scheduled: ICONS.check, override: ICONS.alert, disabled: ICONS.pause }[status] || ICONS.pause;
    const statusColor = STATUS_COLORS[status] || STATUS_COLORS.disabled;

    // Température ambiante : capteur choisi, sinon celle du split
    // Ambiance : moyenne des thermomètres des splits qui suivent le programme ; un split en dérogation à part
    let ambient = "";
    const thermo = thermometers(g, this._hass.states);
    const ambientOf = (eid) => {
      const v = thermo[eid] ? this._state(thermo[eid])?.state : this._state(eid)?.attributes?.current_temperature;
      return v === undefined || v === null || v === "" || Number.isNaN(Number(v)) ? null : Number(v);
    };
    const ambs = followers.map(ambientOf).filter((v) => v !== null);
    if (ambs.length) {
      const mean = ambs.reduce((a, b) => a + b, 0) / ambs.length;
      ambient = `<span class="chip">${svg(ICONS.thermo, 16)}${esc(this._t("ambient"))} <strong>${this._fmt(mean)} °C</strong>${ambs.length > 1 ? ` <span class="small">${esc(this._t("mean_n").replace("{n}", ambs.length))}</span>` : ""}</span>`;
    }
    for (const o of splitOvr) {
      const v = ambientOf(o.entity_id);
      if (v !== null) ambient += `<span class="chip held">${svg(ICONS.thermo, 16)}${esc(this._splitName(o.entity_id))} <strong>${this._fmt(v)} °C</strong></span>`;
    }
    const extra = (g.sensors || []).map((id) => this._sensorChip(id, g.sensor_names?.[id])).join("") + this._compressorChips(g);

    const nextIso = nextState && !["unknown", "unavailable"].includes(nextState.state) ? nextState.state : null;
    const nextProfile = nextState?.attributes?.prochain_profil;

    // Adaptation de la consigne à la température extérieure
    const pa = profileState?.attributes || {};
    const adapted = pa.adaptation_exterieure === true;
    const outdoorAvg = pa.temperature_exterieure;
    let outdoorChip = "";
    if (pa.ecart_max_exterieur != null && outdoorAvg != null) {
      outdoorChip = `<span class="chip">${svg(ICONS.sun, 16)}${esc(this._t("outdoor"))} <strong>${this._fmt(outdoorAvg)} °C</strong> <span class="small">${esc(this._t("outdoor_avg"))}</span></span>`;
    }

    let banner = "";
    if (adapted && status !== "disabled") {
      const text = this._t(mode === "heat" ? "adapt_heat" : "adapt_cool")
        .replace("{e}", this._fmt(pa.consigne_appliquee, 0)).replace("{o}", this._fmt(outdoorAvg, 0))
        .replace("{d}", this._fmt(pa.ecart_max_exterieur, 0)).replace("{p}", this._fmt(pa.consigne_profil, 0));
      banner += `<div class="banner info">${svg(ICONS.info, 18)}<span>${esc(text)}</span></div>`;
    }
    if (status === "override" && !groupOverride) {
      const others = g.info.climates.length - splitOvr.length;
      for (const o of splitOvr) banner += this._splitBanner(g, o, others);
    } else if (status === "override") {
      const gid = esc(g.group);
      const resume = pa.reprise;
      const skip = pa.creneau_ignore;
      const note = skip
        ? this._t("skipped").replace("{t}", this._time(skip.heure)).replace("{p}", skip.profil || "").replace("{n}", pa.reprise_profil || "")
        : (pa.reprise_profil ? this._t("then").replace("{n}", pa.reprise_profil) : "");
      banner += `<div class="banner warn compact">
        <div class="row">
          <span class="when"><span class="small">${esc(this._t("resume_at"))}</span> <strong>${resume ? esc(this._time(resume)) : "–"}</strong></span>
          ${resume ? `<button type="button" class="shift" data-action="shift" data-group="${gid}" data-value="-30" aria-label="${esc(this._t("earlier"))}">−30min</button>
          <button type="button" class="shift" data-action="shift" data-group="${gid}" data-value="30" aria-label="${esc(this._t("later"))}">+30min</button>` : ""}
          <button type="button" class="filled resume" data-action="resume" data-group="${gid}" aria-label="${esc(this._t("resume_now"))}" title="${esc(this._t("resume_now"))}">${svg(ICONS.resume, 20)}</button>
        </div>
        ${note ? `<span class="small note">${esc(note)}</span>` : ""}
      </div>`;
    } else if (status === "disabled") {
      banner += `<div class="banner"><span>${esc(this._t("disabled_text"))}</span><button type="button" class="outlined" data-action="programming-on" data-group="${esc(g.group)}">${esc(this._t("reactivate"))}</button></div>`;
    } else if (status === "no_program") {
      banner += `<div class="banner"><span>${esc(this._t("no_program_text"))}</span></div>`;
    }

    const timeline = this._renderTimeline(
      g, planningState?.state, nextIso, nextProfile,
      this._config.show_timeline && status !== "disabled" && status !== "no_program",
    );

    const hasEdit = g.show_planning || g.show_profiles || (g.manual || []).length || e.programming;
    const open = this._expanded.has(g.group);
    const editToggle = hasEdit
      ? `<button type="button" class="expander" aria-expanded="${open}" data-action="expand" data-group="${esc(g.group)}">${esc(this._t(open ? "hide" : "modify"))} ${svg(open ? ICONS.up : ICONS.down, 18)}</button>`
      : "";

    return `
      <article class="group" aria-label="${esc(g.info.name)}">
        <div class="row between">
          <button type="button" class="gname" aria-expanded="${this._splitsOpen.has(g.group)}" data-action="splits" data-group="${esc(g.group)}">
            <h2>${esc(g.info.name)}</h2><span class="muted small">${esc(plural(this._t("n_splits"), g.info.climates.length))}</span>${svg(this._splitsOpen.has(g.group) ? ICONS.up : ICONS.down, 16)}
          </button>
          <span class="status" title="${esc(statusText)}" style="background:${mix(statusColor, 18)};color:${mix(statusColor, 70, "var(--primary-text-color)")}">${svg(statusIcon, 14)}<span class="ell">${esc(statusText)}</span></span>
        </div>
        ${this._splitsOpen.has(g.group) ? this._renderSplits(g, splitOvr) : ""}
        <div class="row between end">
          <div class="col"><span class="muted small">${esc(this._t("setpoint"))}</span>
            <span class="row bigrow">${big}${adapted ? `<span class="adapted">${svg(pa.consigne_appliquee > pa.consigne_profil ? ICONS.adapt_up : ICONS.adapt_down, 13)}${esc(this._t("adapted"))}</span>` : ""}</span>
            ${adapted ? `<span class="muted small">${esc(this._t("profile_target").replace("{t}", this._fmt(pa.consigne_profil)))}</span>` : ""}
            ${deviations.map((d) => `<span class="small devi">${esc(d)}</span>`).join("")}</div>
          <div class="col right">
            ${profile ? `<span class="pchip" style="background:${mix(color, 20)};color:${mix(color, 55, "var(--primary-text-color)")}"><i style="background:${color}"></i>${esc(profile.name)}</span>` : ""}
            <span class="muted small">${esc([hvac[mode] || "", ["eco", "boost"].includes(attrs.preset_mode) ? I18N[lang(this._hass)].presets[attrs.preset_mode] : ""].filter(Boolean).join(" · "))}</span>

          </div>
        </div>
        ${(() => {
          const L = I18N[lang(this._hass)];
          const active = this._featureStates(g).filter((f) => f.on && f.key !== "powerful");
          return active.length ? `<div class="fchips">${active.map((f) => `<span class="fchip" title="${esc(L.feature_long[f.key])}">${FEATURE_ICONS[f.key]} ${esc(L.features[f.key])}</span>`).join("")}</div>` : "";
        })()}
        ${ambient || extra || outdoorChip ? `<div class="chips">${ambient}${outdoorChip}${extra}</div>` : ""}
        ${banner}
        ${timeline}
        ${editToggle}
        ${open ? this._renderEdit(g, { profileState, planningState, climate, nextIso }) : ""}
      </article>`;
  }

  _renderSplits(g, splitOvr = []) {
    const hvac = I18N[lang(this._hass)].hvac;
    const byId = Object.fromEntries(splitOvr.map((o) => [o.entity_id, o]));
    const rows = g.info.climates.map((eid) => {
      const s = this._state(eid);
      const name = s?.attributes?.friendly_name || eid;
      let sub;
      let color = "var(--primary-color)";
      let warn = false;
      if (!s || ["unavailable", "unknown"].includes(s.state)) {
        const since = s?.last_changed ? this._time(s.last_changed) : "?";
        sub = this._t("unreachable").replace("{t}", since);
        color = "var(--disabled-color, #9e9e9e)";
        warn = true;
      } else {
        const a = s.attributes;
        const parts = [hvac[s.state] || s.state];
        if (a.temperature != null && s.state !== "off") parts.push(`${this._t("setpoint").toLowerCase()} ${this._fmt(a.temperature)} °C`);
        if (a.current_temperature != null) parts.push(`${this._t("measured")} ${this._fmt(a.current_temperature)} °C`);
        const icons = this._splitFeatureIcons(g, eid);
        if (icons) parts.push(icons);
        sub = parts.join(" · ");
        if (s.state === "off") color = "var(--disabled-color, #9e9e9e)";
      }
      const o = byId[eid];
      const extra = o ? [this._ecarts(o), o.reprise ? `${this._t("resume_at").toLowerCase()} ${this._time(o.reprise)}` : ""].filter(Boolean).join(" · ") : "";
      return `<div class="splitrow${o ? " held" : ""}"><button type="button" class="split" data-action="open-split" data-group="${esc(g.group)}" data-value="${esc(eid)}" aria-label="${esc(this._t("open_split"))} : ${esc(name)}">
        <i style="background:${color}"></i><span class="col"><strong>${esc(name)}</strong><span class="small ${warn ? "err" : "muted"}">${esc(sub)}</span>${extra ? `<span class="small devi">${esc(extra)}</span>` : ""}</span>${svg(ICONS.ext, 16)}</button>
        ${o ? `<button type="button" class="filled resume" data-action="split-resume" data-group="${esc(g.group)}" data-value="${esc(eid)}" aria-label="${esc(this._t("split_resume"))} : ${esc(name)}" title="${esc(this._t("split_resume"))}">${svg(ICONS.resume, 20)}</button>` : ""}</div>`;
    }).join("");
    return `<div class="splits">${rows}</div>`;
  }

  /**
   * Fonctions Daikin proposées pour un groupe : seulement celles qu'au moins un de ses splits
   * possède. Activée = activée sur tous les splits qui l'ont.
   */
  _featureStates(g) {
    const result = [];
    const per = g.info.features || {};
    for (const key of ["comfort", "streamer", "sensor_mode", "quiet_outdoor"]) {
      const switches = g.info.climates.map((eid) => per[eid]?.[key]).filter(Boolean);
      if (!switches.length) continue;
      const states = switches.map((sw) => this._state(sw)?.state).filter((v) => v === "on" || v === "off");
      result.push({ key, on: states.length > 0 && states.every((v) => v === "on"), available: states.length > 0, switches });
    }
    const boost = g.info.climates.map((eid) => this._state(eid)).filter((c) => (c?.attributes?.preset_modes || []).includes("boost"));
    if (boost.length) result.push({ key: "powerful", on: boost.every((c) => c.attributes.preset_mode === "boost"), available: true, switches: [] });
    // Appui en cours : on montre l'état demandé jusqu'à la réponse du split
    for (const item of result) {
      const p = this._featPending?.[`${g.group}|${item.key}`];
      if (!p) continue;
      if (item.on === p.want) delete this._featPending[`${g.group}|${item.key}`];
      else { item.on = p.want; item.pending = true; }
    }
    return result;
  }

  /** Icônes des fonctions actives d'un split, ex. « 🙆 🤫 ». */
  _splitFeatureIcons(g, eid) {
    const icons = [];
    for (const [key, sw] of Object.entries(g.info.features?.[eid] || {})) {
      if (this._state(sw)?.state === "on") icons.push(FEATURE_ICONS[key]);
    }
    if (this._state(eid)?.attributes?.preset_mode === "boost") icons.push(FEATURE_ICONS.powerful);
    return icons.join(" ");
  }

  _splitName(entityId, st = this._state(entityId)) {
    return st?.attributes?.friendly_name || entityId;
  }

  /** « 23 °C au lieu de 20 °C », « Climatisation au lieu de Chauffage »… */
  _ecarts(o) {
    const L = I18N[lang(this._hass)];
    const fmt = (r, v) => {
      if (v === null || v === undefined) return "–";
      if (r === "temperature") return `${this._fmt(v)} °C`;
      if (r === "hvac_mode") return L.hvac[v] || v;
      if (r === "preset_mode") return L.presets[v] || v;
      return `${this._t({ fan_mode: "fan", swing_mode: "swing" }[r] || r).toLowerCase()} ${v}`;
    };
    return (o.ecarts || []).map((x) => (L.features[x.reglage]
      ? `${L.features[x.reglage]} : ${this._t("instead").replace("{v}", L.on_off[x.valeur ? 1 : 0]).replace("{p}", L.on_off[x.prevu ? 1 : 0])}`
      : this._t("instead").replace("{v}", fmt(x.reglage, x.valeur)).replace("{p}", fmt(x.reglage, x.prevu)))).join(", ");
  }

  /** Bandeau compact d'un split en dérogation : nom et écart, puis reprise et boutons. */
  _splitBanner(g, o, others) {
    const gid = esc(g.group);
    const eid = esc(o.entity_id);
    const diff = this._ecarts(o);
    const follow = others > 0 ? plural(this._t("others_follow"), others) : "";
    return `<div class="banner warn compact">
        <div class="small head"><b class="who">${esc(this._splitName(o.entity_id))}</b>${diff ? ` · ${esc(diff)}` : ""}</div>
        <div class="row">
          <span class="when"><span class="small">${esc(this._t("resume_at"))}</span> <strong>${o.reprise ? esc(this._time(o.reprise)) : "–"}</strong></span>
          ${o.reprise ? `<button type="button" class="shift" data-action="shift" data-group="${gid}" data-entity="${eid}" data-value="-30" aria-label="${esc(this._t("earlier"))}">−30min</button>
          <button type="button" class="shift" data-action="shift" data-group="${gid}" data-entity="${eid}" data-value="30" aria-label="${esc(this._t("later"))}">+30min</button>` : ""}
          <button type="button" class="filled resume" data-action="split-resume" data-group="${gid}" data-value="${eid}" aria-label="${esc(this._t("split_resume"))}" title="${esc(this._t("split_resume"))}">${svg(ICONS.resume, 20)}</button>
        </div>
        ${follow ? `<span class="small note">${esc(follow)}</span>` : ""}
      </div>`;
  }

  _openSplit(g, entityId) {
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
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
        ? plural(this._t("c_detail"), a.demarrages).replace("{hours}", this._fmt(a.duree_h)) : "";
      chips.push(`<span class="chip" title="${esc(title)}">${svg(ICONS.wave, 16)}${esc(label)} <strong>${esc(value)}</strong></span>`);
    }
    return chips.join("");
  }

  _sensorChip(entityId, label) {
    const s = this._state(entityId);
    if (!s) return this._chip(ICONS.gauge, label || entityId, "–");
    const dc = s.attributes.device_class;
    const icon = dc === "temperature" ? ICONS.thermo : dc === "humidity" ? ICONS.drop : ICONS.gauge;
    const value = typeof this._hass.formatEntityState === "function"
      ? this._hass.formatEntityState(s)
      : `${s.state} ${s.attributes.unit_of_measurement || ""}`;
    return this._chip(icon, label || s.attributes.friendly_name || entityId, esc(value));
  }

  _renderTimeline(g, planningName, nextIso, nextProfile, showProfiles) {
    const now = zonedNow(this._info.time_zone);
    const nowPct = ((now.minutes / 1440) * 100).toFixed(2);
    const compressorEntity = g.info.compressor;
    const showCompressor = g.compressor_timeline && compressorEntity;
    const chart = chartSeries(g.chart);
    if (!showProfiles && !showCompressor && !chart.length) return "";
    const rows = [];
    if (showProfiles) {
      const planning = this._info.plannings.find((p) => p.name === planningName);
      const program = planning?.programs?.[g.group] || {};
      const bars = daySegments(program, now.weekday).map((s) => {
        const p = this._info.profiles.find((x) => x.id === s.profile);
        const width = ((s.to - s.from) / 14.4).toFixed(3);
        return `<span style="width:${width}%;background:${p ? p.color : "var(--divider-color)"}" title="${esc(p ? p.name : "")}"></span>`;
      }).join("");
      const next = nextIso
        ? `${esc(this._t("next"))} : <strong>${esc(this._time(nextIso))} ${esc(nextProfile || "")}</strong>`
        : esc(this._t("no_change"));
      rows.push(`<div class="row between small muted"><span>${esc(this._t("today"))}</span><span>${next}</span></div>`);
      let hatch = "";
      const pa = this._state(g.info.entities.profile)?.attributes || {};
      if (pa.derogation && pa.derogation_depuis && pa.reprise) {
        const toPct = (iso) => {
          const t = new Date(iso).getTime();
          const z = zonedNow(this._info.time_zone, new Date(t));
          const sameDay = z.day === now.day;
          if (sameDay) return (z.minutes / 1440) * 100;
          return t < Date.now() ? 0 : 100;
        };
        const from = toPct(pa.derogation_depuis);
        const to = toPct(pa.reprise);
        if (to > from) hatch = `<i class="hatch" style="left:${from.toFixed(2)}%;width:${(to - from).toFixed(2)}%"></i>`;
      }
      rows.push(`<div class="bar">${bars}${hatch}<b style="left:${nowPct}%"></b></div>`);
    }
    const history = this._history[g.group];
    const legend = [];
    if (showCompressor) {
      const { runs, starts } = this._compressorRuns(history);
      const blocks = runs.map(([a, b]) => `<i style="left:${a.toFixed(3)}%;width:${Math.max(b - a, 0.15).toFixed(3)}%"></i>`).join("");
      const ticks = starts.map((x) => `<u style="left:${x.toFixed(3)}%"></u>`).join("");
      rows.push(`<div class="cbar" title="${esc(this._t("t_compressor"))}">${blocks}${ticks}<b style="left:${nowPct}%"></b></div>`);
      legend.push(`<span><i class="lg run"></i>${esc(this._t("t_compressor"))} · ${esc(plural(this._t("t_starts"), starts.length))}</span>`);
    }
    if (chart.length) {
      rows.push(this._renderChart(g, history, chart, nowPct, legend));
    }
    rows.push(`<div class="ticks">${["0 h", "6 h", "12 h", "18 h", "24 h"].map((l, i) => `<span style="left:${i * 25}%">${l}</span>`).join("")}</div>`);
    if (legend.length) rows.push(`<div class="legend">${legend.join("")}</div>`);
    return `<div class="timeline" role="button" tabindex="0" data-action="detail" data-group="${esc(g.group)}" aria-label="${esc(this._t("open_detail"))}">${rows.join("")}</div>`;
  }

  /** Marches du compresseur aujourd'hui : périodes [début, fin] et démarrages (en %). */
  _compressorRuns(history) {
    const points = [...(history?.comp || [])];
    const live = this._state(history?.compEntity);
    if (live) points.push([Date.now(), live.state]);
    const runs = [];
    const starts = [];
    let on = null;
    let was = null;
    for (const [t, value] of points) {
      const n = Number(value);
      if (!Number.isFinite(n)) continue;
      const x = this._pct(t, history);
      if (n > 0 && on === null) {
        on = x;
        if (was === false) starts.push(x);
      } else if (n <= 0 && on !== null) {
        runs.push([on, x]);
        on = null;
      }
      was = n > 0;
    }
    if (on !== null) runs.push([on, this._pct(Date.now(), history)]);
    return { runs, starts };
  }

  _pct(t, history) {
    const start = history?.midnight ?? Date.now();
    return Math.min(100, Math.max(0, ((t - start) / 86400000) * 100));
  }

  _renderChart(g, history, mode, nowPct, legend) {
    const multi = g.info.climates.length > 1;
    const H = multi ? 120 : 60;
    const curves = history?.curves;
    const live = this._liveSample(g);
    const now = Date.now();
    const series = [];
    const withLive = (points, v) => [...(points || []), [now, v ?? null]];
    if (mode.includes("setpoint")) series.push({ points: withLive(curves?.setpoint, live.group), cls: "set", step: true });
    if (mode.includes("ambient")) series.push({ points: withLive(curves?.ambient, live.mean), cls: "amb", step: false });
    if (mode.includes("outdoor")) {
      const v = history?.outdoorLive?.();
      series.push({ points: [...(history?.outdoor || []), ...(v !== undefined && v !== null ? [[now, v]] : [])], cls: "out", step: false });
    }
    // Pointillés : splits en dérogation (dans la journée ou maintenant)
    const dashed = [];
    for (const eid of g.info.climates) {
      const d = curves?.dashed?.[eid];
      const h = live.held[eid];
      if (!d?.any && !h) continue;
      const name = this._splitName(eid);
      const short = name.length > 10 ? `${name.slice(0, 9)}…` : name;
      if (mode.includes("setpoint")) dashed.push({ points: withLive(d?.setpoint, h ? h.temp : null), cls: "set dash", step: true, name, short });
      if (mode.includes("ambient")) dashed.push({ points: withLive(d?.ambient, h ? h.amb : null), cls: "amb dash", step: false, name, short });
    }
    if (mode.includes("setpoint")) legend.push(`<span><i class="lg set"></i>${esc(this._t(multi ? "t_setpoint_group" : "t_setpoint"))}</span>`);
    if (mode.includes("ambient")) legend.push(`<span><i class="lg amb"></i>${esc(this._t(multi ? "t_ambient_mean" : "t_ambient"))}</span>`);
    if (mode.includes("outdoor")) legend.push(`<span><i class="lg out"></i>${esc(this._t("t_outdoor"))}</span>`);
    if (dashed.some((d) => d.cls === "set dash")) legend.push(`<span><i class="lg set dash"></i>${esc(this._t("t_setpoint_held"))}</span>`);
    if (dashed.some((d) => d.cls === "amb dash")) legend.push(`<span><i class="lg amb dash"></i>${esc(this._t("t_ambient_held"))}</span>`);
    const all = [...series, ...dashed];
    const values = all.flatMap((x) => x.points.map(([, v]) => v)).filter((v) => v !== null && v !== undefined);
    if (!values.length) return `<div class="chart empty" style="height:${H}px"></div>`;
    let lo = Math.floor(Math.min(...values) - 0.5);
    let hi = Math.ceil(Math.max(...values) + 0.5);
    if (hi - lo < 2) { lo -= 1; hi += 1; }
    const y = (v) => (H - 4 - ((v - lo) / (hi - lo)) * (H - 8));
    const x = (t) => (this._pct(t, history) * 10);
    const labels = [];
    const paths = all.map((sr) => {
      let d = "";
      let previous = null;
      let end = null;
      for (const [t, v] of sr.points) {
        if (v === null || v === undefined) { previous = null; continue; }
        if (previous === null) d += `M${x(t).toFixed(1)} ${y(v).toFixed(1)}`;
        else if (sr.step) d += `H${x(t).toFixed(1)}V${y(v).toFixed(1)}`;
        else d += `L${x(t).toFixed(1)} ${y(v).toFixed(1)}`;
        previous = v;
        end = [x(t), y(v)];
      }
      if (sr.name && end) {
        labels.push(`<span class="clab ${sr.cls.split(" ")[0]}" style="left:${Math.min(end[0] / 10, 88).toFixed(2)}%;top:${Math.max(end[1] - 15, 0).toFixed(0)}px" title="${esc(sr.name)}">${esc(sr.short)}</span>`);
      }
      return d ? `<path class="${sr.cls}" d="${d}"><title>${esc(sr.name || "")}</title></path>` : "";
    }).join("");
    return `
      <div class="chart" style="height:${H}px">
        <svg viewBox="0 0 1000 ${H}" preserveAspectRatio="none" aria-hidden="true">
          <line class="grid" x1="0" x2="1000" y1="${y(hi).toFixed(1)}" y2="${y(hi).toFixed(1)}"></line>
          <line class="grid" x1="0" x2="1000" y1="${y(lo).toFixed(1)}" y2="${y(lo).toFixed(1)}"></line>
          ${paths}
          <line class="now" x1="${(Number(nowPct) * 10).toFixed(1)}" x2="${(Number(nowPct) * 10).toFixed(1)}" y1="0" y2="${H}"></line>
        </svg>
        <span class="ylab top">${this._fmt(hi, 0)}°</span><span class="ylab bottom">${this._fmt(lo, 0)}°</span>
        ${labels.join("")}
      </div>`;
  }

  /** Historique du jour (compresseur, ambiance, consigne) d'un groupe, relu toutes les 5 minutes. */
  _ensureHistory() {
    for (const g of this._groupConfigs()) {
      if (!g.info) continue;
      const needs = (g.compressor_timeline && g.info.compressor) || chartSeries(g.chart).length > 0;
      const cached = this._history[g.group];
      if (!needs || this._historyLoading.has(g.group)) continue;
      if (cached && Date.now() - cached.fetched < HISTORY_TTL && cached.key === this._historyKey(g)) continue;
      this._historyLoading.add(g.group);
      this._fetchHistory(g)
        .then((h) => { this._history[g.group] = h; })
        .catch(() => { this._history[g.group] = { fetched: Date.now(), key: this._historyKey(g), midnight: Date.now() }; })
        .finally(() => { this._historyLoading.delete(g.group); this._historyStamp++; this._render(); });
    }
  }

  _historyKey(g) {
    return [g.compressor_timeline, chartSeries(g.chart).join(","), g.temperature_entity, JSON.stringify(g.thermometers || {}), g.info.compressor, this._info.outdoor].join("|");
  }

  /** Valeurs actuelles des courbes (dernier point, mis à jour en direct). */
  _liveSample(g) {
    const states = this._hass.states;
    const thermo = thermometers(g, states);
    const num = (v) => (v === undefined || v === null || v === "" || Number.isNaN(Number(v)) ? null : Number(v));
    const stateOf = (eid) => {
      const c = states[eid];
      return c ? { s: c.state, temp: c.state === "off" ? null : num(c.attributes.temperature), cur: num(c.attributes.current_temperature) } : undefined;
    };
    const target = states[g.info.entities.target];
    const group = target ? num(target.state) : stateOf(g.info.climates[0])?.temp ?? null;
    return sampleAt(g.info.climates, stateOf, (eid) => (thermo[eid] ? num(states[thermo[eid]]?.state) : undefined), group);
  }

  async _fetchHistory(g) {
    const now = new Date(Date.now());
    const z = zonedNow(this._info.time_zone, now);
    const midnight = now.getTime() - (z.minutes * 60 + now.getSeconds()) * 1000 - now.getMilliseconds();
    const series = chartSeries(g.chart);
    const wantCurves = series.includes("ambient") || series.includes("setpoint");
    const outdoorEntity = series.includes("outdoor") ? this._info.outdoor : null;
    const wantCompressor = g.compressor_timeline && g.info.compressor;
    const base = {
      type: "history/history_during_period",
      start_time: new Date(midnight).toISOString(),
      end_time: now.toISOString(),
      include_start_time_state: true,
      significant_changes_only: false,
    };
    const curve = curveEntities(g, this._hass.states);
    const minimal = [...new Set([wantCompressor ? g.info.compressor : null, outdoorEntity, ...(wantCurves ? curve.minimal : [])].filter(Boolean))];
    const [sensorRows, climateRows] = await Promise.all([
      minimal.length ? this._hass.callWS({ ...base, entity_ids: minimal, minimal_response: true, no_attributes: true }) : {},
      wantCurves ? this._hass.callWS({ ...base, entity_ids: curve.full, minimal_response: false, no_attributes: false }) : {},
    ]);
    const time = (e) => Math.max(midnight, ((e.lu ?? e.lc) || 0) * 1000);
    const num = (v) => (v === undefined || v === null || v === "" || Number.isNaN(Number(v)) ? null : Number(v));
    const result = { fetched: Date.now(), key: this._historyKey(g), midnight, compEntity: wantCompressor ? g.info.compressor : null };
    if (wantCompressor) result.comp = (sensorRows[g.info.compressor] || []).map((e) => [time(e), e.s]);
    if (wantCurves) result.curves = groupCurves(g, climateRows, sensorRows, curve.thermo, time, num);
    if (outdoorEntity) {
      result.outdoor = (sensorRows[outdoorEntity] || []).map((e) => [time(e), num(e.s)]);
      result.outdoorLive = () => num(this._state(outdoorEntity)?.state);
    }
    return result;
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
      const offered = a.preset_modes || [];
      // « Normal » : home chez Faikout (none seulement s'il n'y a pas home)
      const presets = ["home", "none", "eco", "boost"].filter((p) => offered.includes(p) && !(p === "none" && offered.includes("home")));
      if (manual.includes("preset_mode") && presets.length > 1) {
        const labels = I18N[lang(this._hass)].presets;
        // Normal = home (ou none) : l'état courant « none » s'affiche aussi comme Normal
        const current = presets.includes(a.preset_mode) ? a.preset_mode : (["home", "none"].includes(a.preset_mode) ? presets.find((p) => p === "home" || p === "none") : a.preset_mode);
        const opts = presets.includes(current) || !current ? presets : [current, ...presets];
        rows.push(this._selectRow(`preset-${g.group}`, this._t("preset"), "preset_mode", g.group, opts, current, (p) => labels[p] || p));
      }
      if (manual.includes("swing_mode") && (a.swing_modes || []).length) {
        rows.push(`<div class="row between"><span>${esc(this._t("swing"))}</span>${this._segmented(a.swing_modes, a.swing_mode, "swing_mode", g.group)}</div>`);
      }
      if (rows.length) {
        const who = n > 1 ? ` <span class="muted">(${esc(this._t("manual_all"))})</span>` : "";
        parts.push(`<div class="col gap10"><span>${esc(this._t("manual"))}${who}</span>${rows.join("")}</div>`);
      }
    }
    const daikin = g.show_daikin === false ? [] : this._featureStates(g);
    if (daikin.length) {
      const L = I18N[lang(this._hass)];
      const buttons = daikin.map(({ key, on, available, pending }) => `<button type="button" class="feat ${on ? "on" : ""} ${pending ? "pending" : ""}" role="switch" aria-checked="${on}" data-action="feature" data-group="${gid}" data-value="${key}" title="${esc(L.feature_long[key])}${available ? "" : ` — ${esc(this._t("feat_unavailable"))}`}" ${available ? "" : "disabled"}>
        <span class="fi" aria-hidden="true">${FEATURE_ICONS[key]}</span><span class="fl">${esc(L.features[key])}${available ? "" : `<small> · ${esc(this._t("feat_unavailable"))}</small>`}${pending ? `<small> · ${esc(this._t("feat_wait"))}</small>` : ""}</span><i></i></button>`).join("");
      const msg = this._featMsg?.[g.group];
      parts.push(`<div class="col gap8"><span>${esc(this._t("daikin"))}${g.info.climates.length > 1 ? ` <span class="muted">(${esc(this._t("manual_all"))})</span>` : ""}</span><div class="feats">${buttons}</div>${msg ? `<span class="small err" role="alert">${esc(msg)}</span>` : ""}</div>`);
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
    const el = ev.target.closest("[data-action]");
    if (!el || el.tagName === "SELECT") return;
    const { action, group, value } = el.dataset;
    const g = group ? this._group(group) : null;
    const e = g?.info?.entities || {};
    const hass = this._hass;
    switch (action) {
      case "global-planning": {
        const current = this._state(this._info.global_planning)?.state;
        if (value === current) break;
        const n = this._groupConfigs().filter((x) => x.info).length;
        this._askConfirm(this._t("confirm_all").replace("{n}", n).replace("{p}", value),
          () => this._call(hass.callService("select", "select_option", { entity_id: this._info.global_planning, option: value })));
        break;
      }
      case "planning":
        if (value === this._state(e.planning)?.state) break;
        this._askConfirm(this._t("confirm_group").replace("{g}", g.info.name).replace("{p}", value),
          () => this._call(hass.callService("select", "select_option", { entity_id: e.planning, option: value })));
        break;
      case "confirm-ok": {
        const run = this._confirm?.run;
        this._closeConfirm();
        run?.();
        break;
      }
      case "confirm-cancel":
        this._closeConfirm();
        break;
      case "feature": {
        const item = this._featureStates(g).find((f) => f.key === value);
        if (!item) break;
        if (!item.available) break;
        this._featurePress(g, item);
        break;
      }
      case "split-resume":
        this._call(hass.callWS({ type: "split_scheduler/split_resume", group_id: group, entity_id: value }));
        break;
      case "profile":
        this._call(hass.callService("select", "select_option", { entity_id: e.profile, option: value }));
        break;
      case "reload":
        window.location.reload();
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
      case "splits":
        if (this._splitsOpen.has(group)) this._splitsOpen.delete(group);
        else this._splitsOpen.add(group);
        this._signature = "";
        this._render();
        break;
      case "open-split":
        this._openSplit(g, value);
        break;
      case "detail":
        SplitSchedulerHistory.open(this._hass, this._info, g);
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
      case "preset_mode":
        this._manual(group, { preset_mode: value });
        break;
      case "shift":
        this._call(this._hass.callWS({ type: "split_scheduler/override_shift", group_id: group, minutes: Number(value), ...(el.dataset.entity ? { entity_id: el.dataset.entity } : {}) }));
        break;
      default:
    }
  }

  /** Fenêtre de confirmation (changement de planning). */
  _askConfirm(text, run) {
    this._confirm = { text, run };
    this._signature = "";
    this._render();
    this.shadowRoot.querySelector(".confirm [data-action=confirm-cancel]")?.focus();
  }

  _closeConfirm() {
    this._confirm = null;
    this._signature = "";
    this._render();
  }

  _renderConfirm() {
    if (!this._confirm) return "";
    return `<div class="confirm" role="alertdialog" aria-modal="true" aria-labelledby="cf-t" aria-describedby="cf-d">
      <div class="confirm-box">
        <h3 id="cf-t">${esc(this._t("confirm_title"))}</h3>
        <p id="cf-d">${esc(this._confirm.text)}</p>
        <div class="row end2">
          <button type="button" class="outlined" data-action="confirm-cancel">${esc(this._t("cancel"))}</button>
          <button type="button" class="filled" data-action="confirm-ok">${esc(this._t("confirm_ok"))}</button>
        </div>
      </div>
    </div>`;
  }

  /** Appui sur une fonction Daikin : état affiché tout de suite, contrôle de la réponse du split. */
  async _featurePress(g, item) {
    const key = `${g.group}|${item.key}`;
    const want = !item.on;
    this._featPending = this._featPending || {};
    this._featMsg = this._featMsg || {};
    this._featPending[key] = { want };
    delete this._featMsg[g.group];
    this._signature = "";
    this._render();
    const L = I18N[lang(this._hass)];
    const fail = (who) => {
      delete this._featPending[key];
      this._featMsg[g.group] = this._t("feat_failed").replace("{f}", L.feature_long[item.key]).replace("{s}", who || "le split");
      this._signature = "";
      this._render();
    };
    let settings;
    if (item.key === "powerful") {
      const c = g.info.climates.map((eid) => this._state(eid)).find((x) => (x?.attributes?.preset_modes || []).includes("boost"));
      const normal = (c?.attributes?.preset_modes || []).includes("home") ? "home" : "none";
      settings = { preset_mode: want ? "boost" : normal };
    } else settings = { [item.key]: want };
    try {
      const res = await this._hass.callWS({ type: "split_scheduler/manual", group_id: g.group, ...settings });
      if (res?.non_appliques?.length) { fail(item.switches.join(", ")); return; }
    } catch (err) {
      fail(err?.message);
      return;
    }
    // Sans changement d'état du split au bout de 20 s : message
    setTimeout(() => { if (this._featPending?.[key]) fail(item.switches.join(", ")); }, 20000);
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

// ---------------------------------------------------------------------------- vue détaillée

const DAY = 86400000;
const PERIODS = { day: 1, "3d": 3, week: 7 };
const HISTORY_DAYS = 10; // historique détaillé conservé par défaut (recorder : purge_keep_days)

/** Valeur en vigueur à l'instant t dans une série [[t, v], ...] triée. */
function valueAt(series, t) {
  let lo = 0;
  let hi = (series?.length || 0) - 1;
  let found;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (series[mid][0] <= t) { found = series[mid][1]; lo = mid + 1; } else hi = mid - 1;
  }
  return found;
}

/** Fonctions Daikin (interrupteurs Faikout), dans l'ordre d'affichage. */
const FEATURE_ICONS = { comfort: "🧸", streamer: "🦠", sensor_mode: "🙆", quiet_outdoor: "🤫", powerful: "💪" };

/** Écart toléré entre la consigne d'un split et celle du groupe (comme l'intégration). */
const TOLERANCE = 0.3;

/** Thermomètre de chaque split : choisi par split, sinon l'ancien capteur unique du groupe. */
function thermometers(g, states) {
  const chosen = g.thermometers || {};
  const legacy = !Object.keys(chosen).length && g.temperature_entity && states[g.temperature_entity] && !g.temperature_entity.startsWith("climate.")
    ? g.temperature_entity : null;
  return Object.fromEntries(g.info.climates.map((eid) => [eid, chosen[eid] || legacy || null]));
}

/** Requêtes d'historique nécessaires aux courbes d'un groupe. */
function curveEntities(g, states) {
  const thermo = thermometers(g, states);
  return {
    thermo,
    full: [...g.info.climates],
    minimal: [g.info.entities.target, ...Object.values(thermo)].filter(Boolean),
  };
}

/**
 * Courbes d'un groupe à partir de l'historique :
 *  - setpoint : consigne du groupe (capteur « Consigne » ; avant lui, celle du premier split) ;
 *  - ambient : moyenne des thermomètres des splits qui suivent le programme ;
 *  - dashed : pour chaque split en dérogation (consigne différente de celle du groupe),
 *    sa consigne et son ambiance, null en dehors des dérogations.
 */
function groupCurves(g, full, minimal, thermo, time, num) {
  const climates = g.info.climates;
  const split = Object.fromEntries(climates.map((eid) => [eid, (full[eid] || []).map((e) => [time(e), {
    s: e.s, temp: e.s === "off" ? null : num(e.a?.temperature), cur: num(e.a?.current_temperature),
  }])]));
  const thermoRows = Object.fromEntries(Object.entries(thermo).filter(([, id]) => id).map(([eid, id]) => [eid, (minimal[id] || []).map((e) => [time(e), num(e.s)])]));
  const targetRows = g.info.entities.target ? (minimal[g.info.entities.target] || []).map((e) => [time(e), e.s === "unavailable" ? undefined : num(e.s)]) : [];
  const firstTarget = targetRows.length ? targetRows[0][0] : Infinity;
  const times = [...new Set([
    ...targetRows.map(([t]) => t), ...Object.values(split).flatMap((r) => r.map(([t]) => t)),
    ...Object.values(thermoRows).flatMap((r) => r.map(([t]) => t)),
  ])].sort((a, b) => a - b);
  const groupAt = (t) => (t >= firstTarget ? valueAt(targetRows, t) : valueAt(split[climates[0]], t)?.temp) ?? null;
  const out = { setpoint: [], ambient: [], dashed: Object.fromEntries(climates.map((eid) => [eid, { setpoint: [], ambient: [], any: false }])) };
  for (const t of times) {
    const sample = sampleAt(climates, (eid) => valueAt(split[eid], t), (eid) => (thermoRows[eid] ? valueAt(thermoRows[eid], t) : undefined), groupAt(t));
    out.setpoint.push([t, sample.group]);
    out.ambient.push([t, sample.mean]);
    for (const eid of climates) {
      const d = sample.held[eid];
      out.dashed[eid].setpoint.push([t, d ? d.temp : null]);
      out.dashed[eid].ambient.push([t, d ? d.amb : null]);
      if (d) out.dashed[eid].any = true;
    }
  }
  return out;
}

/** Valeurs à un instant : consigne du groupe, moyenne des splits qui suivent, splits en dérogation. */
function sampleAt(climates, stateOf, thermoOf, group) {
  const held = {};
  const ambs = [];
  for (const eid of climates) {
    const st = stateOf(eid);
    if (!st || ["unavailable", "unknown"].includes(st.s)) continue;
    const th = thermoOf(eid);
    const amb = th !== undefined ? th : st.cur;
    const deviates = group !== null && group !== undefined
      && (st.s === "off" || st.temp === null || st.temp === undefined || Math.abs(st.temp - group) > TOLERANCE);
    if (deviates) held[eid] = { temp: st.temp ?? null, amb: amb ?? null };
    else if (amb !== null && amb !== undefined) ambs.push(amb);
  }
  return { group: group ?? null, mean: ambs.length ? ambs.reduce((a, b) => a + b, 0) / ambs.length : null, n: ambs.length, held };
}

class SplitSchedulerHistory extends HTMLElement {
  static open(hass, info, group) {
    const dialog = document.createElement("split-scheduler-history");
    dialog._hass = hass;
    dialog._info = info;
    dialog._g = group;
    document.body.append(dialog);
    return dialog;
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._period = "day";
    this._offset = 0;
    this._show = { ambient: true, setpoint: true, outdoor: true, dashed: true };
    this._data = null;
    this._cursor = null;
    this._onKey = (ev) => { if (ev.key === "Escape") this.close(); };
  }

  connectedCallback() {
    document.addEventListener("keydown", this._onKey);
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this._load();
  }

  disconnectedCallback() {
    document.removeEventListener("keydown", this._onKey);
  }

  close() {
    this.remove();
  }

  _t(key) {
    return I18N[lang(this._hass)][key] ?? key;
  }

  _loc() {
    return this._hass?.locale?.language || this._hass?.language || "fr";
  }

  _fmt(v, d = 1) {
    return new Intl.NumberFormat(this._loc(), { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
  }

  _range() {
    const now = Date.now();
    const z = zonedNow(this._info.time_zone, new Date(now));
    const todayStart = now - (z.minutes * 60 + new Date(now).getSeconds()) * 1000 - new Date(now).getMilliseconds();
    const days = PERIODS[this._period];
    const end = todayStart + DAY - this._offset * days * DAY;
    return { start: end - days * DAY, end, now, days };
  }

  _canGoBack() {
    const { start, now } = this._range();
    return start > now - HISTORY_DAYS * DAY;
  }

  async _load() {
    this._data = null;
    this._render();
    const { start, end, now } = this._range();
    const g = this._g;
    const curve = curveEntities(g, this._hass.states);
    const sensors = [...new Set([g.info.compressor, this._info.outdoor, ...curve.minimal].filter(Boolean))];
    const base = {
      type: "history/history_during_period",
      start_time: new Date(start).toISOString(),
      end_time: new Date(Math.min(end, now)).toISOString(),
      include_start_time_state: true,
      significant_changes_only: false,
    };
    try {
      const [sensorRows, fullRows] = await Promise.all([
        sensors.length ? this._hass.callWS({ ...base, entity_ids: sensors, minimal_response: true, no_attributes: true }) : {},
        this._hass.callWS({ ...base, entity_ids: [...curve.full, g.info.entities.profile].filter(Boolean), minimal_response: false, no_attributes: false }),
      ]);
      const time = (e) => Math.max(start, ((e.lu ?? e.lc) || 0) * 1000);
      const num = (v) => (v === undefined || v === null || v === "" || Number.isNaN(Number(v)) ? null : Number(v));
      const curves = groupCurves(g, fullRows, sensorRows, curve.thermo, time, num);
      const profileRows = fullRows[g.info.entities.profile] || [];
      let first = Infinity;
      for (const rows of [...Object.values(sensorRows), ...Object.values(fullRows)]) {
        if (rows.length) first = Math.min(first, ((rows[0].lu ?? rows[0].lc) || 0) * 1000);
      }
      this._data = {
        first,
        ambient: curves.ambient,
        setpoint: curves.setpoint,
        dashed: Object.entries(curves.dashed).filter(([, v]) => v.any).map(([eid, v]) => ({
          eid, name: this._hass.states[eid]?.attributes?.friendly_name || eid, setpoint: v.setpoint, ambient: v.ambient,
        })),
        outdoor: this._info.outdoor ? (sensorRows[this._info.outdoor] || []).map((e) => [time(e), num(e.s)]) : [],
        comp: g.info.compressor ? (sensorRows[g.info.compressor] || []).map((e) => [time(e), num(e.s)]) : [],
        profile: profileRows.map((e) => [time(e), { name: e.s, adapted: e.a?.adaptation_exterieure === true }]),
      };
    } catch (err) {
      this._data = { error: err?.message || String(err) };
    }
    this._render();
  }

  _onClick(ev) {
    if (ev.target === this.shadowRoot.querySelector(".backdrop")) { this.close(); return; }
    const el = ev.target.closest("[data-act]");
    if (!el) return;
    const { act, value } = el.dataset;
    if (act === "close") this.close();
    if (act === "period") { this._period = value; this._offset = 0; this._load(); }
    if (act === "prev" && this._canGoBack()) { this._offset += 1; this._load(); }
    if (act === "next" && this._offset > 0) { this._offset -= 1; this._load(); }
    if (act === "toggle") { this._show[value] = !this._show[value]; this._render(); }
  }

  _profileColor(name) {
    return this._info.profiles.find((p) => p.name === name)?.color || "var(--divider-color)";
  }

  _render() {
    const { start, end, now, days } = this._range();
    const g = this._g;
    const mobile = window.innerWidth < 600;
    const span = end - start;
    const pct = (t) => (((Math.min(Math.max(t, start), end) - start) / span) * 100);
    const last = Math.min(end, now);
    const date = (t, opts) => new Intl.DateTimeFormat(this._loc(), { timeZone: this._info.time_zone, ...opts }).format(new Date(t));
    const title = days === 1
      ? date(start + 1, { weekday: "long", day: "numeric", month: "long" })
      : `${date(start + 1, { weekday: "short", day: "numeric" })} – ${date(end - 1, { weekday: "short", day: "numeric", month: "short" })}`;
    const d = this._data;

    let body;
    if (!d) body = `<div class="msg">${esc(this._t("loading"))}</div>`;
    else if (d.error) body = `<div class="msg err">${esc(d.error)}</div>`;
    else body = this._renderBody(d, { start, end, now, last, pct, days, mobile });

    const periods = Object.keys(PERIODS).map((p) => `<button type="button" class="${p === this._period ? "on" : ""}" aria-pressed="${p === this._period}" data-act="period" data-value="${p}">${esc(this._t(`p_${p}`))}</button>`).join("");
    const multi = g.info.climates.length > 1;
    const toggles = [["setpoint", "set", this._t(multi ? "t_setpoint_group" : "t_setpoint")], ["ambient", "amb", this._t(multi ? "t_ambient_mean" : "t_ambient")],
      ...(d?.dashed?.length ? [["dashed", "set dash", this._t("t_dashed")]] : []), ...(this._info.outdoor ? [["outdoor", "out", this._t("t_outdoor")]] : [])]
      .map(([k, cls, label]) => `<button type="button" class="tog ${this._show[k] ? "on" : ""}" aria-pressed="${this._show[k]}" data-act="toggle" data-value="${k}"><i class="lg ${cls}"></i>${esc(label)}</button>`).join("");
    const since = d && Number.isFinite(d.first) && d.first > start + 60000
      ? `<span class="muted small">${esc(this._t("available_since").replace("{d}", date(d.first, { day: "numeric", month: "long" })))}</span>` : "";

    this.shadowRoot.innerHTML = `<style>${HISTORY_CSS}</style>
      <div class="backdrop">
        <section class="dlg ${mobile ? "mobile" : ""}" role="dialog" aria-modal="true" aria-label="${esc(this._t("history").replace("{g}", g.info.name))}">
          <header>
            ${mobile ? `<button type="button" class="icon" data-act="close" aria-label="${esc(this._t("close"))}">${svg(ICONS.left, 22)}</button>` : ""}
            <h1>${esc(this._t("history").replace("{g}", g.info.name))}</h1>
            ${mobile ? "" : `<button type="button" class="icon" data-act="close" aria-label="${esc(this._t("close"))}">${svg(ICONS.close, 22)}</button>`}
          </header>
          <div class="tools">
            <div class="seg" role="group">${periods}</div>
            <div class="nav">
              <button type="button" class="icon round" data-act="prev" aria-label="${esc(this._t("prev"))}" ${this._canGoBack() ? "" : "disabled"}>${svg(ICONS.left, 18)}</button>
              <span class="when">${esc(title)}</span>
              <button type="button" class="icon round" data-act="next" aria-label="${esc(this._t("next_p"))}" ${this._offset > 0 ? "" : "disabled"}>${svg(ICONS.right, 18)}</button>
            </div>
            <div class="togs">${toggles}</div>
            ${since}
          </div>
          ${body}
        </section>
      </div>`;
    this.shadowRoot.querySelector("[data-act=close]")?.focus({ preventScroll: true });
    this._bindCursor({ start, end, last, pct, mobile });
  }

  _renderBody(d, { start, end, now, last, pct, days, mobile }) {
    // Profils réellement appliqués
    const profileBlocks = [];
    for (let i = 0; i < d.profile.length; i++) {
      const [t, p] = d.profile[i];
      const until = i + 1 < d.profile.length ? d.profile[i + 1][0] : last;
      if (until <= t || ["unknown", "unavailable"].includes(p.name)) continue;
      profileBlocks.push(`<span title="${esc(p.name)}" style="left:${pct(t).toFixed(3)}%;width:${(pct(until) - pct(t)).toFixed(3)}%;background:${this._profileColor(p.name)}"></span>`);
    }
    // Compresseur
    const runs = [];
    let on = null;
    let was = null;
    let starts = 0;
    for (const [t, v] of d.comp) {
      if (v === null) continue;
      if (v > 0 && on === null) { on = t; if (was === false) starts++; }
      else if (v <= 0 && on !== null) { runs.push([on, t]); on = null; }
      was = v > 0;
    }
    if (on !== null) runs.push([on, last]);
    const observedFrom = Number.isFinite(d.first) ? Math.max(start, d.first) : start;
    const hours = Math.max((last - observedFrom) / 3600000, 1 / 60);
    const compBlocks = runs.map(([a, b]) => `<i style="left:${pct(a).toFixed(3)}%;width:${Math.max(pct(b) - pct(a), 0.12).toFixed(3)}%"></i>`).join("");
    const compRow = this._g.info.compressor ? `
      <span class="lab">${esc(this._t("compressor_band"))}</span><div class="cband">${compBlocks}</div>
      <span></span><span class="muted small">${esc(plural(this._t("starts_period"), starts).replace("{r}", this._fmt(starts / hours)))}</span>` : "";

    // Courbes
    const H = mobile ? 250 : 360;
    const visible = [["ambient", "amb", false], ["setpoint", "set", true], ["outdoor", "out", false]].filter(([k]) => this._show[k] && d[k]?.length)
      .map(([k, cls, step]) => ({ points: d[k], cls, step }));
    if (this._show.dashed) {
      for (const x of d.dashed || []) {
        if (this._show.setpoint) visible.push({ points: x.setpoint, cls: "set dash", step: true, name: x.name });
        if (this._show.ambient) visible.push({ points: x.ambient, cls: "amb dash", step: false, name: x.name });
      }
    }
    const values = visible.flatMap((sr) => sr.points.map(([, v]) => v)).filter((v) => v !== null && v !== undefined);
    let chart = `<div class="msg">${esc(this._t("no_data"))}</div>`;
    if (values.length) {
      let lo = Math.floor(Math.min(...values) - 0.5);
      let hi = Math.ceil(Math.max(...values) + 0.5);
      if (hi - lo < 4) { lo -= 2; hi += 2; }
      const stepY = hi - lo > 16 ? 4 : 2;
      lo = Math.floor(lo / stepY) * stepY;
      hi = Math.ceil(hi / stepY) * stepY;
      const y = (v) => (H - ((v - lo) / (hi - lo)) * H).toFixed(1);
      const x = (t) => (pct(t) * 10).toFixed(1);
      const paths = visible.map(({ points, cls, step, name }) => {
        let path = "";
        let prev = null;
        for (const [t, v] of [...points, [last, points.at(-1)?.[1] ?? null]]) {
          if (v === null || v === undefined) { prev = null; continue; }
          if (prev === null) path += `M${x(t)} ${y(v)}`;
          else if (step) path += `H${x(t)}V${y(v)}`;
          else path += `L${x(t)} ${y(v)}`;
          prev = v;
        }
        return path ? `<path class="${cls}" d="${path}">${name ? `<title>${esc(name)}</title>` : ""}</path>` : "";
      }).join("");
      const grid = [];
      const labels = [];
      for (let v = lo; v <= hi; v += stepY) {
        grid.push(`<line class="grid" x1="0" x2="1000" y1="${y(v)}" y2="${y(v)}"></line>`);
        labels.push(`<span style="top:${((1 - (v - lo) / (hi - lo)) * 100).toFixed(2)}%">${v} °C</span>`);
      }
      for (let k = 1; k < days; k++) grid.push(`<line class="day" x1="${(k / days * 1000).toFixed(1)}" x2="${(k / days * 1000).toFixed(1)}" y1="0" y2="${H}"></line>`);
      const nowLine = now < end ? `<line class="now" x1="${x(now)}" x2="${x(now)}" y1="0" y2="${H}"></line>` : "";
      chart = `
        <div class="ylabels">${labels.join("")}</div>
        <div class="plot" style="height:${H}px">
          <svg viewBox="0 0 1000 ${H}" preserveAspectRatio="none" aria-hidden="true">${grid.join("")}${paths}${nowLine}<line class="cursor" x1="0" x2="0" y1="0" y2="${H}" visibility="hidden"></line></svg>
          <div class="tip" hidden></div>
        </div>`;
    }
    // Axe du temps
    const ticks = [];
    const date = (t, o) => new Intl.DateTimeFormat(this._loc(), { timeZone: this._info.time_zone, ...o }).format(new Date(t));
    if (days === 1) ["0 h", "6 h", "12 h", "18 h", "24 h"].forEach((l, i) => ticks.push(`<span style="left:${i * 25}%">${l}</span>`));
    else {
      // 3 jours : nom du jour au début de la journée, « 12 h » au milieu ; semaine : jour centré dans sa colonne
      const narrow = mobile && days > 3;
      for (let k = 0; k < days; k++) {
        const label = esc(date(start + k * DAY + 3600000, narrow ? { day: "numeric" } : { weekday: "short", day: "numeric" }));
        if (days <= 3) {
          ticks.push(`<span class="start" style="left:${(k / days * 100).toFixed(2)}%">${label}</span>`);
          ticks.push(`<span style="left:${((k + 0.5) / days * 100).toFixed(2)}%">12 h</span>`);
        } else ticks.push(`<span style="left:${((k + 0.5) / days * 100).toFixed(2)}%">${label}</span>`);
      }
    }
    return `
      <div class="bands">
        <span class="lab">${esc(this._t("profiles_band"))}</span><div class="pband">${profileBlocks.join("")}</div>
        ${compRow}
      </div>
      <div class="chartwrap">${chart}</div>
      <div class="xaxis">${ticks.join("")}</div>
      ${mobile ? `<div class="panel" hidden></div><span class="muted small center">${esc(this._t("touch_hint"))}</span>` : ""}`;
  }

  _bindCursor({ start, end, last, pct, mobile }) {
    const plot = this.shadowRoot.querySelector(".plot");
    const d = this._data;
    if (!plot || !d || d.error) return;
    const line = plot.querySelector(".cursor");
    const tip = plot.querySelector(".tip");
    const panel = this.shadowRoot.querySelector(".panel");
    const time = (t, o) => new Intl.DateTimeFormat(this._loc(), { timeZone: this._info.time_zone, ...o }).format(new Date(t));
    const show = (clientX) => {
      const box = plot.getBoundingClientRect();
      const ratio = Math.min(Math.max((clientX - box.left) / box.width, 0), 1);
      const t = Math.min(start + ratio * (end - start), last);
      const x = ((t - start) / (end - start)) * 1000;
      line.setAttribute("x1", x); line.setAttribute("x2", x); line.setAttribute("visibility", "visible");
      const p = valueAt(d.profile, t);
      const c = valueAt(d.comp, t);
      const row = (cls, label, v) => (v === undefined || v === null ? "" : `<span class="r"><span><i class="lg ${cls}"></i>${esc(label)}</span><strong>${this._fmt(v)} °C</strong></span>`);
      const html = `
        <strong class="h">${esc(time(t, { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }))}</strong>
        ${p ? `<span class="r"><span><i class="dot" style="background:${this._profileColor(p.name)}"></i>${esc(p.name)}${p.adapted ? ` <em>(${esc(this._t("adapted_short"))})</em>` : ""}</span></span>` : ""}
        ${this._show.setpoint ? row("set", this._t(this._g.info.climates.length > 1 ? "t_setpoint_group" : "t_setpoint"), valueAt(d.setpoint, t)) : ""}
        ${this._show.ambient ? row("amb", this._t(this._g.info.climates.length > 1 ? "t_ambient_mean" : "t_ambient"), valueAt(d.ambient, t)) : ""}
        ${this._show.outdoor && this._info.outdoor ? row("out", this._t("t_outdoor"), valueAt(d.outdoor, t)) : ""}
        ${this._show.dashed ? (d.dashed || []).map((x) => {
          const sp = valueAt(x.setpoint, t);
          const am = valueAt(x.ambient, t);
          if ((sp === null || sp === undefined) && (am === null || am === undefined)) return "";
          return `<span class="sep"></span><span class="r held"><span>${esc(this._t("held_since").replace("{s}", x.name))}</span></span>${row("set dash", this._t("t_setpoint"), sp)}${row("amb dash", this._t("t_ambient"), am)}`;
        }).join("") : ""}
        ${this._g.info.compressor && c !== undefined && c !== null ? `<span class="r"><span>${esc(this._t("compressor_band"))}</span><strong>${esc(c > 0 ? `${this._t("running")} · ${Math.round(c)} Hz` : this._t("stopped"))}</strong></span>` : ""}`;
      const empty = !p && [d.setpoint, d.ambient, d.outdoor, d.comp].every((serie) => valueAt(serie, t) == null);
      const content = empty ? `${html}<span class="muted">${esc(this._t("no_data_at"))}</span>` : html;
      if (mobile && panel) { panel.innerHTML = content; panel.hidden = false; }
      else {
        tip.innerHTML = content;
        tip.hidden = false;
        const left = (ratio * box.width) + 14;
        tip.style.left = `${left + 260 > box.width ? ratio * box.width - 274 : left}px`;
      }
    };
    plot.addEventListener("pointermove", (ev) => show(ev.clientX));
    plot.addEventListener("pointerdown", (ev) => show(ev.clientX));
    plot.addEventListener("pointerleave", () => {
      if (!mobile) { tip.hidden = true; line.setAttribute("visibility", "hidden"); }
    });
  }
}

const HISTORY_CSS = `
  :host { position: fixed; inset: 0; z-index: 9999; font-family: var(--ha-font-family-body, Roboto, system-ui, sans-serif); color: var(--primary-text-color); }
  .backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; padding: 24px; box-sizing: border-box; }
  .dlg { background: var(--card-background-color, #fff); border-radius: 24px; box-shadow: 0 16px 48px rgba(0,0,0,.35); width: min(1180px, 100%); max-height: 100%; overflow: auto; box-sizing: border-box; padding: 18px 24px 22px; display: flex; flex-direction: column; gap: 14px; }
  .dlg.mobile { position: fixed; inset: 0; width: 100%; height: 100%; max-height: none; border-radius: 0; padding: 10px 16px 16px; }
  header { display: flex; align-items: center; gap: 8px; }
  h1 { margin: 0; font-size: 20px; font-weight: 500; flex: 1; }
  button { font: inherit; color: inherit; cursor: pointer; }
  .icon { width: 44px; height: 44px; border: 0; border-radius: 22px; background: none; display: inline-flex; align-items: center; justify-content: center; color: var(--primary-text-color); }
  .icon.round { width: 40px; height: 40px; border: 1px solid var(--divider-color); }
  .icon:disabled { opacity: .35; cursor: default; }
  .tools { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 18px; }
  .dlg.mobile .tools { flex-direction: column; align-items: stretch; }
  .seg { display: inline-flex; gap: 2px; padding: 3px; border-radius: 20px; background: ${mix("var(--primary-text-color)", 8)}; }
  .dlg.mobile .seg { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .seg button { min-height: 36px; padding: 0 14px; border: 0; border-radius: 17px; background: none; font-size: 13.5px; }
  .seg button.on { background: var(--primary-color); color: var(--text-primary-color, #fff); font-weight: 500; }
  .nav { display: flex; align-items: center; gap: 6px; justify-content: space-between; }
  .when { min-width: 200px; text-align: center; font-weight: 500; font-size: 14.5px; }
  .togs { display: flex; flex-wrap: wrap; gap: 8px; }
  .tog { display: inline-flex; align-items: center; gap: 7px; min-height: 36px; padding: 0 12px; border-radius: 18px; border: 1px solid var(--divider-color); background: none; font-size: 13px; opacity: .55; }
  .tog.on { opacity: 1; border-color: var(--primary-color); }
  .muted { color: var(--secondary-text-color); } .small { font-size: 12px; } .center { text-align: center; }
  .bands { display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: 8px 12px; align-items: center; }
  .dlg.mobile .bands { grid-template-columns: 1fr; gap: 4px; }
  /* même départ que les courbes (colonne des °C : 44 px + 6 px) */
  .dlg.mobile .pband, .dlg.mobile .cband { margin-left: 50px; }
  .lab { font-size: 12.5px; color: var(--secondary-text-color); }
  .pband { position: relative; height: 22px; border-radius: 6px; background: ${mix("var(--primary-text-color)", 6)}; overflow: hidden; }
  .pband span { position: absolute; top: 0; bottom: 0; }
  .cband { position: relative; height: 14px; border-radius: 5px; background: ${mix("var(--primary-text-color)", 7)}; overflow: hidden; }
  .cband i { position: absolute; top: 0; bottom: 0; background: ${mix("var(--primary-color)", 45)}; border-left: 2px solid var(--primary-color); box-sizing: border-box; }
  .chartwrap { display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: 0 12px; }
  .dlg.mobile .chartwrap { grid-template-columns: 44px minmax(0, 1fr); gap: 0 6px; }
  .chartwrap > .msg { grid-column: 1 / -1; }
  .ylabels { position: relative; }
  .ylabels span { position: absolute; right: 0; transform: translateY(-50%); font-size: 11.5px; color: var(--secondary-text-color); white-space: nowrap; }
  .plot { position: relative; touch-action: none; cursor: crosshair; }
  .plot svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
  path { fill: none; stroke-width: 2; vector-effect: non-scaling-stroke; stroke-linejoin: round; }
  path.amb { stroke: var(--primary-color); stroke-width: 2.2; }
  path.set { stroke: var(--warning-color, #ffa000); stroke-width: 2.2; }
  path.dash { stroke-dasharray: 6 4; stroke-width: 1.8; }
  path.out { stroke: var(--error-color, #e53935); stroke-dasharray: 2 3; }
  line.grid { stroke: var(--divider-color); stroke-width: 1; vector-effect: non-scaling-stroke; }
  line.day { stroke: var(--secondary-text-color); stroke-width: 1; vector-effect: non-scaling-stroke; opacity: .35; }
  line.now { stroke: var(--primary-text-color); stroke-width: 1; vector-effect: non-scaling-stroke; stroke-dasharray: 3 3; opacity: .6; }
  line.cursor { stroke: var(--primary-text-color); stroke-width: 1.2; vector-effect: non-scaling-stroke; opacity: .75; }
  .tip { position: absolute; top: 10px; width: 260px; box-sizing: border-box; padding: 10px 12px; border-radius: 12px; border: 1px solid var(--divider-color); background: var(--card-background-color, #fff); box-shadow: 0 6px 18px rgba(0,0,0,.18); display: flex; flex-direction: column; gap: 6px; font-size: 13px; pointer-events: none; }
  .panel { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 12px; padding: 12px 14px; border-radius: 14px; border: 1px solid var(--divider-color); background: ${mix("var(--primary-text-color)", 4)}; font-size: 13px; }
  .panel .h { grid-column: 1 / -1; }
  .r { display: flex; justify-content: space-between; gap: 8px; }
  .panel .r { flex-direction: column; gap: 2px; }
  .r em { font-style: normal; color: var(--info-color, #039be5); }
  .h { font-size: 13.5px; }
  .sep { grid-column: 1 / -1; height: 1px; background: var(--divider-color); }
  .r.held { grid-column: 1 / -1; color: ${mix("var(--warning-color, #ffa000)", 75, "var(--primary-text-color)")}; font-weight: 500; }
  .lg { display: inline-block; width: 14px; height: 0; border-top: 2px solid; margin-right: 6px; vertical-align: middle; }
  .lg.amb { border-color: var(--primary-color); }
  .lg.set { border-color: var(--warning-color, #ffa000); }
  .lg.dash { border-top-style: dashed; }
  .lg.out { border-color: var(--error-color, #e53935); border-top-style: dotted; }
  .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
  .xaxis { position: relative; height: 16px; margin-left: 108px; font-size: 11.5px; color: var(--secondary-text-color); }
  .dlg.mobile .xaxis { margin-left: 50px; }
  .xaxis span { position: absolute; transform: translateX(-50%); white-space: nowrap; }
  .xaxis span.start, .xaxis span[style="left:0%"] { transform: none; }
  .xaxis span[style="left:100%"] { transform: translateX(-100%); }
  .tip[hidden], .panel[hidden] { display: none; }
  .msg { padding: 40px 0; text-align: center; color: var(--secondary-text-color); }
  .err { color: var(--error-color, #db4437); }
  button:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
`;

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
  .banner.compact { flex-direction: column; align-items: stretch; gap: 2px; padding: 6px 6px 6px 12px; }
  .banner.compact .row { gap: 5px; }
  .banner.compact span { flex: none; }
  .banner.compact .when { flex: 1; min-width: 0; display: flex; align-items: baseline; gap: 5px; white-space: nowrap; }
  .banner.compact .when strong { font-size: 18px; font-weight: 500; }
  .banner.compact .note { color: var(--secondary-text-color); }
  .banner.compact .resume { width: 40px; min-height: 40px; padding: 0; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .shift { padding: 0 7px; flex-shrink: 0; white-space: nowrap; min-height: 40px; border-radius: 20px; border: 1px solid ${mix("var(--warning-color, #ffa000)", 70, "var(--primary-text-color)")}; background: var(--card-background-color, #fff); font-weight: 500; font-size: 13px; }
  .bar .hatch { position: absolute; top: 0; bottom: 0; background: repeating-linear-gradient(135deg, rgba(0,0,0,.35) 0 3px, transparent 3px 7px); }
  .timeline { display: flex; flex-direction: column; gap: 5px; }
  .bar { position: relative; display: flex; height: 12px; border-radius: 6px; overflow: hidden; }
  .bar b { position: absolute; top: 0; bottom: 0; width: 3px; margin-left: -1px; background: var(--primary-text-color); border-radius: 2px; }
  .ticks { position: relative; height: 14px; font-size: 11px; line-height: 14px; color: var(--secondary-text-color); }
  .ticks span { position: absolute; top: 0; transform: translateX(-50%); white-space: nowrap; }
  .ticks span:first-child { transform: none; }
  .ticks span:last-child { transform: translateX(-100%); }
  .cbar { position: relative; height: 8px; border-radius: 4px; background: ${mix("var(--primary-text-color)", 7)}; overflow: hidden; }
  .cbar i { position: absolute; top: 0; bottom: 0; background: ${mix("var(--primary-color)", 45)}; }
  .cbar u { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--primary-color); }
  .cbar b { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--primary-text-color); }
  .chart { position: relative; }
  .chart svg { display: block; width: 100%; height: 100%; overflow: visible; }
  .chart path { fill: none; stroke-width: 2; vector-effect: non-scaling-stroke; stroke-linejoin: round; }
  .chart path.amb { stroke: var(--primary-color); }
  .chart path.set { stroke: var(--warning-color, #ffa000); }
  .chart path.out { stroke: var(--error-color, #e53935); stroke-dasharray: 2 3; }
  .chart path.dash { stroke-dasharray: 5 4; stroke-width: 1.8; }
  .clab { position: absolute; font-size: 10.5px; line-height: 14px; font-weight: 500; padding: 0 3px; border-radius: 3px; background: var(--ha-card-background, var(--card-background-color, #fff)); white-space: nowrap; pointer-events: auto; }
  .clab.set { color: ${mix("var(--warning-color, #ffa000)", 75, "var(--primary-text-color)")}; }
  .clab.amb { color: ${mix("var(--primary-color)", 80, "var(--primary-text-color)")}; }
  .chart .grid { stroke: var(--divider-color); stroke-width: 1; vector-effect: non-scaling-stroke; }
  .chart .now { stroke: var(--primary-text-color); stroke-width: 1.5; vector-effect: non-scaling-stroke; opacity: .6; }
  .chart.empty { background: ${mix("var(--primary-text-color)", 4)}; border-radius: 6px; }
  .ylab { position: absolute; left: 0; font-size: 10px; line-height: 1; color: var(--secondary-text-color); background: var(--ha-card-background, var(--card-background-color, #fff)); padding: 0 2px; border-radius: 3px; }
  .ylab.top { top: -2px; } .ylab.bottom { bottom: -2px; }
  .gname { display: inline-flex; align-items: center; gap: 8px; min-height: 40px; padding: 0 6px 0 0; border: 0; background: none; color: var(--primary-text-color); text-align: left; }
  .gname svg { color: var(--secondary-text-color); }
  .splitrow { display: flex; align-items: center; border-top: 1px solid var(--divider-color); background: var(--card-background-color, #fff); }
  .splitrow:first-child { border-top: 0; }
  .splitrow .split { flex: 1; min-width: 0; border-top: 0; background: none; }
  .splitrow.held { background: ${mix("var(--warning-color, #ffa000)", 9, "var(--card-background-color, #fff)")}; box-shadow: inset 3px 0 0 var(--warning-color, #ffa000); }
  .splitrow .resume { width: 40px; min-height: 40px; padding: 0; margin-right: 10px; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .feats { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
  .feat { display: flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 10px; border-radius: 12px; border: 1px solid var(--divider-color); background: var(--card-background-color, #fff); color: var(--primary-text-color); font: inherit; font-size: 13.5px; text-align: left; cursor: pointer; }
  .feat.on { border-color: var(--primary-color); background: ${mix("var(--primary-color)", 10, "var(--card-background-color, #fff)")}; }
  .feat .fi { font-size: 17px; }
  .feat .fl { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .feat i { position: relative; width: 32px; height: 18px; border-radius: 9px; background: var(--disabled-color, #bdc1c6); flex-shrink: 0; }
  .feat i::after { content: ""; position: absolute; top: 2px; left: 2px; width: 14px; height: 14px; border-radius: 50%; background: #fff; transition: left .15s; }
  .feat.on i { background: var(--primary-color); }
  .feat.on i::after { left: 16px; }
  .feat.pending { opacity: .7; }
  .feat:disabled { opacity: .5; cursor: default; }
  .feat small { color: var(--secondary-text-color); font-size: 11.5px; }
  .fchips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: -4px; }
  .bigrow { white-space: nowrap; }
  .status { min-width: 0; overflow: hidden; flex-shrink: 1; }
  .gname { flex-shrink: 0; white-space: nowrap; }
  .fchip { display: inline-flex; align-items: center; height: 22px; padding: 0 8px; border-radius: 11px; background: ${mix("var(--primary-text-color)", 7)}; font-size: 11.5px; white-space: nowrap; }
  .chip.held { background: ${mix("var(--warning-color, #ffa000)", 16)}; }
  .devi { color: ${mix("var(--warning-color, #ffa000)", 75, "var(--primary-text-color)")}; font-weight: 500; }
  .status .ell { overflow: hidden; text-overflow: ellipsis; }
  .status { max-width: 60%; }
  .banner.compact .who { font-size: 14px; font-weight: 500; }
  .banner.compact .head { display: block; padding-top: 4px; overflow-wrap: anywhere; }
  .confirm { position: fixed; inset: 0; z-index: 10; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(0,0,0,.45); }
  .confirm-box { width: min(420px, 100%); box-sizing: border-box; padding: 20px; border-radius: 20px; background: var(--card-background-color, #fff); color: var(--primary-text-color); box-shadow: 0 10px 30px rgba(0,0,0,.3); display: flex; flex-direction: column; gap: 12px; }
  .confirm-box h3 { margin: 0; font-size: 19px; font-weight: 500; }
  .confirm-box p { margin: 0; font-size: 14px; line-height: 20px; color: var(--secondary-text-color); }
  .confirm-box .end2 { justify-content: flex-end; gap: 8px; }
  .splits { display: flex; flex-direction: column; border: 1px solid var(--divider-color); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 14px rgba(0,0,0,.08); }
  .split { display: flex; align-items: center; gap: 12px; min-height: 56px; padding: 8px 12px; border: 0; border-top: 1px solid var(--divider-color); background: var(--card-background-color, #fff); color: var(--primary-text-color); text-align: left; }
  .split:first-child { border-top: 0; }
  .split i { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .split .col { flex: 1; min-width: 0; gap: 2px; }
  .split strong { font-weight: 500; font-size: 14.5px; }
  .split svg { color: var(--secondary-text-color); flex-shrink: 0; }
  .split:hover { background: ${mix("var(--primary-color)", 6, "var(--card-background-color, #fff)")}; }
  .err { color: var(--error-color, #db4437); }
  .timeline[data-action] { cursor: pointer; border-radius: 8px; }
  .timeline[data-action]:hover .bar, .timeline[data-action]:hover .chart { filter: brightness(1.04); }
  .timeline:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 4px; }
  .legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 11.5px; color: var(--secondary-text-color); }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  .lg { display: inline-block; width: 14px; height: 0; border-top: 2px solid; }
  .lg.amb { border-color: var(--primary-color); }
  .lg.set { border-color: var(--warning-color, #ffa000); }
  .lg.dash { border-top-style: dashed; }
  .lg.out { border-color: var(--error-color, #e53935); border-top-style: dotted; }
  .bigrow { align-items: flex-end; gap: 10px; flex-wrap: wrap; }
  .adapted { display: inline-flex; align-items: center; gap: 5px; height: 24px; margin-bottom: 4px; padding: 0 9px; border-radius: 12px; font-size: 12px; font-weight: 500; background: ${mix("var(--info-color, #039be5)", 16)}; color: ${mix("var(--info-color, #039be5)", 70, "var(--primary-text-color)")}; }
  .banner.info { background: ${mix("var(--info-color, #039be5)", 13)}; }
  .banner.info svg { flex-shrink: 0; color: ${mix("var(--info-color, #039be5)", 80, "var(--primary-text-color)")}; }
  .lg.run { height: 8px; border: 0; border-radius: 2px; background: ${mix("var(--primary-color)", 45)}; box-shadow: inset 2px 0 var(--primary-color); }
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
    form.addEventListener("value-changed", (ev) => {
      form.data = ev.detail.value;
      onChange(ev.detail.value);
    });
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
    const manualOptions = ["temperature", "fan_mode", "swing_mode", "preset_mode", "hvac_mode"].map((v) => ({ value: v, label: this._t(`m_${v}`) }));
    const compressorOptions = ["avg_24h", "avg_profile"].map((v) => ({ value: v, label: this._t(`o_${v}`) }));
    const chartOptions = ["ambient", "setpoint", "outdoor"].map((v) => ({ value: v, label: this._t(`ch_${v}`) }));
    const infoById = Object.fromEntries((this._info?.groups || []).map((g) => [g.id, g]));

    groups.forEach((group, index) => {
      const details = document.createElement("details");
      details.dataset.group = group.group;
      if (open.has(group.group)) details.open = true;
      const summary = document.createElement("summary");
      summary.textContent = names[group.group] || group.group;
      details.append(summary);
      const data = { ...GROUP_DEFAULTS, ...group, chart: chartSeries(group.chart) };
      delete data.sensor_names;
      const namesBox = document.createElement("div");
      namesBox.className = "names";
      const fillNames = (sensors, names) => {
        namesBox.replaceChildren();
        if (!sensors.length) return;
        const title = document.createElement("p");
        title.className = "hint";
        title.textContent = this._t("e_sensor_names");
        const form = this._form(
          Object.fromEntries(sensors.map((id) => [id, names[id] || ""])),
          sensors.map((id) => ({ name: id, selector: { text: {} } })),
          (value) => {
            const list = [...this._config.groups];
            const item = { ...list[index] };
            const cleaned = Object.fromEntries(Object.entries(value).map(([id, v]) => [id, String(v ?? "").trim()]).filter(([id, v]) => (item.sensors || []).includes(id) && v));
            if (Object.keys(cleaned).length) item.sensor_names = cleaned;
            else delete item.sensor_names;
            list[index] = item;
            this._emit({ ...this._config, groups: list });
          },
        );
        form.computeLabel = (s) => this._hass?.states[s.name]?.attributes.friendly_name || s.name;
        namesBox.append(title, form);
      };
      let shownSensors = [...(group.sensors || [])];
      fillNames(shownSensors, group.sensor_names || {});
      // Thermomètre de chaque split (remplace l'ancien capteur unique « temperature_entity »)
      const climates = infoById[group.group]?.climates || [];
      if (climates.length) {
        const legacy = group.temperature_entity && !String(group.temperature_entity).startsWith("climate.") ? group.temperature_entity : null;
        const initial = Object.fromEntries(climates.map((eid) => [eid, group.thermometers?.[eid] || (!group.thermometers && legacy) || ""]));
        const hint = document.createElement("p");
        hint.className = "hint";
        hint.textContent = this._t("e_thermo");
        const thermoForm = this._form(
          initial,
          climates.map((eid) => ({ name: eid, selector: { entity: { filter: [{ domain: "sensor", device_class: "temperature" }, { domain: "sensor" }] } } })),
          (value) => {
            const list = [...this._config.groups];
            const item = { ...list[index] };
            const chosen = Object.fromEntries(Object.entries(value).filter(([eid, v]) => climates.includes(eid) && v));
            if (Object.keys(chosen).length) item.thermometers = chosen;
            else delete item.thermometers;
            delete item.temperature_entity;
            list[index] = item;
            this._emit({ ...this._config, groups: list });
          },
        );
        thermoForm.computeLabel = (sch) => this._t("e_thermo_of").replace("{s}", this._hass?.states[sch.name]?.attributes.friendly_name || sch.name);
        const box = document.createElement("div");
        box.className = "names";
        box.append(hint, thermoForm);
        details.append(box);
      }
      const keysA = ["sensors"];
      const pick = (keys, keep) => Object.fromEntries(Object.entries(data).filter(([k]) => keys.includes(k) === keep));
      // Les deux formulaires se partagent la configuration du groupe : chacun n'écrit que ses champs.
      const save = (value, keys) => {
        const list = [...this._config.groups];
        const prev = Object.fromEntries(Object.entries(list[index] || {}).filter(([k]) => !keys.includes(k)));
        const item = { ...prev, group: group.group, ...value };
        const sensors = item.sensors || [];
        const names = Object.fromEntries(Object.entries(item.sensor_names || {}).filter(([id]) => sensors.includes(id)));
        if (Object.keys(names).length) item.sensor_names = names;
        else delete item.sensor_names;
        list[index] = item;
        this._emit({ ...this._config, groups: list });
        if (sensors.join("|") !== shownSensors.join("|")) {
          shownSensors = [...sensors];
          fillNames(sensors, names);
        }
      };
      details.append(this._form(
        pick(keysA, true),
        [
          { name: "sensors", label: "e_sensors", selector: { entity: { multiple: true } } },
        ],
        (value) => save(value, keysA),
      ));
      details.append(namesBox);
      const keysB = ["show_planning", "show_profiles", "manual", "compressor", "compressor_timeline", "show_daikin", "chart"];
      details.append(this._form(
        pick(keysB, true),
        [
          { name: "show_planning", label: "e_show_planning", selector: { boolean: {} } },
          { name: "show_profiles", label: "e_show_profiles", selector: { boolean: {} } },
          { name: "manual", label: "e_manual", selector: { select: { multiple: true, mode: "list", options: manualOptions } } },
          { name: "compressor", label: "e_compressor", selector: { select: { multiple: true, mode: "list", options: compressorOptions } } },
          { name: "compressor_timeline", label: "e_compressor_timeline", selector: { boolean: {} } },
          { name: "show_daikin", label: "e_daikin", selector: { boolean: {} } },
          { name: "chart", label: "e_chart", selector: { select: { multiple: true, mode: "list", options: chartOptions } } },
        ],
        (value) => save(value, keysB),
        {
          compressor: this._t(infoById[group.group]?.compressor ? "e_compressor_ok" : "e_compressor_missing"),
          compressor_timeline: infoById[group.group]?.compressor ? "" : this._t("e_compressor_missing"),
        },
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
  .names { display: flex; flex-direction: column; gap: 6px; margin: 12px 0 4px; }
  .names:empty { display: none; }
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
  customElements.define("split-scheduler-history", SplitSchedulerHistory);
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
