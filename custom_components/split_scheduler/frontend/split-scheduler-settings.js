/*
 * Carte « Réglages de la programmation des splits » pour Home Assistant.
 *
 * Fournie et chargée automatiquement par l'intégration split_scheduler.
 *
 *   type: custom:split-scheduler-settings-card
 *
 * Les administrateurs modifient la configuration (bouton « Enregistrer ») ; les autres
 * utilisateurs la consultent en lecture seule. Étape 1 : réglages généraux et
 * programmation hebdomadaire ; les autres onglets renvoient au menu Paramètres.
 */

const SETTINGS_VERSION = "1.20.0";
const STEP = 15; // minutes : pas des poignées
const DAY_MIN = 1440;
const SETTINGS_URL = "/config/integrations/integration/split_scheduler";

const TXT = {
  fr: {
    name: "Réglages de la programmation des splits",
    desc: "Réglages de l'intégration : programmation hebdomadaire visuelle, réglages généraux.",
    title: "Réglages de la programmation",
    tabs: { general: "Réglages généraux", heat_pumps: "Pompes à chaleur", groups: "Groupes", plannings: "Types de planning", profiles: "Profils", program: "Programmation" },
    days: ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
    days_short: ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"],
    loading: "Chargement…",
    not_loaded: "L'intégration « Programmation des splits » n'est pas chargée.",
    readonly: "Lecture seule : seuls les administrateurs peuvent modifier ces réglages.",
    dirty: "{n} modification(s) non enregistrée(s)",
    clean: "✓ Tout est enregistré",
    cancel: "Annuler",
    save: "Enregistrer",
    saving: "Enregistrement…",
    saved: "Enregistré : l'intégration se recharge.",
    leave: "Des modifications ne sont pas enregistrées.",
    planning: "Planning",
    group: "Groupe",
    changes: "{n} changement(s)",
    none: "Aucun changement",
    inherited: "hérité",
    inherited_long: "Début de journée : profil hérité de {d} {t}",
    no_profile: "Aucun profil (programme vide)",
    seg: "{d} · {a} – {b}",
    start: "Début",
    profile: "Profil",
    only_allowed: "Seuls les profils autorisés dans ce planning sont proposés.",
    split: "Couper la plage en deux",
    remove: "Supprimer ce changement",
    close: "Fermer",
    add_line: "+ Ligne",
    hint: "Glisser une poignée déplace l'heure du changement (par pas de 15 min). Un clic sur une plage ouvre son réglage ; double-clic : nouveau changement à cet endroit.",
    copy_day: "Copier {d} vers…",
    copy_week: "Copier la semaine vers d'autres groupes / plannings",
    copy_do: "Copier",
    copy_days_title: "Copier les changements de {d} vers :",
    copy_week_title: "Remplacer la semaine de ces groupes, dans ces plannings :",
    copy_refused: "Refusé : {p} n'est pas autorisé dans {pl}.",
    copied: "Copié.",
    time_taken: "Un changement existe déjà à {t}.",
    conflict_title: "Conflit avec la pompe à chaleur",
    conflict: "{d} {a}–{b} : {m} ici, {o} pour {s} ({g}, {p})",
    conflict_prio: "prioritaire sur {h}",
    conflict_free: "même pompe {h}, sans split prioritaire",
    side: { heat: "chauffage", cool: "froid" },
    outdoor: "Capteur de température extérieure",
    outdoor_help: "Vide : détection automatique (capteur « Outside » de Faikout). Sert à l'adaptation des consignes.",
    send_normal: "Envoyer le préréglage Normal à chaque commande",
    always_quiet: "Unité extérieure silencieuse à chaque commande",
    soon: "Cet onglet arrive dans une prochaine version. En attendant, ces réglages se font dans le menu Paramètres de l'intégration.",
    open_settings: "Ouvrir les paramètres de l'intégration",
    add: "+ Ajouter",
    up: "Monter",
    down: "Descendre",
    delete: "Supprimer",
    duplicate: "Dupliquer",
    name: "Nom",
    new_profile: "Nouveau profil",
    new_planning: "Nouveau planning",
    new_group: "Nouveau groupe",
    new_pump: "Nouvelle pompe à chaleur",
    copy_of: "{n} (copie)",
    keep: "Ne pas modifier",
    hvac: { off: "Arrêt", heat: "Chauffage", cool: "Climatisation", heat_cool: "Chaud / froid", auto: "Automatique", dry: "Déshumidification", fan_only: "Ventilation" },
    mode: "Mode",
    setpoint: "Consigne",
    fan_mode: "Ventilation",
    swing_mode: "Oscillation verticale",
    swing_horizontal_mode: "Oscillation horizontale",
    quiet_outdoor: "Unité extérieure silencieuse",
    quiet_on: "Activée",
    quiet_off: "Désactivée",
    outdoor_max_delta: "Écart maximal avec l'extérieur (°C)",
    outdoor_delta_help: "Chauffage : consigne ≤ extérieur + écart ; climatisation : consigne ≥ extérieur − écart. Vide : pas d'adaptation.",
    used_in: "Utilisé dans : {u}",
    unused: "Utilisé dans aucun programme.",
    in_use: "Profil utilisé dans un programme : retirez-le d'abord des programmes ({u}).",
    keep_one: "Il faut en garder au moins un.",
    allowed: "Profils autorisés",
    allowed_help: "Un clic coche ou décoche. 🔒 : utilisé dans un programme de ce planning, ne peut pas être décoché.",
    dup_planning: "Dupliquer (avec les programmes)",
    splits: "Splits",
    climates: "Splits (thermostats)",
    offsets: "Décalage des consignes",
    offset_heat: "Décalage chauffage",
    offset_cool: "Décalage froid",
    offsets_help: "Ajouté à la consigne envoyée au split pour corriger son thermostat (invisible sur la carte), de −3 à +3 °C.",
    pump_of_group: "Pompe à chaleur « {n} »",
    no_pump: "Aucune pompe à chaleur pour ces splits : créez-la dans l'onglet Pompes à chaleur.",
    pump_summary_help: "Les mêmes réglages que dans l'onglet Pompes à chaleur.",
    model: "Modèle",
    priority: "Split prioritaire",
    no_priority: "Aucun",
    compressors: "Capteurs du compresseur",
    compressors_help: "Vide : détection automatique ({d}). Plusieurs capteurs : leur médiane.",
    compressor_max: "Fréquence maximale du compresseur",
    compressor_max_help: "Unité du capteur (Hz ou tr/min). Vide : observée sur 30 jours.",
    power_sensor: "Capteur de puissance (W)",
    energy_sensor: "Compteur d'énergie (kWh)",
    pump_climates: "Splits reliés à cette unité extérieure",
    other_pump: "{s} appartient déjà à {h}.",
    empty_list: "Aucun élément.",
    stale_ref: "Après enregistrement, vérifiez la programmation des nouveaux groupes et plannings.",
  },
  en: {
    name: "Split scheduler settings",
    desc: "Integration settings: visual weekly programming, general settings.",
    title: "Scheduling settings",
    tabs: { general: "General settings", heat_pumps: "Heat pumps", groups: "Groups", plannings: "Planning types", profiles: "Profiles", program: "Programming" },
    days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    days_short: ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    loading: "Loading…",
    not_loaded: "The Split scheduler integration is not loaded.",
    readonly: "Read only: only administrators can change these settings.",
    dirty: "{n} unsaved change(s)",
    clean: "✓ Everything is saved",
    cancel: "Cancel",
    save: "Save",
    saving: "Saving…",
    saved: "Saved: the integration is reloading.",
    leave: "Some changes are not saved.",
    planning: "Planning",
    group: "Group",
    changes: "{n} change(s)",
    none: "No change",
    inherited: "inherited",
    inherited_long: "Start of day: profile inherited from {d} {t}",
    no_profile: "No profile (empty program)",
    seg: "{d} · {a} – {b}",
    start: "Start",
    profile: "Profile",
    only_allowed: "Only the profiles allowed in this planning are offered.",
    split: "Split the range in two",
    remove: "Delete this change",
    close: "Close",
    add_line: "+ Line",
    hint: "Drag a handle to move the change time (15 min steps). Click a range to set it; double-click: new change at that point.",
    copy_day: "Copy {d} to…",
    copy_week: "Copy the week to other groups / plannings",
    copy_do: "Copy",
    copy_days_title: "Copy the changes of {d} to:",
    copy_week_title: "Replace the week of these groups, in these plannings:",
    copy_refused: "Refused: {p} is not allowed in {pl}.",
    copied: "Copied.",
    time_taken: "A change already exists at {t}.",
    conflict_title: "Heat pump conflict",
    conflict: "{d} {a}–{b}: {m} here, {o} for {s} ({g}, {p})",
    conflict_prio: "priority on {h}",
    conflict_free: "same pump {h}, no priority split",
    side: { heat: "heating", cool: "cooling" },
    outdoor: "Outdoor temperature sensor",
    outdoor_help: "Empty: automatic detection (Faikout \"Outside\" sensor). Used to adapt setpoints.",
    send_normal: "Send the Normal preset with every command",
    always_quiet: "Quiet outdoor unit with every command",
    soon: "This tab comes in a later version. Meanwhile, these settings are in the integration's Settings menu.",
    open_settings: "Open the integration settings",
    add: "+ Add",
    up: "Move up",
    down: "Move down",
    delete: "Delete",
    duplicate: "Duplicate",
    name: "Name",
    new_profile: "New profile",
    new_planning: "New planning",
    new_group: "New group",
    new_pump: "New heat pump",
    copy_of: "{n} (copy)",
    keep: "Do not change",
    hvac: { off: "Off", heat: "Heat", cool: "Cool", heat_cool: "Heat/Cool", auto: "Auto", dry: "Dry", fan_only: "Fan only" },
    mode: "Mode",
    setpoint: "Setpoint",
    fan_mode: "Fan",
    swing_mode: "Vertical swing",
    swing_horizontal_mode: "Horizontal swing",
    quiet_outdoor: "Quiet outdoor unit",
    quiet_on: "On",
    quiet_off: "Off",
    outdoor_max_delta: "Maximum gap with outdoor (°C)",
    outdoor_delta_help: "Heating: setpoint ≤ outdoor + gap; cooling: setpoint ≥ outdoor − gap. Empty: no adaptation.",
    used_in: "Used in: {u}",
    unused: "Not used in any program.",
    in_use: "Profile used in a program: remove it from the programs first ({u}).",
    keep_one: "At least one must be kept.",
    allowed: "Allowed profiles",
    allowed_help: "Click to check or uncheck. 🔒: used in a program of this planning, cannot be unchecked.",
    dup_planning: "Duplicate (with the programs)",
    splits: "Splits",
    climates: "Splits (thermostats)",
    offsets: "Setpoint offsets",
    offset_heat: "Heating offset",
    offset_cool: "Cooling offset",
    offsets_help: "Added to the setpoint sent to the split to correct its thermostat (not shown on the card), −3 to +3 °C.",
    pump_of_group: "Heat pump \"{n}\"",
    no_pump: "No heat pump for these splits: create it in the Heat pumps tab.",
    pump_summary_help: "The same settings as in the Heat pumps tab.",
    model: "Model",
    priority: "Priority split",
    no_priority: "None",
    compressors: "Compressor sensors",
    compressors_help: "Empty: automatic detection ({d}). Several sensors: their median.",
    compressor_max: "Maximum compressor frequency",
    compressor_max_help: "Sensor unit (Hz or rpm). Empty: observed over 30 days.",
    power_sensor: "Power sensor (W)",
    energy_sensor: "Energy meter (kWh)",
    pump_climates: "Splits connected to this outdoor unit",
    other_pump: "{s} already belongs to {h}.",
    empty_list: "No item.",
    stale_ref: "After saving, check the programming of new groups and plannings.",
  },
};

