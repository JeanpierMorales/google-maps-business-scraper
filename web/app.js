"use strict";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

const ICONS = {
  phone: '<svg viewBox="0 0 24 24"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2Z"/></svg>',
  wa: '<svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2.1 1-2.4c.3-.3.6-.3.8-.3h.6c.2 0 .4 0 .6.5l.9 2.1c.1.2.1.3 0 .5l-.3.5-.4.5c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.4 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l2 .9c.3.2.5.2.5.4.1.1.1.7-.1 1.4Z"/></svg>',
  mail: '<svg viewBox="0 0 24 24"><path d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm9 7.2L4.4 7H4v.8l8 5.5 8-5.5V7h-.4L12 12.2Z"/></svg>',
  instagram: '<svg viewBox="0 0 24 24"><path d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Zm0 8.2a3.2 3.2 0 1 1 0-6.4 3.2 3.2 0 0 1 0 6.4ZM17.3 5.5a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4ZM12 2c-2.7 0-3 0-4.1.1C4.3 2.2 2.2 4.3 2.1 7.9 2 9 2 9.3 2 12s0 3 .1 4.1c.1 3.6 2.2 5.7 5.8 5.8 1.1.1 1.4.1 4.1.1s3 0 4.1-.1c3.6-.1 5.7-2.2 5.8-5.8.1-1.1.1-1.4.1-4.1s0-3-.1-4.1c-.1-3.6-2.2-5.7-5.8-5.8C15 2 14.7 2 12 2Z"/></svg>',
  facebook: '<svg viewBox="0 0 24 24"><path d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.5 1.6-1.5h1.7V4.5c-.3 0-1.3-.1-2.4-.1-2.4 0-4.1 1.5-4.1 4.2v2.3H7.6V14h2.7v8h3.2Z"/></svg>',
  tiktok: '<svg viewBox="0 0 24 24"><path d="M16.6 3c.4 2.2 1.8 3.6 4 3.8v3.1c-1.5.1-2.8-.4-4-1.2v5.8c0 7.4-8 9.7-11.3 4.4-2.1-3.4-.8-9.3 6-9.6v3.3c-.5.1-1.1.2-1.6.4-1.5.5-2.3 1.5-2.1 3.1.5 3.2 6.3 4.1 5.8-2.1V3h3.2Z"/></svg>',
  youtube: '<svg viewBox="0 0 24 24"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8ZM10 15V9l5.2 3L10 15Z"/></svg>',
  linkedin: '<svg viewBox="0 0 24 24"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9.5h4V21H3V9.5Zm6.5 0h3.8v1.6h.1c.5-1 1.8-2 3.8-2 4 0 4.8 2.6 4.8 6V21h-4v-5.2c0-1.2 0-2.8-1.7-2.8s-2 1.3-2 2.7V21h-4V9.5Z"/></svg>',
  twitter: '<svg viewBox="0 0 24 24"><path d="M17.8 3h3.1l-6.8 7.8 8 10.2h-6.3l-4.9-6.4L5.3 21H2.2l7.3-8.3L1.9 3h6.4l4.4 5.9L17.8 3Zm-1.1 16.2h1.7L7.4 4.7H5.6l11.1 14.5Z"/></svg>',
  map: '<svg viewBox="0 0 24 24"><path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7Zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5Z"/></svg>',
};

const PHASE_ORDER = ["lista", "detalle", "webs", "excel", "fin"];
const NO_WEB = ["Sin web", "Solo redes sociales", "Linktree / bio", "Directorio / plataforma"];

const state = {
  jobId: null,
  runId: null,        // id de historial cargado
  version: -1,
  sinceLog: 0,
  rows: [],
  prevKeys: new Set(),
  filter: "all",
  search: "",
  sort: { key: "lead_score", dir: -1 },
  limit: 0,
  view: "table",
  timer: null,
  poll: null,
  map: null,
  markers: null,
  status: null,
};

