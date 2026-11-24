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

const SETTINGS_VERSION = "1.19.0";
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
    this._programs = Object.fromEntries(this._cfg.plannings.map((p) => [p.id, clone(p.programs || {})]));
    this._settings = clone(this._cfg.settings);
    this._sel = null;
    this._panel = null;
    this._genForm = null;
  }

  get _admin() { return this._cfg?.admin === true; }

  _dirtyCount() {
    if (!this._cfg) return 0;
    let n = 0;
    for (const pl of this._cfg.plannings) {
      const ids = new Set([...Object.keys(pl.programs || {}), ...Object.keys(this._programs[pl.id] || {})]);
      for (const gid of ids) if (JSON.stringify(this._norm(pl.programs?.[gid])) !== JSON.stringify(this._norm(this._programs[pl.id]?.[gid]))) n++;
    }
    if (JSON.stringify(this._cfg.settings) !== JSON.stringify(this._settings)) n++;
    return n;
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
    let html;
    if (this._error) html = `<ha-card><div class="msg err">${escS(this._error)}</div></ha-card>`;
    else if (!this._cfg) html = `<ha-card><div class="msg">${escS(this._t("loading"))}</div></ha-card>`;
    else html = `<ha-card class="${this._narrow ? "narrow" : ""}">${this._renderHeader()}${this._renderTabs()}<div class="body">${this._renderBody()}</div></ha-card>`;
    this.shadowRoot.innerHTML = `<style>${SETTINGS_CSS}</style>${html}`;
    if (scrollY) this.shadowRoot.querySelector(".body")?.scrollTo(0, scrollY);
    if (this._cfg && this._tab === "general") this._mountGeneral();
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
            m: this._t("side")[m], o: this._t("side")[o], s: g.names?.[split] || split, g: g.name,
            p: hp.priority ? this._tf("conflict_prio", { h: hp.name }) : this._tf("conflict_free", { h: hp.name }),
          }));
        }
      }
    }
    if (!lines.length) return "";
    return `<div class="warn" role="alert">⚠️ <div><strong>${escS(this._t("conflict_title"))}</strong>${lines.slice(0, 8).map((l) => `<div>${escS(l)}</div>`).join("")}</div></div>`;
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
      case "tab": this._tab = value; this._render(); return;
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
    for (const pl of this._cfg.plannings) {
      const ids = new Set([...Object.keys(pl.programs || {}), ...Object.keys(this._programs[pl.id] || {})]);
      for (const gid of ids) {
        const now = this._norm(this._programs[pl.id]?.[gid]);
        if (JSON.stringify(this._norm(pl.programs?.[gid])) !== JSON.stringify(now)) (programs[pl.id] ??= {})[gid] = now;
      }
    }
    const msg = { type: "split_scheduler/config/save", programs };
    if (JSON.stringify(this._cfg.settings) !== JSON.stringify(this._settings)) msg.settings = this._settings;
    this._saving = true;
    this._render();
    try {
      await this._hass.callWS(msg);
      this._msg = { text: this._t("saved") };
      // la configuration enregistrée devient la référence (l'intégration se recharge)
      for (const pl of this._cfg.plannings) pl.programs = clone(this._programs[pl.id] || {});
      this._cfg.settings = clone(this._settings);
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
`;

if (!customElements.get("split-scheduler-settings-card")) {
  customElements.define("split-scheduler-settings-card", SplitSchedulerSettingsCard);
  window.customCards = window.customCards || [];
  const l = (navigator.language || "fr").startsWith("fr") ? "fr" : "en";
  window.customCards.push({ type: "split-scheduler-settings-card", name: TXT[l].name, description: TXT[l].desc, preview: false });
}