const TABS = ["general", "heat_pumps", "groups", "plannings", "profiles", "program"];
const SIDES = { heat: "heat", cool: "cool", dry: "cool" };

function escS(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const toMin = (hhmm) => { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; };
const toHHMM = (min) => `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(min % 60).padStart(2, "0")}`;
const clone = (x) => JSON.parse(JSON.stringify(x));

/** Changements de la semaine en minutes depuis lundi 00:00. */
function weekChanges(program) {
  const out = [];
  for (const [day, slots] of Object.entries(program || {})) for (const [t, pid] of slots) out.push([Number(day) * DAY_MIN + toMin(t), pid]);
  return out.sort((a, b) => a[0] - b[0]);
}
function activeAt(changes, minute) {
  if (!changes.length) return null;
  let current = changes.at(-1)[1];
  for (const [t, pid] of changes) { if (t > minute) break; current = pid; }
  return current;
}
/** Plages où deux programmes demandent des côtés opposés (chaud / froid). */
function programConflicts(own, other, sideOf) {
  const a = weekChanges(own);
  const b = weekChanges(other);
  const points = [...new Set([0, ...a.map(([t]) => t), ...b.map(([t]) => t)])].sort((x, y) => x - y);
  const result = [];
  points.forEach((start, i) => {
    const end = i + 1 < points.length ? points[i + 1] : 7 * DAY_MIN;
    const mine = sideOf(activeAt(a, start));
    const theirs = sideOf(activeAt(b, start));
    if (mine && theirs && mine !== theirs) {
      const last = result.at(-1);
      if (last && last[1] === start && last[2] === mine && last[3] === theirs) last[1] = end;
      else result.push([start, end, mine, theirs]);
    }
  });
  return result;
}


const newId = () => Math.random().toString(16).slice(2, 10);
const normName = (n) => String(n || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().split(/\s+/).filter(Boolean).join(" ");
const KINDS = { profiles: "profiles", plannings: "plannings", groups: "groups", heat_pumps: "heat_pumps" };

class SplitSchedulerSettingsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "program";
    this._sel = null;      // plage sélectionnée {day, idx} (idx -1 : début de journée hérité)
    this._panel = null;    // "day" | "week" : panneau de copie ouvert
    this._day = 0;         // jour affiché sur téléphone
    this._msg = null;
    this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    this.shadowRoot.addEventListener("dblclick", (ev) => this._onDblClick(ev));
    this.shadowRoot.addEventListener("change", (ev) => this._onChange(ev));
    this.shadowRoot.addEventListener("pointerdown", (ev) => this._onPointerDown(ev));
    this._beforeUnload = (ev) => { if (this._dirtyCount()) { ev.preventDefault(); ev.returnValue = this._t("leave"); } };
  }

  static getStubConfig() { return {}; }
  setConfig(config) { this._config = config || {}; }
  getCardSize() { return 12; }
  getGridOptions() { return { columns: 12, min_columns: 6 }; }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) { this._load(); }
    if (this._genForm) this._genForm.hass = hass;
  }

  connectedCallback() {
    window.addEventListener("beforeunload", this._beforeUnload);
    this._resize = new ResizeObserver(() => {
      const narrow = this.clientWidth < 640;
      if (narrow !== this._narrow) { this._narrow = narrow; this._render(); }
    });
    this._resize.observe(this);
  }

  disconnectedCallback() {
    window.removeEventListener("beforeunload", this._beforeUnload);
    this._resize?.disconnect();
  }

  _t(key) {
    const l = (this._hass?.locale?.language || this._hass?.language || "fr").startsWith("fr") ? "fr" : "en";
    return TXT[l][key] ?? TXT.fr[key] ?? key;
  }

  _tf(key, vars) {
    return Object.entries(vars).reduce((s, [k, v]) => s.replaceAll(`{${k}}`, v), this._t(key));
  }

  async _load() {
    try {
      const cfg = await this._hass.callWS({ type: "split_scheduler/config/get" });
      this._server = cfg;
      this._cfg = cfg;
      this._error = null;
      this._reset();
      this._planning ??= cfg.plannings[0]?.id;
      this._group ??= cfg.groups[0]?.id;
      if (!cfg.plannings.some((p) => p.id === this._planning)) this._planning = cfg.plannings[0]?.id;
      if (!cfg.groups.some((g) => g.id === this._group)) this._group = cfg.groups[0]?.id;
    } catch (err) {
      this._error = err?.code === "not_loaded" ? this._t("not_loaded") : err?.message || String(err);
    }
    this._render();
  }

  /** Copie de travail : programmes et réglages généraux. */
  _reset() {
    // _orig : configuration enregistrée ; _cfg : copie de travail (profils, groupes…)
    this._orig = clone(this._server);
    this._cfg = clone(this._server);
    this._programs = Object.fromEntries(this._cfg.plannings.map((p) => [p.id, clone(p.programs || {})]));
    this._settings = clone(this._cfg.settings);
    this._item = {};
    this._sel = null;
    this._panel = null;
    this._genForm = null;
  }

  get _admin() { return this._cfg?.admin === true; }

  _dirtyCount() {
    if (!this._cfg) return 0;
    return Object.keys(this._programChanges()).length + Object.keys(this._collectionChanges()).length
      + (JSON.stringify(this._orig.settings) !== JSON.stringify(this._settings) ? 1 : 0);
  }

  /** Programmes modifiés : {planning: {groupe: programme}} (une entrée par couple). */
  _programChanges() {
    const out = {};
    for (const pl of this._cfg.plannings) {
      const before = this._orig.plannings.find((p) => p.id === pl.id)?.programs || {};
      const ids = new Set([...Object.keys(before), ...Object.keys(this._programs[pl.id] || {})]);
      for (const gid of ids) {
        if (!this._cfg.groups.some((g) => g.id === gid)) continue;
        const now = this._norm(this._programs[pl.id]?.[gid]);
        if (JSON.stringify(this._norm(before[gid])) !== JSON.stringify(now)) out[`${pl.id}|${gid}`] = [pl.id, gid, now];
      }
    }
    return out;
  }

  /** Collections modifiées (profils, plannings, groupes, pompes, décalages) : valeurs à envoyer. */
  _collectionChanges() {
    const strip = {
      profiles: (p) => { const { color, summary, ...rest } = p; return rest; },
      plannings: (p) => ({ id: p.id, name: p.name, allowed: p.allowed, ...(p.copy_from ? { copy_from: p.copy_from } : {}) }),
      groups: (g) => ({ id: g.id, name: g.name, climates: g.climates }),
      heat_pumps: (h) => { const { priority_name, ...rest } = h; return rest; },
    };
    const out = {};
    for (const [key, fn] of Object.entries(strip)) {
      const now = this._cfg[key].map(fn);
      if (JSON.stringify(now) !== JSON.stringify(this._orig[key].map(fn))) out[key] = now;
    }
    if (JSON.stringify(this._cfg.offsets || {}) !== JSON.stringify(this._orig.offsets || {})) out.offsets = this._cfg.offsets || {};
    return out;
  }

  _norm(program) {
    return Object.fromEntries(Object.entries(program || {}).filter(([, s]) => s && s.length).sort());
  }

  _profile(pid) { return this._cfg.profiles.find((p) => p.id === pid); }
  _planningCfg() { return this._cfg.plannings.find((p) => p.id === this._planning); }
  _groupCfg(gid = this._group) { return this._cfg.groups.find((g) => g.id === gid); }
  _program() {
    const progs = (this._programs[this._planning] ??= {});
    return (progs[this._group] ??= {});
  }
  _slots(day) { return this._program()[String(day)] || []; }
  _setSlots(day, slots) {
    const sorted = [...slots].sort((a, b) => toMin(a[0]) - toMin(b[0]));
    if (sorted.length) this._program()[String(day)] = sorted;
    else delete this._program()[String(day)];
  }

  /** Profil hérité au début du jour : dernier changement des jours précédents. */
  _inherited(day) {
    for (let back = 1; back <= 7; back++) {
      const d = (day - back + 7) % 7;
      const slots = this._slots(d);
      if (slots.length) return { day: d, time: slots.at(-1)[0], pid: slots.at(-1)[1] };
    }
    return null;
  }

  /** Plages d'un jour : [{start, end, pid, idx, inherited}]. */
  _segments(day) {
    const slots = this._slots(day);
    const segs = [];
    const inh = this._inherited(day);
    const first = slots.length ? toMin(slots[0][0]) : DAY_MIN;
    if (first > 0) segs.push({ start: 0, end: first, pid: inh?.pid ?? null, idx: -1, inherited: true });
    slots.forEach(([t, pid], i) => {
      const end = i + 1 < slots.length ? toMin(slots[i + 1][0]) : DAY_MIN;
      segs.push({ start: toMin(t), end, pid, idx: i, inherited: false });
    });
    return segs;
  }

  // ------------------------------------------------------------------ rendu

  _render() {
    if (!this._hass) return;
    const scrollY = this.shadowRoot.querySelector(".body")?.scrollTop;
    this._formSpecs = {};
    let html;
    if (this._error) html = `<ha-card><div class="msg err">${escS(this._error)}</div></ha-card>`;
    else if (!this._cfg) html = `<ha-card><div class="msg">${escS(this._t("loading"))}</div></ha-card>`;
    else html = `<ha-card class="${this._narrow ? "narrow" : ""}">${this._renderHeader()}${this._renderTabs()}<div class="body">${this._renderBody()}</div></ha-card>`;
    this.shadowRoot.innerHTML = `<style>${SETTINGS_CSS}</style>${html}`;
    if (scrollY) this.shadowRoot.querySelector(".body")?.scrollTo(0, scrollY);
    if (this._cfg && this._tab === "general") this._mountGeneral();
    if (this._cfg) this._mountForms();
  }

  _renderHeader() {
    let right;
    if (!this._admin) right = `<span class="ro">🔒 ${escS(this._t("readonly"))}</span>`;
    else {
      const n = this._dirtyCount();
      const msg = this._msg ? `<span class="note ${this._msg.err ? "err" : "ok"}">${escS(this._msg.text)}</span>` : "";
      right = n
        ? `${msg}<span class="dirty"><i></i>${escS(this._tf("dirty", { n }))}</span>
           <button type="button" class="outlined" data-act="cancel">${escS(this._t("cancel"))}</button>
           <button type="button" class="filled" data-act="save" ${this._saving ? "disabled" : ""}>${escS(this._t(this._saving ? "saving" : "save"))}</button>`
        : `${msg || `<span class="note ok">${escS(this._t("clean"))}</span>`}`;
    }
    return `<header><h1>${escS(this._config?.title || this._t("title"))}</h1><div class="actions">${right}</div></header>`;
  }

  _renderTabs() {
    const tabs = TXT.fr.tabs;
    return `<nav role="tablist">${TABS.map((k) => `<button type="button" role="tab" aria-selected="${k === this._tab}" class="${k === this._tab ? "on" : ""}" data-act="tab" data-value="${k}">${escS(this._t("tabs")[k] || tabs[k])}</button>`).join("")}</nav>`;
  }

  _renderBody() {
    if (this._tab === "program") return this._renderProgram();
    if (this._tab === "general") return `<div class="general"></div>`;
    if (this._tab === "profiles") return this._renderProfiles();
    if (this._tab === "plannings") return this._renderPlannings();
    if (this._tab === "groups") return this._renderGroups();
    if (this._tab === "heat_pumps") return this._renderPumps();
    return `<div class="soon"><p>${escS(this._t("soon"))}</p><button type="button" class="outlined" data-act="open-settings">${escS(this._t("open_settings"))}</button></div>`;
  }

  _mountGeneral() {
    const host = this.shadowRoot.querySelector(".general");
    if (!host) return;
    if (!this._genForm) {
      const form = document.createElement("ha-form");
      form.schema = [
        { name: "outdoor_sensor", selector: { entity: { domain: "sensor" } } },
        { name: "send_normal_preset", selector: { boolean: {} } },
        { name: "always_quiet", selector: { boolean: {} } },
      ];
      form.computeLabel = (s) => this._t({ outdoor_sensor: "outdoor", send_normal_preset: "send_normal", always_quiet: "always_quiet" }[s.name]);
      form.computeHelper = (s) => (s.name === "outdoor_sensor" ? this._t("outdoor_help") : "");
      form.addEventListener("value-changed", (ev) => {
        const v = ev.detail.value;
        this._settings = { outdoor_sensor: v.outdoor_sensor || null, send_normal_preset: !!v.send_normal_preset, always_quiet: !!v.always_quiet };
        form.data = v;
        this._refreshHeader();
      });
      this._genForm = form;
    }
    this._genForm.hass = this._hass;
    this._genForm.data = { ...this._settings, outdoor_sensor: this._settings.outdoor_sensor || "" };
    this._genForm.disabled = !this._admin;
    host.append(this._genForm);
  }

  /** Met à jour l'en-tête sans redessiner l'onglet (saisie en cours). */
  _refreshHeader() {
    const header = this.shadowRoot.querySelector("header");
    if (header) header.outerHTML = this._renderHeader();
  }

  _chips(items, current, act) {
    return `<div class="chips">${items.map((x) => `<button type="button" class="chip ${x.id === current ? "on" : ""}" data-act="${act}" data-value="${escS(x.id)}">${escS(x.name)}</button>`).join("")}</div>`;
  }

  _renderProgram() {
    if (!this._cfg.groups.length || !this._cfg.plannings.length) return `<div class="soon"><p>${escS(this._t("soon"))}</p></div>`;
    const pickers = `<div class="pickers"><span class="lab">${escS(this._t("planning"))}</span>${this._chips(this._cfg.plannings, this._planning, "planning")}
      <span class="lab">${escS(this._t("group"))}</span>${this._chips(this._cfg.groups, this._group, "group")}</div>`;
    const week = this._narrow ? this._renderDayMobile() : this._renderWeek();
    const editor = this._sel ? this._renderEditor() : "";
    const copy = this._admin ? this._renderCopy() : "";
    const legend = `<div class="legend">${this._allowed().map((pid) => { const p = this._profile(pid); return `<span><i style="background:${p.color}"></i>${escS(p.name)}</span>`; }).join("")}</div>`;
    return `${pickers}${this._renderConflicts()}${week}${editor}${legend}${copy}${this._admin && !this._narrow ? `<p class="hint">${escS(this._t("hint"))}</p>` : ""}`;
  }

  _allowed() { return this._planningCfg()?.allowed || []; }

  _bar(day, { handles = true, height = 34 } = {}) {
    const segs = this._segments(day);
    const blocks = segs.map((s) => {
      const p = s.pid ? this._profile(s.pid) : null;
      const sel = this._sel && this._sel.day === day && this._sel.idx === s.idx;
      const wide = s.end - s.start >= 120;
      return `<button type="button" class="seg ${s.inherited ? "inh" : ""} ${sel ? "sel" : ""}" style="left:${(s.start / DAY_MIN) * 100}%;width:${((s.end - s.start) / DAY_MIN) * 100}%;background:${p?.color || "var(--disabled-color, #bdbdbd)"}"
        data-act="seg" data-day="${day}" data-idx="${s.idx}" title="${escS(`${toHHMM(s.start)}–${toHHMM(s.end)} ${p?.name || ""}`)}">${wide && p ? escS(p.name) : ""}</button>`;
    }).join("");
    const grips = handles && this._admin
      ? this._slots(day).map(([t], i) => (toMin(t) === 0 ? "" : `<span class="grip" style="left:${(toMin(t) / DAY_MIN) * 100}%" data-day="${day}" data-idx="${i}" role="slider" aria-label="${escS(t)}" aria-valuenow="${toMin(t)}"></span>`)).join("")
      : "";
    return `<div class="bar" style="height:${height}px" data-bar="${day}">${blocks}${grips}</div>`;
  }

  _renderWeek() {
    const rows = [0, 1, 2, 3, 4, 5, 6].map((d) => {
      const n = this._slots(d).length;
      return `<div class="day"><span class="dname ${this._sel?.day === d ? "on" : ""}">${escS(this._t("days")[d])}</span>${this._bar(d)}<span class="dcount">${escS(n ? this._tf("changes", { n }) : this._t("none"))}</span></div>`;
    }).join("");
    const axis = `<div class="day axis"><span></span><div class="ticks"><span>0 h</span><span>6 h</span><span>12 h</span><span>18 h</span><span>24 h</span></div><span></span></div>`;
    return `<div class="week">${rows}${axis}</div>`;
  }

  _renderDayMobile() {
    const d = this._day;
    const pills = `<div class="pills">${this._t("days_short").map((x, i) => `<button type="button" class="pill ${i === d ? "on" : ""}" data-act="mday" data-value="${i}">${escS(x)}</button>`).join("")}</div>`;
    const lines = this._segments(d).map((s) => {
      const p = s.pid ? this._profile(s.pid) : null;
      const sel = this._sel && this._sel.day === d && this._sel.idx === s.idx;
      return `<button type="button" class="line ${sel ? "on" : ""} ${s.inherited ? "inh" : ""}" data-act="seg" data-day="${d}" data-idx="${s.idx}">
        <span class="time">${toHHMM(s.start)}</span><i style="background:${p?.color || "var(--disabled-color)"}"></i><span class="pname">${escS(p?.name || this._t("no_profile"))}</span>${s.inherited ? `<span class="small">${escS(this._t("inherited"))}</span>` : ""}<span class="chev">›</span></button>`;
    }).join("");
    const add = this._admin ? `<div class="row"><button type="button" class="filled" data-act="add-line">${escS(this._t("add_line"))}</button></div>` : "";
    return `${pills}${this._bar(d, { handles: false, height: 26 })}<div class="lines">${lines}</div>${add}`;
  }

  _renderEditor() {
    const { day, idx } = this._sel;
    const seg = this._segments(day).find((s) => s.idx === idx);
    if (!seg) return "";
    const title = this._tf("seg", { d: this._t("days")[day], a: toHHMM(seg.start), b: toHHMM(seg.end) });
    const inh = seg.inherited ? this._inherited(day) : null;
    const note = seg.inherited && inh ? `<p class="small">${escS(this._tf("inherited_long", { d: this._t("days")[inh.day].toLowerCase(), t: inh.time }))}</p>` : "";
    const ro = !this._admin;
    const time = seg.inherited ? "" : `<label class="field"><span>${escS(this._t("start"))}</span><input type="time" step="900" value="${toHHMM(seg.start)}" data-act="time" ${ro ? "disabled" : ""}></label>`;
    const chips = this._allowed().map((pid) => {
      const p = this._profile(pid);
      return `<button type="button" class="pchip ${pid === seg.pid ? "on" : ""}" style="--c:${p.color}" data-act="profile" data-value="${escS(pid)}" ${ro ? "disabled" : ""} title="${escS(p.summary || "")}"><i></i>${escS(p.name)}</button>`;
    }).join("");
    const actions = ro ? "" : `<div class="row">
      ${seg.end - seg.start >= 2 * STEP ? `<button type="button" class="outlined" data-act="split">${escS(this._t("split"))}</button>` : ""}
      ${seg.inherited ? "" : `<button type="button" class="outlined" data-act="remove">${escS(this._t("remove"))}</button>`}
      <button type="button" class="text" data-act="close">${escS(this._t("close"))}</button></div>`;
    return `<section class="editor"><h2>${escS(title)}</h2>${note}${time}<span class="lab">${escS(this._t("profile"))}</span><div class="pchips">${chips}</div><p class="small">${escS(this._t("only_allowed"))}</p>${actions}</section>`;
  }

  _renderCopy() {
    const dayName = this._t("days")[this._sel?.day ?? this._day];
    let panel = "";
    if (this._panel === "day") {
      const src = this._sel?.day ?? this._day;
      panel = `<section class="editor"><h2>${escS(this._tf("copy_days_title", { d: dayName.toLowerCase() }))}</h2><div class="checks">${this._t("days").map((n, i) => (i === src ? "" : `<label><input type="checkbox" data-copy-day="${i}"> ${escS(n)}</label>`)).join("")}</div>
        <div class="row"><button type="button" class="filled" data-act="copy-day-do">${escS(this._t("copy_do"))}</button><button type="button" class="text" data-act="copy-close">${escS(this._t("close"))}</button></div></section>`;
    } else if (this._panel === "week") {
      panel = `<section class="editor"><h2>${escS(this._t("copy_week_title"))}</h2>
        <span class="lab">${escS(this._t("planning"))}</span><div class="checks">${this._cfg.plannings.map((p) => `<label><input type="checkbox" data-copy-pl="${escS(p.id)}" ${p.id === this._planning ? "checked" : ""}> ${escS(p.name)}</label>`).join("")}</div>
        <span class="lab">${escS(this._t("group"))}</span><div class="checks">${this._cfg.groups.filter((g) => g.id !== this._group).map((g) => `<label><input type="checkbox" data-copy-g="${escS(g.id)}"> ${escS(g.name)}</label>`).join("")}</div>
        <div class="row"><button type="button" class="filled" data-act="copy-week-do">${escS(this._t("copy_do"))}</button><button type="button" class="text" data-act="copy-close">${escS(this._t("close"))}</button></div></section>`;
    }
    return `<div class="row wrap"><button type="button" class="outlined" data-act="copy-day">${escS(this._tf("copy_day", { d: dayName.toLowerCase() }))}</button><button type="button" class="outlined" data-act="copy-week">${escS(this._t("copy_week"))}</button></div>${panel}`;
  }

  /** Avertissements pompe à chaleur pour le programme édité (même règle que le menu). */
  _renderConflicts() {
    const group = this._groupCfg();
    const own = new Set(group?.climates || []);
    const progs = this._programs[this._planning] || {};
    const sideOf = (pid) => SIDES[this._profile(pid)?.hvac_mode] || null;
    const lines = [];
    for (const hp of this._cfg.heat_pumps || []) {
      const members = new Set(hp.climates);
      if (![...own].some((e) => members.has(e))) continue;
      const refs = hp.priority ? [hp.priority] : [...members].filter((e) => !own.has(e));
      for (const g of this._cfg.groups) {
        const split = refs.find((e) => g.climates.includes(e));
        if (g.id === this._group || !split || own.has(split)) continue;
        for (const [a, b, m, o] of programConflicts(progs[this._group], progs[g.id], sideOf).slice(0, 4)) {
          lines.push(this._tf("conflict", {
            d: this._t("days")[Math.floor(a / DAY_MIN)].slice(0, 3), a: toHHMM(a % DAY_MIN), b: b % DAY_MIN === 0 ? "24:00" : toHHMM(b % DAY_MIN),
            m: this._t("side")[m], o: this._t("side")[o], s: g.names?.[split] || this._name(split), g: g.name,
            p: hp.priority ? this._tf("conflict_prio", { h: hp.name }) : this._tf("conflict_free", { h: hp.name }),
          }));
        }
      }
    }
    if (!lines.length) return "";
    return `<div class="warn" role="alert">⚠️ <div><strong>${escS(this._t("conflict_title"))}</strong>${lines.slice(0, 8).map((l) => `<div>${escS(l)}</div>`).join("")}</div></div>`;
  }


  // ------------------------------------------------------------------ listes (profils, plannings, groupes, pompes)

  _colorOf(name) {
    const key = normName(name);
    const c = this._cfg.colors;
    for (const [prefix, color] of c?.prefixes || []) if (key.startsWith(prefix)) return color;
    const extra = c?.extra || ["#8e24aa"];
    return extra[[...key].reduce((a, ch) => a + ch.charCodeAt(0), 0) % extra.length];
  }

  _selected(kind) {
    const list = this._cfg[kind];
    if (!list.some((x) => x.id === this._item[kind])) this._item[kind] = list[0]?.id;
    return list.find((x) => x.id === this._item[kind]);
  }

  _listPane(kind, subOf, dotOf) {
    const list = this._cfg[kind];
    const cur = this._selected(kind)?.id;
    const rows = list.map((x) => `<button type="button" class="li ${x.id === cur ? "on" : ""}" data-act="item" data-kind="${kind}" data-value="${escS(x.id)}">
      ${dotOf ? `<i style="background:${dotOf(x)}"></i>` : ""}<span class="col"><strong>${escS(x.name)}</strong><span class="small">${escS(subOf(x))}</span></span></button>`).join("");
    const head = `<div class="lhead"><span>${escS(this._t("tabs")[kind])}</span>${this._admin ? `<button type="button" class="filled sm" data-act="add" data-kind="${kind}">${escS(this._t("add"))}</button>` : ""}</div>`;
    const order = this._admin && cur ? `<div class="row"><button type="button" class="text" data-act="move" data-kind="${kind}" data-value="-1">↑ ${escS(this._t("up"))}</button><button type="button" class="text" data-act="move" data-kind="${kind}" data-value="1">↓ ${escS(this._t("down"))}</button></div>` : "";
    return `<aside class="list">${head}${rows || `<p class="small">${escS(this._t("empty_list"))}</p>`}${order}</aside>`;
  }

  _textField(kind, field, label, value, extra = "") {
    return `<label class="field wide"><span>${escS(label)}</span><input type="text" value="${escS(value ?? "")}" data-field="${field}" data-kind="${kind}" ${this._admin ? "" : "disabled"} ${extra}></label>`;
  }

  _numField(kind, field, label, value, { min, max, step = 0.5, help = "" } = {}) {
    return `<label class="field"><span>${escS(label)}</span><input type="number" inputmode="decimal" min="${min}" max="${max}" step="${step}" value="${value ?? ""}" data-field="${field}" data-kind="${kind}" data-num="1" ${this._admin ? "" : "disabled"}>${help ? `<em>${escS(help)}</em>` : ""}</label>`;
  }

  _selectField(kind, field, label, value, options, keepLabel) {
    const opts = [`<option value="">${escS(keepLabel ?? this._t("keep"))}</option>`, ...options.map(([v, l]) => `<option value="${escS(v)}" ${String(value) === String(v) ? "selected" : ""}>${escS(l)}</option>`)];
    if (value && !options.some(([v]) => String(v) === String(value))) opts.push(`<option value="${escS(value)}" selected>${escS(value)}</option>`);
    return `<label class="field"><span>${escS(label)}</span><select data-field="${field}" data-kind="${kind}" ${this._admin ? "" : "disabled"}>${opts.join("")}</select></label>`;
  }

  /** Formulaire Home Assistant (sélecteurs d'entités) monté après le rendu. */
  _form(key, schema, data, onChange, labels = {}, helpers = {}) {
    (this._formSpecs ??= {})[key] = { schema, data, onChange, labels, helpers };
    return `<div class="haform" data-form="${escS(key)}"></div>`;
  }

  _mountForms() {
    for (const host of this.shadowRoot.querySelectorAll("[data-form]")) {
      const spec = this._formSpecs?.[host.dataset.form];
      if (!spec) continue;
      const form = document.createElement("ha-form");
      form.hass = this._hass;
      form.schema = spec.schema;
      form.data = spec.data;
      form.disabled = !this._admin;
      form.computeLabel = (sch) => spec.labels[sch.name] || sch.name;
      form.computeHelper = (sch) => spec.helpers[sch.name] || "";
      form.addEventListener("value-changed", (ev) => { spec.onChange(ev.detail.value); this._changed(); });
      host.append(form);
    }
  }

  _usage(pid) {
    const out = [];
    for (const pl of this._cfg.plannings) {
      const groups = this._cfg.groups.filter((g) => Object.values(this._programs[pl.id]?.[g.id] || {}).some((slots) => slots.some(([, p]) => p === pid)));
      if (groups.length) out.push(`${pl.name} (${groups.map((g) => g.name).join(", ")})`);
    }
    return out;
  }

  _renderProfiles() {
    const hv = this._t("hvac");
    const list = this._listPane("profiles", (p) => p.summary || "", (p) => p.color);
    const p = this._selected("profiles");
    if (!p) return `<div class="split">${list}</div>`;
    const ro = !this._admin;
    const modes = [["", this._t("keep")], ...this._cfg.modes.hvac_mode.map((m) => [m, hv[m] || m])]
      .map(([m, l]) => `<button type="button" class="mode ${String(p.hvac_mode ?? "") === m ? "on" : ""}" data-act="pmode" data-value="${m}" ${ro ? "disabled" : ""}>${escS(l)}</button>`).join("");
    const temp = p.temperature;
    const stepper = `<div class="stepper"><button type="button" class="round" data-act="tstep" data-value="-0.5" ${ro ? "disabled" : ""}>−</button>
      <span class="tval">${temp == null || temp === "" ? escS(this._t("keep")) : `${String(Number(temp).toFixed(1)).replace(".", ",")} <small>°C</small>`}</span>
      <button type="button" class="round" data-act="tstep" data-value="0.5" ${ro ? "disabled" : ""}>+</button>
      ${temp == null || temp === "" || ro ? "" : `<button type="button" class="text" data-act="tclear">${escS(this._t("keep"))}</button>`}</div>`;
    const lists = ["fan_mode", "swing_mode", "swing_horizontal_mode"].map((f) => this._selectField("profiles", f, this._t(f), p[f], (this._cfg.modes[f] || []).map((v) => [v, v]))).join("");
    const quiet = this._cfg.quiet_available || typeof p.quiet_outdoor === "boolean"
      ? this._selectField("profiles", "quiet_outdoor", this._t("quiet_outdoor"), p.quiet_outdoor === true ? "on" : p.quiet_outdoor === false ? "off" : "", [["on", this._t("quiet_on")], ["off", this._t("quiet_off")]])
      : "";
    const used = this._usage(p.id);
    const actions = ro ? "" : `<div class="row"><button type="button" class="outlined" data-act="dup" data-kind="profiles">${escS(this._t("duplicate"))}</button><button type="button" class="outlined danger" data-act="del" data-kind="profiles">${escS(this._t("delete"))}</button></div>`;
    const detail = `<section class="detail">
      <div class="dhead"><i style="background:${p.color}"></i><h2>${escS(p.name)}</h2></div>
      ${this._textField("profiles", "name", this._t("name"), p.name)}
      <span class="lab">${escS(this._t("mode"))}</span><div class="modes">${modes}</div>
      <span class="lab">${escS(this._t("setpoint"))}</span>${stepper}
      <div class="grid2">${lists}${quiet}</div>
      ${this._numField("profiles", "outdoor_max_delta", this._t("outdoor_max_delta"), p.outdoor_max_delta, { min: 1, max: 30, help: this._t("outdoor_delta_help") })}
      <p class="small">${escS(used.length ? this._tf("used_in", { u: used.join(" · ") }) : this._t("unused"))}</p>
      ${actions}</section>`;
    return `<div class="split">${list}${detail}</div>`;
  }

  _renderPlannings() {
    const list = this._listPane("plannings", (pl) => `${pl.allowed.length} / ${this._cfg.profiles.length} · ${Object.keys(this._programs[pl.id] || {}).filter((g) => Object.keys(this._norm(this._programs[pl.id][g])).length).length} programme(s)`);
    const pl = this._selected("plannings");
    if (!pl) return `<div class="split">${list}</div>`;
    const used = new Set(Object.values(this._programs[pl.id] || {}).flatMap((prog) => Object.values(prog).flatMap((sl) => sl.map(([, p]) => p))));
    const chips = this._cfg.profiles.map((p) => {
      const on = pl.allowed.includes(p.id);
      const lock = on && used.has(p.id);
      return `<button type="button" class="pchip ${on ? "on" : ""}" style="--c:${p.color}" data-act="allow" data-value="${escS(p.id)}" ${!this._admin || lock ? "disabled" : ""}><i></i>${escS(p.name)}${lock ? " 🔒" : ""}</button>`;
    }).join("");
    const actions = this._admin ? `<div class="row"><button type="button" class="outlined" data-act="dup" data-kind="plannings">${escS(this._t("dup_planning"))}</button><button type="button" class="outlined danger" data-act="del" data-kind="plannings">${escS(this._t("delete"))}</button></div>` : "";
    return `<div class="split">${list}<section class="detail"><h2>${escS(pl.name)}</h2>
      ${this._textField("plannings", "name", this._t("name"), pl.name)}
      <span class="lab">${escS(this._t("allowed"))}</span><div class="pchips">${chips}</div><p class="small">${escS(this._t("allowed_help"))}</p>${actions}</section></div>`;
  }

  _pumpOf(eid) { return this._cfg.heat_pumps.find((h) => h.climates.includes(eid)); }
  _name(eid) { return this._cfg.names?.[eid] || this._hass.states[eid]?.attributes?.friendly_name || eid; }

  _pumpFields(hp, keyPrefix) {
    const detected = hp.climates.map((e) => this._cfg.detected_compressors?.[e]).filter(Boolean);
    const prio = this._selectField("heat_pumps", "priority", this._t("priority"), hp.priority || "", hp.climates.map((e) => [e, this._name(e)]), this._t("no_priority"))
      .replace('data-kind="heat_pumps"', `data-kind="heat_pumps" data-id="${escS(hp.id)}"`);
    const model = this._textField("heat_pumps", "model", this._t("model"), hp.model || "", `data-id="${escS(hp.id)}"`);
    const max = this._numField("heat_pumps", "compressor_max", this._t("compressor_max"), hp.compressor_max, { min: 1, max: 15000, step: 1, help: this._t("compressor_max_help") })
      .replace('data-kind="heat_pumps"', `data-kind="heat_pumps" data-id="${escS(hp.id)}"`);
    const form = this._form(`${keyPrefix}-sensors`, [
      { name: "compressors", selector: { entity: { domain: "sensor", multiple: true } } },
      { name: "power_sensor", selector: { entity: { domain: "sensor" } } },
      { name: "energy_sensor", selector: { entity: { domain: "sensor" } } },
    ], { compressors: hp.compressors || [], power_sensor: hp.power_sensor || "", energy_sensor: hp.energy_sensor || "" },
    (v) => {
      for (const k of ["compressors", "power_sensor", "energy_sensor"]) {
        const val = v[k];
        if (val && (!Array.isArray(val) || val.length)) hp[k] = val; else delete hp[k];
      }
    },
    { compressors: this._t("compressors"), power_sensor: this._t("power_sensor"), energy_sensor: this._t("energy_sensor") },
    { compressors: this._tf("compressors_help", { d: detected.join(", ") || "—" }) });
    return `<div class="grid2">${model}${prio}</div>${max}${form}`;
  }

  _renderGroups() {
    const list = this._listPane("groups", (g) => {
      const pumps = [...new Set(g.climates.map((e) => this._pumpOf(e)?.name).filter(Boolean))];
      return `${g.climates.length} split(s)${pumps.length ? ` · ${pumps.join(", ")}` : ""}`;
    });
    const g = this._selected("groups");
    if (!g) return `<div class="split">${list}</div>`;
    const ro = !this._admin;
    const climates = this._form(`g-${g.id}`, [{ name: "climates", selector: { entity: { domain: "climate", multiple: true } } }],
      { climates: g.climates }, (v) => { g.climates = v.climates || []; }, { climates: this._t("climates") });
    const offs = this._cfg.offsets || {};
    const rows = g.climates.map((eid) => {
      const hp = this._pumpOf(eid);
      const sub = hp ? `${hp.name}${hp.priority === eid ? " · ★" : ""}` : "";
      const inp = (side) => `<label class="field"><span>${escS(this._t(side === "heat" ? "offset_heat" : "offset_cool"))}</span><input type="number" step="0.5" min="-3" max="3" value="${offs[eid]?.[side] ?? 0}" data-offset="${escS(eid)}|${side}" ${ro ? "disabled" : ""}></label>`;
      return `<div class="srow"><span class="col"><strong>${escS(this._name(eid))}</strong><span class="small">${escS(sub)}</span></span>${inp("heat")}${inp("cool")}</div>`;
    }).join("");
    const pumps = [...new Set(g.climates.map((e) => this._pumpOf(e)).filter(Boolean))];
    const pumpBlocks = pumps.length
      ? pumps.map((hp) => `<div class="sub"><h3>${escS(this._tf("pump_of_group", { n: hp.name }))}</h3><p class="small">${escS(this._t("pump_summary_help"))}</p>${this._pumpFields(hp, `gp-${g.id}-${hp.id}`)}</div>`).join("")
      : `<p class="small">${escS(this._t("no_pump"))}</p>`;
    const actions = ro ? "" : `<div class="row"><button type="button" class="outlined danger" data-act="del" data-kind="groups">${escS(this._t("delete"))}</button></div>`;
    return `<div class="split">${list}<section class="detail"><h2>${escS(g.name)}</h2>
      ${this._textField("groups", "name", this._t("name"), g.name)}${climates}
      <h3>${escS(this._t("offsets"))}</h3>${rows}<p class="small">${escS(this._t("offsets_help"))}</p>
      ${pumpBlocks}${actions}</section></div>`;
  }

  _renderPumps() {
    const list = this._listPane("heat_pumps", (h) => `${h.climates.length} split(s)${h.model ? ` · ${h.model}` : ""}`);
    const hp = this._selected("heat_pumps");
    if (!hp) return `<div class="split">${list}</div>`;
    const climates = this._form(`hp-${hp.id}`, [{ name: "climates", selector: { entity: { domain: "climate", multiple: true } } }],
      { climates: hp.climates }, (v) => {
        const wanted = v.climates || [];
        const clash = wanted.map((e) => [e, this._cfg.heat_pumps.find((o) => o.id !== hp.id && o.climates.includes(e))]).find(([, o]) => o);
        if (clash) { this._msg = { err: true, text: this._tf("other_pump", { s: this._name(clash[0]), h: clash[1].name }) }; return; }
        hp.climates = wanted;
        if (hp.priority && !wanted.includes(hp.priority)) delete hp.priority;
      }, { climates: this._t("pump_climates") });
    const actions = this._admin ? `<div class="row"><button type="button" class="outlined danger" data-act="del" data-kind="heat_pumps">${escS(this._t("delete"))}</button></div>` : "";
    return `<div class="split">${list}<section class="detail"><h2>${escS(hp.name)}</h2>
      ${this._textField("heat_pumps", "name", this._t("name"), hp.name, `data-id="${escS(hp.id)}"`)}${climates}${this._pumpFields(hp, `hp-${hp.id}`)}${actions}</section></div>`;
  }

  _itemFor(el) {
    const kind = el.dataset.kind;
    if (!kind) return null;
    if (el.dataset.id) return this._cfg[kind].find((x) => x.id === el.dataset.id);
    return this._selected(kind);
  }

  _listAction(act, el) {
    const kind = el.dataset.kind;
    const list = this._cfg[kind];
    const cur = this._selected(kind);
    if (act === "add") {
      const base = this._t({ profiles: "new_profile", plannings: "new_planning", groups: "new_group", heat_pumps: "new_pump" }[kind]);
      let name = base;
      for (let i = 2; list.some((x) => normName(x.name) === normName(name)); i++) name = `${base} ${i}`;
      const item = { id: newId(), name };
      if (kind === "profiles") {
        Object.assign(item, { hvac_mode: "heat", temperature: 20 });
        for (const pl of this._cfg.plannings) pl.allowed.push(item.id);
      }
      if (kind === "plannings") { item.allowed = this._cfg.profiles.map((p) => p.id); item.programs = {}; this._programs[item.id] = {}; }
      if (kind === "groups" || kind === "heat_pumps") item.climates = [];
      list.push(item);
      this._item[kind] = item.id;
    } else if (act === "move" && cur) {
      const i = list.indexOf(cur);
      const j = i + Number(el.dataset.value);
      if (j < 0 || j >= list.length) return;
      [list[i], list[j]] = [list[j], list[i]];
    } else if (act === "dup" && cur) {
      const item = { ...clone(cur), id: newId(), name: this._tf("copy_of", { n: cur.name }) };
      if (kind === "profiles") for (const pl of this._cfg.plannings) if (pl.allowed.includes(cur.id)) pl.allowed.push(item.id);
      if (kind === "plannings") { item.copy_from = cur.id; this._programs[item.id] = clone(this._programs[cur.id] || {}); }
      list.splice(list.indexOf(cur) + 1, 0, item);
      this._item[kind] = item.id;
    } else if (act === "del" && cur) {
      if ((kind === "profiles" || kind === "plannings") && list.length <= 1) { this._msg = { err: true, text: this._t("keep_one") }; this._render(); return; }
      if (kind === "profiles") {
        const used = this._usage(cur.id);
        if (used.length) { this._msg = { err: true, text: this._tf("in_use", { u: used.join(" · ") }) }; this._render(); return; }
        for (const pl of this._cfg.plannings) pl.allowed = pl.allowed.filter((x) => x !== cur.id);
      }
      if (kind === "plannings") delete this._programs[cur.id];
      if (kind === "groups") for (const pl of Object.values(this._programs)) delete pl[cur.id];
      list.splice(list.indexOf(cur), 1);
      this._item[kind] = list[0]?.id;
    }
    if (kind === "profiles") for (const p of list) p.color ??= this._colorOf(p.name);
    this._changed();
  }

  // ------------------------------------------------------------------ actions

  _changed() {
    this._msg = null;
    this._render();
  }

  _onClick(ev) {
    const el = ev.target.closest("[data-act]");
    if (!el || el.tagName === "INPUT") return;
    const { act, value } = el.dataset;
    const day = Number(el.dataset.day);
    const idx = Number(el.dataset.idx);
    switch (act) {
      case "tab": this._tab = value; this._msg = null; this._render(); return;
      case "item": this._item[el.dataset.kind] = value; this._msg = null; this._render(); return;
      case "planning": this._planning = value; this._sel = null; this._render(); return;
      case "group": this._group = value; this._sel = null; this._render(); return;
      case "mday": this._day = Number(value); this._sel = null; this._render(); return;
      case "seg":
        if (Date.now() - (this._dragEnd || 0) < 250) return;
        this._sel = { day, idx };
        this._day = day;
        this._render();
        return;
      case "close": this._sel = null; this._render(); return;
      case "open-settings":
        history.pushState(null, "", SETTINGS_URL);
        window.dispatchEvent(new CustomEvent("location-changed"));
        return;
      default: break;
    }
    if (!this._admin) return;
    switch (act) {
      case "profile": this._setProfile(value); break;
      case "split": this._splitSeg(); break;
      case "remove": this._removeSlot(); break;
      case "add-line": this._addLine(); break;
      case "copy-day": this._panel = this._panel === "day" ? null : "day"; this._render(); break;
      case "copy-week": this._panel = this._panel === "week" ? null : "week"; this._render(); break;
      case "copy-close": this._panel = null; this._render(); break;
      case "copy-day-do": this._copyDay(); break;
      case "copy-week-do": this._copyWeek(); break;
      case "cancel": this._reset(); this._msg = null; this._render(); break;
      case "add": case "move": case "dup": case "del": this._listAction(act, el); break;
      case "pmode": { const p = this._selected("profiles"); if (value) p.hvac_mode = value; else delete p.hvac_mode; this._changed(); break; }
      case "tstep": {
        const p = this._selected("profiles");
        const t = p.temperature == null ? 20 : Number(p.temperature) + Number(value);
        p.temperature = Math.min(35, Math.max(5, Math.round(t * 2) / 2));
        this._changed(); break;
      }
      case "tclear": delete this._selected("profiles").temperature; this._changed(); break;
      case "allow": {
        const pl = this._selected("plannings");
        pl.allowed = pl.allowed.includes(value) ? pl.allowed.filter((x) => x !== value) : this._cfg.profiles.map((p) => p.id).filter((x) => x === value || pl.allowed.includes(x));
        this._changed(); break;
      }
      case "save": this._save(); break;
      default: break;
    }
  }

  _onDblClick(ev) {
    const bar = ev.target.closest("[data-bar]");
    if (!bar || !this._admin || this._narrow) return;
    const box = bar.getBoundingClientRect();
    const minute = Math.round((((ev.clientX - box.left) / box.width) * DAY_MIN) / STEP) * STEP;
    this._insertAt(Number(bar.dataset.bar), Math.min(Math.max(minute, 0), DAY_MIN - STEP));
  }

  _onChange(ev) {
    const el = ev.target;
    if (this._admin && el.dataset?.offset) {
      const [eid, side] = el.dataset.offset.split("|");
      const v = Math.round(Math.min(3, Math.max(-3, Number(el.value) || 0)) * 2) / 2;
      const offs = (this._cfg.offsets ??= {});
      const split = { ...(offs[eid] || {}) };
      if (v) split[side] = v; else delete split[side];
      if (Object.keys(split).length) offs[eid] = split; else delete offs[eid];
      this._changed();
      return;
    }
    if (this._admin && el.dataset?.field) {
      const item = this._itemFor(el);
      if (!item) return;
      const field = el.dataset.field;
      let v = el.value;
      if (field === "name") {
        v = v.trim();
        const clash = this._cfg[el.dataset.kind].some((x) => x !== item && normName(x.name) === normName(v));
        if (!v || clash) { this._msg = { err: true, text: !v ? this._t("name") : `« ${v} »` }; this._render(); return; }
        item.name = v;
        if (el.dataset.kind === "profiles") item.color = this._colorOf(v);
      } else if (field === "quiet_outdoor") {
        if (v === "on") item.quiet_outdoor = true; else if (v === "off") item.quiet_outdoor = false; else delete item.quiet_outdoor;
      } else if (el.dataset.num) {
        if (v === "") delete item[field]; else item[field] = Number(v);
      } else if (v === "") delete item[field];
      else item[field] = v;
      this._changed();
      return;
    }
    if (el.dataset?.act !== "time" || !this._admin || !this._sel) return;
    const { day, idx } = this._sel;
    const slots = clone(this._slots(day));
    const t = el.value;
    if (!/^\d\d:\d\d$/.test(t)) return;
    if (slots.some(([x], i) => x === t && i !== idx)) { this._msg = { err: true, text: this._tf("time_taken", { t }) }; this._render(); return; }
    const pid = slots[idx][1];
    slots[idx] = [t, pid];
    this._setSlots(day, slots);
    this._sel = { day, idx: this._slots(day).findIndex(([x]) => x === t) };
    this._changed();
  }

  _setProfile(pid) {
    const { day, idx } = this._sel;
    const slots = clone(this._slots(day));
    if (idx === -1) {
      slots.unshift(["00:00", pid]);   // début de journée : nouveau changement à minuit
      this._setSlots(day, slots);
      this._sel = { day, idx: 0 };
    } else {
      slots[idx] = [slots[idx][0], pid];
      this._setSlots(day, slots);
    }
    this._changed();
  }

  _insertAt(day, minute) {
    const seg = this._segments(day).find((s) => minute >= s.start && minute < s.end);
    const t = toHHMM(minute);
    const slots = clone(this._slots(day));
    if (slots.some(([x]) => x === t)) return;
    slots.push([t, seg?.pid || this._allowed()[0]]);
    this._setSlots(day, slots);
    this._sel = { day, idx: this._slots(day).findIndex(([x]) => x === t) };
    this._changed();
  }

  _splitSeg() {
    const { day, idx } = this._sel;
    const seg = this._segments(day).find((s) => s.idx === idx);
    const mid = Math.round((seg.start + seg.end) / 2 / STEP) * STEP;
    this._insertAt(day, Math.min(Math.max(mid, seg.start + STEP), seg.end - STEP));
  }

  _removeSlot() {
    const { day, idx } = this._sel;
    const slots = clone(this._slots(day));
    slots.splice(idx, 1);
    this._setSlots(day, slots);
    this._sel = null;
    this._changed();
  }

  _addLine() {
    const d = this._day;
    const used = new Set(this._slots(d).map(([t]) => toMin(t)));
    const last = this._slots(d).length ? toMin(this._slots(d).at(-1)[0]) : 11 * 60;
    let minute = Math.min(last + 60, DAY_MIN - STEP);
    while (used.has(minute) && minute > 0) minute -= STEP;
    this._insertAt(d, minute);
  }

  _copyDay() {
    const src = this._sel?.day ?? this._day;
    const days = [...this.shadowRoot.querySelectorAll("[data-copy-day]:checked")].map((x) => Number(x.dataset.copyDay));
    for (const d of days) this._setSlots(d, clone(this._slots(src)));
    this._panel = null;
    this._msg = days.length ? { text: this._t("copied") } : null;
    this._render();
  }

  _copyWeek() {
    const pls = [...this.shadowRoot.querySelectorAll("[data-copy-pl]:checked")].map((x) => x.dataset.copyPl);
    const gids = [...this.shadowRoot.querySelectorAll("[data-copy-g]:checked")].map((x) => x.dataset.copyG);
    const program = this._program();
    const used = new Set(Object.values(program).flatMap((s) => s.map(([, pid]) => pid)));
    for (const plid of pls) {
      const pl = this._cfg.plannings.find((p) => p.id === plid);
      const bad = [...used].find((pid) => !pl.allowed.includes(pid));
      if (bad) { this._msg = { err: true, text: this._tf("copy_refused", { p: this._profile(bad)?.name || bad, pl: pl.name }) }; this._render(); return; }
    }
    for (const plid of pls) {
      const targets = (this._programs[plid] ??= {});
      for (const gid of gids) targets[gid] = clone(program);
      if (plid !== this._planning) targets[this._group] = clone(program);
    }
    this._panel = null;
    this._msg = { text: this._t("copied") };
    this._render();
  }

  _onPointerDown(ev) {
    const grip = ev.target.closest(".grip");
    if (!grip || !this._admin) return;
    ev.preventDefault();
    const day = Number(grip.dataset.day);
    const idx = Number(grip.dataset.idx);
    const bar = grip.parentElement;
    const box = bar.getBoundingClientRect();
    const slots = clone(this._slots(day));
    const lo = idx > 0 ? toMin(slots[idx - 1][0]) + STEP : STEP;
    const hi = idx + 1 < slots.length ? toMin(slots[idx + 1][0]) - STEP : DAY_MIN - STEP;
    grip.setPointerCapture(ev.pointerId);
    grip.classList.add("drag");
    let minute = toMin(slots[idx][0]);
    const tip = document.createElement("span");
    tip.className = "tip";
    bar.append(tip);
    const move = (e) => {
      const raw = ((e.clientX - box.left) / box.width) * DAY_MIN;
      minute = Math.min(Math.max(Math.round(raw / STEP) * STEP, lo), hi);
      grip.style.left = `${(minute / DAY_MIN) * 100}%`;
      tip.style.left = grip.style.left;
      tip.textContent = toHHMM(minute);
      // aperçu : les deux plages voisines suivent la poignée
      const segs = bar.querySelectorAll(".seg");
      const before = [...segs].find((s) => Number(s.dataset.idx) === idx - 1);
      const after = [...segs].find((s) => Number(s.dataset.idx) === idx);
      if (before) before.style.width = `${((minute - (idx > 0 ? toMin(slots[idx - 1][0]) : 0)) / DAY_MIN) * 100}%`;
      if (after) {
        const end = idx + 1 < slots.length ? toMin(slots[idx + 1][0]) : DAY_MIN;
        after.style.left = `${(minute / DAY_MIN) * 100}%`;
        after.style.width = `${((end - minute) / DAY_MIN) * 100}%`;
      }
    };
    const up = () => {
      grip.removeEventListener("pointermove", move);
      grip.removeEventListener("pointerup", up);
      grip.removeEventListener("pointercancel", up);
      this._dragEnd = Date.now();
      if (toHHMM(minute) !== slots[idx][0]) {
        slots[idx] = [toHHMM(minute), slots[idx][1]];
        this._setSlots(day, slots);
        this._sel = { day, idx };
        this._changed();
      } else this._render();
    };
    grip.addEventListener("pointermove", move);
    grip.addEventListener("pointerup", up);
    grip.addEventListener("pointercancel", up);
  }

  async _save() {
    const programs = {};
    for (const [plid, gid, program] of Object.values(this._programChanges())) (programs[plid] ??= {})[gid] = program;
    const msg = { type: "split_scheduler/config/save", programs, ...this._collectionChanges() };
    if (JSON.stringify(this._orig.settings) !== JSON.stringify(this._settings)) msg.settings = this._settings;
    this._saving = true;
    this._render();
    try {
      await this._hass.callWS(msg);
      this._msg = { text: this._t("saved") };
      // la configuration enregistrée devient la référence (l'intégration se recharge)
      for (const pl of this._cfg.plannings) pl.programs = clone(this._programs[pl.id] || {});
      this._cfg.settings = clone(this._settings);
      this._server = clone(this._cfg);
      this._orig = clone(this._cfg);
      setTimeout(() => this._load(), 2500);
    } catch (err) {
      this._msg = { err: true, text: err?.message || String(err) };
    }
    this._saving = false;
    this._render();
  }
}