// ------------------------------------------------------------------ helpers

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function keyOf(b) { return b.place_id || `${b.nombre}|${b.direccion}`; }
function fmtTime(sec) {
  const m = Math.floor(sec / 60), s = sec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
function shortUrl(url) { return String(url || "").replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, ""); }
function isBadWeb(b) {
  return b.tipo_web === "Web propia" && ((b.estado_web && !String(b.estado_web).startsWith("OK")) || b.web_responsive === "No");
}

const FILTERS = {
  all: () => true,
  alta: (b) => b.prioridad === "Alta",
  sinweb: (b) => NO_WEB.includes(b.tipo_web),
  whatsapp: (b) => !!b.whatsapp,
  email: (b) => !!b.email,
  webmala: isBadWeb,
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
  return data;
}

// --------------------------------------------------------------------- form

$("#limit").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  $$("#limit button").forEach((b) => b.classList.toggle("active", b === btn));
  state.limit = Number(btn.dataset.value);
});

$("#concurrencia").addEventListener("input", (e) => { $("#concurrencyValue").textContent = e.target.value; });

$$(".examples .chip").forEach((chip) => chip.addEventListener("click", () => {
  $("#tipo").value = chip.dataset.tipo;
  $("#ubicacion").value = chip.dataset.ubicacion;
  $("#tipo").focus();
}));

$("#searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const body = {
    tipo: form.get("tipo"),
    ubicacion: form.get("ubicacion"),
    zonas: form.get("zonas"),
    max_resultados: state.limit,
    rating_min: form.get("rating_min"),
    resenas_min: form.get("resenas_min"),
    solo_con_telefono: form.has("solo_con_telefono"),
    solo_sin_web: form.has("solo_sin_web"),
    excluir_cerrados: form.has("excluir_cerrados"),
    analizar_webs: form.has("analizar_webs"),
    ver_navegador: form.has("ver_navegador"),
    concurrencia: form.get("concurrencia"),
    radio_km: form.get("radio_km"),
  };
  $("#formError").textContent = "";
  $("#startBtn").disabled = true;
  try {
    const { id } = await api("/api/jobs", { method: "POST", body: JSON.stringify(body) });
    startJob(id, body);
  } catch (err) {
    $("#formError").textContent = err.message;
    $("#startBtn").disabled = false;
  }
});

$("#stopBtn").addEventListener("click", async () => {
  if (!state.jobId) return;
  $("#stopBtn").disabled = true;
  $("#stopBtn").textContent = "Deteniendo…";
  await api(`/api/jobs/${state.jobId}/cancel`, { method: "POST" }).catch(() => {});
});

$("#openFolder").addEventListener("click", () => api("/api/open-folder", { method: "POST" }).catch(() => {}));

// En la nube no hay carpeta local ni navegador visible.
api("/api/config").then((cfg) => {
  if (!cfg.cloud) return;
  $("#openFolder").style.display = "none";
  const verNav = $('input[name="ver_navegador"]')?.closest("label");
  if (verNav) verNav.style.display = "none";
}).catch(() => {});

// ---------------------------------------------------------------- job flow

function resetView(title) {
  state.rows = [];
  state.prevKeys = new Set();
  state.version = -1;
  state.sinceLog = 0;
  $("#log").innerHTML = "";
  $("#emptyState").classList.add("hidden");
  $("#statusCard").classList.remove("hidden");
  $("#kpis").classList.remove("hidden");
  $("#results").classList.remove("hidden");
  $("#statusTitle").textContent = title;
  $("#downloadBtn").classList.add("hidden");
  renderKpis(null);
  renderRows();
}

function startJob(id, body) {
  state.jobId = id;
  state.runId = null;
  resetView(`${body.tipo} en ${body.ubicacion}`);
  setRunning(true);
  $("#statusEyebrow").textContent = "En curso";
  $("#statusEyebrow").classList.remove("error");
  clearInterval(state.poll);
  state.poll = setInterval(pollJob, 1000);
  pollJob();
  highlightHistory();
}

function setRunning(running) {
  $("#startBtn").disabled = running;
  $("#startBtn").classList.toggle("hidden", running);
  $("#stopBtn").classList.toggle("hidden", !running);
  $("#stopBtn").disabled = false;
  $("#stopBtn").textContent = "Detener y guardar lo obtenido";
}

async function pollJob() {
  if (!state.jobId) return;
  let job;
  try {
    job = await api(`/api/jobs/${state.jobId}?since_log=${state.sinceLog}&version=${state.version}`);
  } catch (err) {
    return;
  }
  state.version = job.version;
  state.sinceLog = job.log_total;
  appendLog(job.log);
  renderStatus(job);
  if (job.rows) {
    state.rows = job.rows;
    renderRows();
    renderKpis(job.result ? job.result.summary : null);
  }
  if (job.status !== "running") {
    clearInterval(state.poll);
    setRunning(false);
    loadHistory();
  }
}

function appendLog(entries) {
  if (!entries || !entries.length) return;
  const log = $("#log");
  const atBottom = log.scrollTop + log.clientHeight >= log.scrollHeight - 10;
  for (const entry of entries) {
    const time = new Date(entry.t * 1000).toLocaleTimeString("es-PE", { hour12: false });
    const line = document.createElement("div");
    line.className = entry.level;
    line.textContent = `${time}  ${entry.message}`;
    log.appendChild(line);
  }
  if (atBottom) log.scrollTop = log.scrollHeight;
}

function renderStatus(job) {
  $("#timer").textContent = fmtTime(job.elapsed || 0);
  const phaseIndex = PHASE_ORDER.indexOf(job.phase);
  $$("#steps li").forEach((li) => {
    const i = PHASE_ORDER.indexOf(li.dataset.phase);
    li.classList.toggle("done", phaseIndex > i || job.status === "done");
    li.classList.toggle("active", phaseIndex === i && job.status === "running");
  });

  const bar = $("#progressBar");
  let pct = 0, text = job.message;
  bar.classList.remove("indeterminate");
  if (job.status === "running") {
    if (job.phase === "lista" || job.phase === "inicio") {
      bar.classList.add("indeterminate");
      const q = job.query_total > 1 ? ` (búsqueda ${job.query_index}/${job.query_total})` : "";
      text = job.phase === "inicio" ? "Abriendo Google Maps…" : `Cargando lista: ${job.loaded} negocios${q}`;
    } else if (job.phase === "detalle") {
      pct = job.detail_total ? job.detail_done / job.detail_total : 0;
      text = `Leyendo fichas: ${job.detail_done} de ${job.detail_total}`;
    } else if (job.phase === "webs") {
      pct = job.web_total ? job.web_done / job.web_total : 1;
      text = `Revisando sitios web: ${job.web_done} de ${job.web_total}`;
    } else if (job.phase === "excel") {
      pct = 1; text = "Generando Excel…";
    }
    bar.style.width = `${Math.round(pct * 100)}%`;
  } else {
    bar.style.width = "100%";
  }

  const eyebrow = $("#statusEyebrow");
  if (job.status === "done") {
    eyebrow.textContent = "Completado";
    text = `Listo: ${job.result.summary.total} negocios en ${job.result.stats.duracion}` +
      (job.result.stats.descartados ? ` · ${job.result.stats.descartados} descartados por filtros` : "");
  } else if (job.status === "cancelled") {
    eyebrow.textContent = "Detenido — resultados parciales guardados";
    text = `Se guardaron ${job.result.summary.total} negocios`;
  } else if (job.status === "error") {
    eyebrow.textContent = "Error";
    eyebrow.classList.add("error");
    text = job.error;
  }
  $("#progressText").textContent = text;

  if (job.result && job.result.excel) {
    const link = $("#downloadBtn");
    link.href = `/download/${encodeURIComponent(job.result.excel)}`;
    link.classList.remove("hidden");
  }
}