const SETTINGS_CSS = `
  :host { display: block; }
  ha-card { display: flex; flex-direction: column; overflow: hidden; }
  .msg { padding: 24px; color: var(--secondary-text-color); }
  .err { color: var(--error-color, #db4437); }
  header { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 16px 16px 4px; }
  h1 { margin: 0; font-size: 20px; font-weight: 500; flex: 1; min-width: 200px; }
  .actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .dirty { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--warning-color, #b06000); }
  .dirty i { width: 8px; height: 8px; border-radius: 50%; background: var(--warning-color, #f9a825); }
  .note { font-size: 13px; }
  .note.ok { color: var(--success-color, #1e8e3e); }
  .ro { font-size: 13px; color: var(--secondary-text-color); }
  button { font: inherit; cursor: pointer; color: inherit; }
  button:disabled { cursor: default; opacity: .55; }
  .filled, .outlined, .text { height: 36px; padding: 0 16px; border-radius: 18px; font-size: 14px; font-weight: 500; }
  .filled { border: 0; background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .outlined { border: 1px solid var(--divider-color); background: none; }
  .text { border: 0; background: none; color: var(--primary-color); }
  nav { display: flex; gap: 2px; padding: 0 8px; border-bottom: 1px solid var(--divider-color); overflow-x: auto; scrollbar-width: none; }
  nav button { border: 0; background: none; padding: 12px 12px 10px; font-size: 14px; color: var(--secondary-text-color); border-bottom: 2px solid transparent; white-space: nowrap; }
  nav button.on { color: var(--primary-color); border-bottom-color: var(--primary-color); font-weight: 500; }
  .body { padding: 16px; display: flex; flex-direction: column; gap: 14px; }
  .soon { display: flex; flex-direction: column; gap: 12px; align-items: flex-start; color: var(--secondary-text-color); }
  .soon p { margin: 0; line-height: 20px; }
  .pickers { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 10px; }
  .lab { font-size: 13px; color: var(--secondary-text-color); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { height: 32px; padding: 0 12px; border-radius: 16px; border: 1px solid var(--divider-color); background: none; font-size: 13.5px; }
  .chip.on { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color, #fff); font-weight: 500; }
  .warn { display: flex; gap: 10px; padding: 10px 12px; border-radius: 10px; background: color-mix(in srgb, var(--error-color, #db4437) 12%, transparent); font-size: 13px; line-height: 19px; }
  .week { display: flex; flex-direction: column; gap: 10px; }
  .day { display: grid; grid-template-columns: 92px 1fr 116px; align-items: center; gap: 12px; }
  .dname { font-size: 14px; }
  .dname.on { font-weight: 500; color: var(--primary-color); }
  .dcount { font-size: 12px; color: var(--secondary-text-color); }
  .ticks { display: flex; justify-content: space-between; font-size: 11px; color: var(--secondary-text-color); }
  .bar { position: relative; border-radius: 6px; background: var(--secondary-background-color); touch-action: none; }
  .seg { position: absolute; top: 0; bottom: 0; border: 0; border-right: 2px solid var(--card-background-color, #fff); padding: 0 6px; color: #fff; font-size: 11.5px; text-align: left; overflow: hidden; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,.25); }
  .seg:first-child { border-radius: 6px 0 0 6px; }
  .seg:last-of-type { border-radius: 0 6px 6px 0; border-right: 0; }
  .seg.inh { opacity: .55; background-image: repeating-linear-gradient(135deg, rgba(255,255,255,.25) 0 6px, transparent 6px 12px) !important; }
  .seg.sel { box-shadow: inset 0 0 0 3px var(--primary-text-color); z-index: 1; }
  .grip { position: absolute; top: -6px; bottom: -6px; width: 12px; margin-left: -6px; border-radius: 6px; background: var(--card-background-color, #fff); border: 2px solid var(--primary-color); box-sizing: border-box; cursor: ew-resize; z-index: 2; touch-action: none; }
  .grip.drag { background: var(--primary-color); }
  .tip { position: absolute; top: -30px; transform: translateX(-50%); padding: 2px 6px; border-radius: 6px; background: var(--primary-text-color); color: var(--card-background-color, #fff); font-size: 12px; z-index: 3; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 12.5px; color: var(--secondary-text-color); }
  .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; }
  .editor { display: flex; flex-direction: column; gap: 10px; padding: 14px; border-radius: 12px; border: 1px solid var(--divider-color); background: var(--secondary-background-color); }
  .editor h2 { margin: 0; font-size: 15px; font-weight: 500; }
  .small { margin: 0; font-size: 12.5px; color: var(--secondary-text-color); }
  .field { display: flex; flex-direction: column; gap: 4px; font-size: 12.5px; color: var(--secondary-text-color); max-width: 200px; }
  .field input { height: 40px; padding: 0 10px; border-radius: 8px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); font: inherit; font-size: 16px; }
  .pchips { display: flex; flex-wrap: wrap; gap: 6px; }
  .pchip { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border-radius: 17px; border: 1px solid var(--divider-color); background: var(--card-background-color); font-size: 13.5px; }
  .pchip i { width: 9px; height: 9px; border-radius: 50%; background: var(--c); }
  .pchip.on { border-color: var(--c); background: color-mix(in srgb, var(--c) 20%, var(--card-background-color)); font-weight: 500; }
  .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .row button { white-space: nowrap; }
  .row.wrap { flex-wrap: wrap; }
  .checks { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 14px; }
  .checks label { display: inline-flex; align-items: center; gap: 6px; min-height: 32px; }
  .hint { margin: 0; font-size: 12.5px; color: var(--secondary-text-color); }
  .pills { display: flex; justify-content: space-between; gap: 4px; }
  .pill { width: 42px; height: 42px; border-radius: 50%; border: 1px solid var(--divider-color); background: none; font-size: 13px; }
  .pill.on { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color, #fff); }
  .lines { display: flex; flex-direction: column; gap: 6px; }
  .line { display: flex; align-items: center; gap: 12px; min-height: 52px; padding: 0 12px; border-radius: 10px; border: 0; background: var(--secondary-background-color); text-align: left; }
  .line.on { outline: 2px solid var(--primary-color); }
  .line.inh { opacity: .7; }
  .line .time { font-size: 20px; font-weight: 300; width: 64px; }
  .line i { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .line .pname { flex: 1; font-size: 15px; }
  .line .chev { color: var(--secondary-text-color); font-size: 18px; }
  .general { max-width: 640px; }
  .split { display: grid; grid-template-columns: minmax(220px, 300px) 1fr; gap: 16px; align-items: start; }
  .narrow .split { grid-template-columns: 1fr; }
  .list { display: flex; flex-direction: column; gap: 4px; padding: 10px; border: 1px solid var(--divider-color); border-radius: 12px; }
  .lhead { display: flex; align-items: center; justify-content: space-between; padding: 2px 4px 6px; font-weight: 500; }
  .filled.sm { height: 32px; padding: 0 12px; font-size: 13px; }
  .li { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border: 0; border-radius: 10px; background: none; text-align: left; }
  .li.on { background: color-mix(in srgb, var(--primary-color) 14%, transparent); }
  .li i, .dhead i { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .li .col, .srow .col { display: flex; flex-direction: column; min-width: 0; }
  .li strong { font-weight: 500; font-size: 14.5px; }
  .li .small { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .detail { display: flex; flex-direction: column; gap: 12px; padding: 14px 16px; border: 1px solid var(--divider-color); border-radius: 12px; min-width: 0; }
  .detail h2 { margin: 0; font-size: 18px; font-weight: 500; }
  .detail h3, .sub h3 { margin: 6px 0 0; font-size: 15px; font-weight: 500; }
  .dhead { display: flex; align-items: center; gap: 10px; }
  .field.wide { max-width: 420px; }
  .field em { font-style: normal; font-size: 12px; }
  .field select { height: 40px; padding: 0 8px; border-radius: 8px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); font: inherit; font-size: 15px; }
  .grid2 { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px 14px; }
  .grid2 .field { max-width: none; }
  .modes { display: flex; flex-wrap: wrap; gap: 6px; }
  .mode { height: 36px; padding: 0 12px; border-radius: 8px; border: 1px solid var(--divider-color); background: none; font-size: 13.5px; }
  .mode.on { border-color: var(--primary-color); background: color-mix(in srgb, var(--primary-color) 14%, transparent); font-weight: 500; }
  .stepper { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
  .round { width: 42px; height: 42px; border-radius: 50%; border: 1px solid var(--divider-color); background: none; font-size: 20px; }
  .tval { font-size: 28px; font-weight: 300; min-width: 110px; text-align: center; }
  .tval small { font-size: 15px; color: var(--secondary-text-color); }
  .srow { display: grid; grid-template-columns: 1fr 130px 130px; gap: 10px; align-items: end; padding: 6px 0; border-bottom: 1px solid var(--divider-color); }
  .narrow .srow { grid-template-columns: 1fr 1fr; }
  .narrow .srow .col { grid-column: 1 / -1; }
  .sub { display: flex; flex-direction: column; gap: 10px; padding-top: 8px; border-top: 1px solid var(--divider-color); }
  .danger { color: var(--error-color, #db4437); }
  .haform { max-width: 560px; }
`;

if (!customElements.get("split-scheduler-settings-card")) {
  customElements.define("split-scheduler-settings-card", SplitSchedulerSettingsCard);
  window.customCards = window.customCards || [];
  const l = (navigator.language || "fr").startsWith("fr") ? "fr" : "en";
  window.customCards.push({ type: "split-scheduler-settings-card", name: TXT[l].name, description: TXT[l].desc, preview: false });
}