$("#toggleLog").addEventListener("click", () => {
  const log = $("#log");
  log.classList.toggle("hidden");
  $("#toggleLog").textContent = log.classList.contains("hidden") ? "Ver registro" : "Ocultar registro";
  log.scrollTop = log.scrollHeight;
});

// ----------------------------------------------------------------- KPIs

function computeSummary(rows) {
  const ratings = rows.map((b) => b.rating).filter((r) => typeof r === "number");
  return {
    total: rows.length,
    con_whatsapp: rows.filter((b) => b.whatsapp).length,
    con_telefono: rows.filter((b) => b.telefono).length,
    sin_web: rows.filter((b) => NO_WEB.includes(b.tipo_web)).length,
    prioridad_alta: rows.filter((b) => b.prioridad === "Alta").length,
    con_email: rows.filter((b) => b.email).length,
    con_instagram: rows.filter((b) => b.instagram).length,
    rating_promedio: ratings.length ? (ratings.reduce((a, b) => a + b, 0) / ratings.length).toFixed(2) : null,
  };
}

function renderKpis(summary) {
  const s = summary || computeSummary(state.rows);
  const pct = (n) => (s.total ? `${Math.round((n / s.total) * 100)}% del total` : "—");
  const items = [
    { label: "Negocios", value: s.total, sub: `${s.con_telefono ?? 0} con teléfono` },
    { label: "Prioridad alta", value: s.prioridad_alta, sub: pct(s.prioridad_alta), highlight: true },
    { label: "Sin web propia", value: s.sin_web, sub: pct(s.sin_web) },
    { label: "Con WhatsApp", value: s.con_whatsapp, sub: pct(s.con_whatsapp) },
    { label: "Con email", value: s.con_email, sub: `${s.con_instagram ?? 0} con Instagram` },
    { label: "Rating promedio", value: s.rating_promedio ?? "—", sub: "de 5 estrellas" },
  ];
  $("#kpis").innerHTML = items.map((k) => `
    <div class="card kpi ${k.highlight ? "highlight" : ""}">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value">${esc(k.value ?? 0)}</div>
      <div class="kpi-sub">${esc(k.sub)}</div>
    </div>`).join("");
}

// ----------------------------------------------------------------- table

$("#filterChips").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  state.filter = chip.dataset.filter;
  $$("#filterChips .chip").forEach((c) => c.classList.toggle("active", c === chip));
  renderRows();
});

$("#searchInput").addEventListener("input", (e) => {
  state.search = e.target.value.trim().toLowerCase();
  renderRows();
});

$$("th[data-sort]").forEach((th) => th.addEventListener("click", () => {
  const key = th.dataset.sort;
  if (state.sort.key === key) state.sort.dir *= -1;
  else state.sort = { key, dir: key === "nombre" || key === "direccion" || key === "tipo_web" ? 1 : -1 };
  renderRows();
}));

function visibleRows() {
  const filter = FILTERS[state.filter];
  const q = state.search;
  const { key, dir } = state.sort;
  return state.rows
    .filter(filter)
    .filter((b) => !q || `${b.nombre} ${b.categoria} ${b.direccion} ${b.telefono}`.toLowerCase().includes(q))
    .sort((a, b) => {
      let x = a[key], y = b[key];
      if (typeof x === "number" || typeof y === "number") {
        const diff = ((x ?? -1) - (y ?? -1)) * dir;
        return diff || ((b.resenas ?? 0) - (a.resenas ?? 0));
      }
      return String(x ?? "").localeCompare(String(y ?? ""), "es") * dir;
    });
}

function renderRows() {
  // Contadores de chips
  $$("#filterChips .chip").forEach((chip) => {
    chip.querySelector("b").textContent = state.rows.filter(FILTERS[chip.dataset.filter]).length;
  });
  $$("th[data-sort]").forEach((th) => {
    th.classList.toggle("sorted", th.dataset.sort === state.sort.key);
    th.classList.toggle("asc", th.dataset.sort === state.sort.key && state.sort.dir === 1);
  });

  const rows = visibleRows();
  const newKeys = new Set(state.rows.map(keyOf));
  $("#rows").innerHTML = rows.map((b) => rowHtml(b, !state.prevKeys.has(keyOf(b)) && state.prevKeys.size > 0)).join("");
  state.prevKeys = newKeys;
  $("#tableEmpty").classList.toggle("hidden", rows.length > 0 || state.rows.length === 0);
  if (state.view === "map") renderMap();
}

function webHtml(b) {
  const type = b.tipo_web || "Sin web";
  let badge = "";
  if (type === "Web propia") {
    const bad = isBadWeb(b);
    const label = bad ? (b.estado_web && !String(b.estado_web).startsWith("OK") ? b.estado_web : "No es móvil") : (b.plataforma_web || "Web propia");
    badge = `<span class="badge ${bad ? "bad" : "good"}">${esc(label)}</span>`;
  } else {
    badge = `<span class="badge">${esc(type)}</span>`;
  }
  const link = b.sitio_web ? `<a href="${esc(b.sitio_web)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${esc(shortUrl(b.sitio_web))}</a>` : "";
  return `<div class="web-cell">${badge}${link}</div>`;
}

function socialsHtml(b) {
  return `<div class="socials">${["instagram", "facebook", "tiktok", "youtube", "linkedin", "twitter"]
    .filter((k) => b[k])
    .map((k) => `<a href="${esc(b[k])}" target="_blank" rel="noopener" title="${k}" onclick="event.stopPropagation()">${ICONS[k]}</a>`)
    .join("") || '<span class="sub">—</span>'}</div>`;
}

function rowHtml(b, fresh) {
  const stars = b.rating != null
    ? `<span class="stars"><span class="star">★</span> <b>${Number(b.rating).toFixed(1)}</b> <span class="sub">(${b.resenas ?? 0})</span></span>`
    : '<span class="sub">Sin reseñas</span>';
  const contact = [
    b.telefono ? `<span>${ICONS.phone} ${esc(b.telefono)}</span>` : "",
    b.whatsapp ? `<a class="wa" href="${esc(b.whatsapp)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${ICONS.wa} WhatsApp</a>` : "",
    b.email ? `<a href="mailto:${esc(b.email)}" onclick="event.stopPropagation()">${ICONS.mail} ${esc(b.email)}</a>` : "",
  ].filter(Boolean).join("") || '<span class="sub">Sin contacto</span>';
  return `
    <tr data-key="${esc(keyOf(b))}" class="${fresh ? "fresh" : ""}">
      <td><span class="pill ${esc(b.prioridad)}">${esc(b.prioridad || "—")} <span class="score">${b.lead_score ?? ""}</span></span></td>
      <td><div class="name">${esc(b.nombre)}</div><div class="sub">${esc(b.categoria)}${b.estado_negocio && b.estado_negocio !== "Operativo" ? ` · <b>${esc(b.estado_negocio)}</b>` : ""}</div></td>
      <td>${stars}</td>
      <td><div class="contact">${contact}</div></td>
      <td>${webHtml(b)}</td>
      <td>${socialsHtml(b)}</td>
      <td><div class="addr">${esc(b.direccion)}</div></td>
    </tr>`;
}

$("#rows").addEventListener("click", (e) => {
  const tr = e.target.closest("tr");
  if (!tr) return;
  const b = state.rows.find((r) => keyOf(r) === tr.dataset.key);
  if (b) openDrawer(b);
});

// ----------------------------------------------------------------- drawer

function openDrawer(b) {
  const rows = [
    ["Categoría", b.categoria],
    ["Rating", b.rating != null ? `★ ${b.rating} (${b.resenas ?? 0} reseñas)` : ""],
    ["Dirección", b.direccion],
    ["Plus Code", b.plus_code],
    ["Teléfono", b.telefono_intl ? `${b.telefono_intl} (${b.tipo_telefono || "—"})` : ""],
    ["WhatsApp", b.whatsapp ? `<a href="${esc(b.whatsapp)}" target="_blank" rel="noopener">${esc(shortUrl(b.whatsapp))}</a>` : "", true],
    ["Email", b.email ? `<a href="mailto:${esc(b.email)}">${esc(b.email)}</a>` : "", true],
    ["Sitio web", b.sitio_web ? `<a href="${esc(b.sitio_web)}" target="_blank" rel="noopener">${esc(shortUrl(b.sitio_web))}</a>` : "", true],
    ["Tipo de web", b.tipo_web],
    ["Estado web", b.estado_web],
    ["Plataforma", b.plataforma_web],
    ["Web móvil", b.web_responsive],
    ["Horario", b.horario ? esc(b.horario).split(" | ").join("<br>") : "", true],
    ["Estado", b.estado_negocio],
    ["Perfil reclamado", b.perfil_reclamado],
    ["Distancia", b.distancia_km != null ? `${b.distancia_km} km del centro` : ""],
    ["Encontrado en", b.busqueda],
  ].filter((r) => r[1]);

  $("#drawerBody").innerHTML = `
    <span class="pill ${esc(b.prioridad)}">Prioridad ${esc(b.prioridad)} <span class="score">${b.lead_score}/100</span></span>
    <h1 style="margin-top:10px">${esc(b.nombre)}</h1>
    ${b.motivos ? `<div class="reasons">${esc(b.motivos)}</div>` : ""}
    <div class="actions">
      ${b.whatsapp ? `<a class="btn primary" href="${esc(b.whatsapp)}" target="_blank" rel="noopener">${ICONS.wa} Escribir por WhatsApp</a>` : ""}
      ${b.google_maps ? `<a class="btn ghost" href="${esc(b.google_maps)}" target="_blank" rel="noopener">${ICONS.map} Ver en Google Maps</a>` : ""}
    </div>
    <dl>${rows.map(([k, v, html]) => `<dt>${k}</dt><dd>${html ? v : esc(v)}</dd>`).join("")}</dl>
    ${socialsHtml(b)}
  `;
  $("#drawer").classList.add("open");
  $("#drawer").setAttribute("aria-hidden", "false");
  $("#drawerBackdrop").classList.remove("hidden");
}

function closeDrawer() {
  $("#drawer").classList.remove("open");
  $("#drawer").setAttribute("aria-hidden", "true");
  $("#drawerBackdrop").classList.add("hidden");
}
$("#drawerClose").addEventListener("click", closeDrawer);
$("#drawerBackdrop").addEventListener("click", closeDrawer);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });

// ------------------------------------------------------------------- map

$("#viewToggle").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  state.view = btn.dataset.view;
  $$("#viewToggle button").forEach((b) => b.classList.toggle("active", b === btn));
  $("#tableView").classList.toggle("hidden", state.view !== "table");
  $("#mapView").classList.toggle("hidden", state.view !== "map");
  if (state.view === "map") renderMap();
});

const PRIORITY_COLORS = { Alta: "#16a34a", Media: "#f59e0b", Baja: "#94a3b8", Descartar: "#ef4444" };

function renderMap() {
  if (typeof L === "undefined") {
    $("#map").innerHTML = '<p class="table-empty">No se pudo cargar el mapa (sin conexión).</p>';
    return;
  }
  if (!state.map) {
    state.map = L.map("map", { scrollWheelZoom: true });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap",
    }).addTo(state.map);
    state.markers = L.layerGroup().addTo(state.map);
  }
  setTimeout(() => state.map.invalidateSize(), 50);
  state.markers.clearLayers();
  const points = [];
  for (const b of visibleRows()) {
    if (b.lat == null || b.lng == null) continue;
    const icon = L.divIcon({
      className: "",
      html: `<div class="marker" style="background:${PRIORITY_COLORS[b.prioridad] || "#64748b"}"></div>`,
      iconSize: [14, 14],
    });
    const marker = L.marker([b.lat, b.lng], { icon }).bindPopup(`
      <b>${esc(b.nombre)}</b><br>${esc(b.categoria)}<br>
      ${b.rating != null ? `★ ${b.rating} (${b.resenas ?? 0})<br>` : ""}
      ${b.telefono ? `${esc(b.telefono)}<br>` : ""}
      <span style="color:${PRIORITY_COLORS[b.prioridad]}">Prioridad ${esc(b.prioridad)}</span>`);
    marker.on("dblclick", () => openDrawer(b));
    state.markers.addLayer(marker);
    points.push([b.lat, b.lng]);
  }
  if (points.length) state.map.fitBounds(points, { padding: [30, 30], maxZoom: 15 });
}

// --------------------------------------------------------------- history

async function loadHistory() {
  let items = [];
  try { items = await api("/api/history"); } catch (err) { /* sin historial */ }
  const list = $("#historyList");
  if (!items.length) {
    list.innerHTML = '<li class="empty-note">Aún no hay búsquedas guardadas.</li>';
    return;
  }
  list.innerHTML = items.map((item) => `
    <li data-id="${esc(item.id)}" data-excel="${esc(item.excel)}" title="${item.id ? "Ver resultados" : "Descargar Excel (versión anterior)"}">
      <div class="h-main">
        <div class="h-title">${esc(item.tipo)}${item.ubicacion ? ` · ${esc(item.ubicacion)}` : ""}</div>
        <div class="h-meta">${esc(item.fecha)}${item.total != null ? ` · ${item.total} negocios · ${item.sin_web} sin web` : " · formato anterior"}${item.parcial ? " · parcial" : ""}</div>
      </div>
      <a class="icon-btn" href="/download/${encodeURIComponent(item.excel)}" title="Descargar Excel" aria-label="Descargar Excel" onclick="event.stopPropagation()">
        <svg viewBox="0 0 24 24"><path d="M11 3h2v9.2l3.3-3.3 1.4 1.4L12 16l-5.7-5.7 1.4-1.4 3.3 3.3V3ZM5 18h14v2H5v-2Z"/></svg>
      </a>
    </li>`).join("");
  highlightHistory();
}

function highlightHistory() {
  $$("#historyList li").forEach((li) => li.classList.toggle("current", !!state.runId && li.dataset.id === state.runId));
}

$("#historyList").addEventListener("click", async (e) => {
  const li = e.target.closest("li[data-excel]");
  if (!li) return;
  if (!li.dataset.id) {
    window.location.href = `/download/${encodeURIComponent(li.dataset.excel)}`;
    return;
  }
  if (state.poll && !$("#stopBtn").classList.contains("hidden")) return; // hay una búsqueda en curso
  const data = await api(`/api/history/${encodeURIComponent(li.dataset.id)}`);
  state.jobId = null;
  state.runId = li.dataset.id;
  resetView(`${data.params.tipo} en ${data.params.ubicacion}`);
  state.rows = data.businesses;
  state.prevKeys = new Set(state.rows.map(keyOf));
  $("#statusEyebrow").textContent = data.stats.interrumpido ? "Resultado parcial guardado" : "Búsqueda guardada";
  $("#statusEyebrow").classList.remove("error");
  $("#timer").textContent = data.stats.duracion || "";
  $$("#steps li").forEach((li2) => { li2.classList.add("done"); li2.classList.remove("active"); });
  $("#progressBar").classList.remove("indeterminate");
  $("#progressBar").style.width = "100%";
  $("#progressText").textContent = `${data.stats.fecha} · ${data.summary.total} negocios · filtros: ${data.params.filtros_texto || "ninguno"}`;
  $("#downloadBtn").href = `/download/${encodeURIComponent(data.excel)}`;
  $("#downloadBtn").classList.remove("hidden");
  renderRows();
  renderKpis(data.summary);
  highlightHistory();
});

$("#refreshHistory").addEventListener("click", loadHistory);

loadHistory();
