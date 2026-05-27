let authToken = sessionStorage.getItem("omninet_token") || null;
let currentUser = null;
let alertsPollingIntervalId = null;
let latestItems = [];
let uiColumns = [];

const tableState = {
  search: "",
  sortColumn: "",
  sortDirection: "desc",
  pageSize: 10,
  page: 1,
};

/* ─── Toast System ─── */

function showToast(message, type = "info") {
  const container =
    document.getElementById("toast-container") ||
    (() => {
      const el = document.createElement("div");
      el.id = "toast-container";
      el.className = "toast-container";
      document.body.appendChild(el);
      return el;
    })();

  const icons = { success: "\u2713", error: "\u2717", info: "\u25CB" };
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${icons[type] || "\u25CB"} ${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">\u2715</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(16px)";
      toast.style.transition = "0.25s ease";
      setTimeout(() => toast.remove(), 250);
    }
  }, 4000);
}

/* ─── Modal Login ─── */

function openLoginModal() {
  const overlay = document.getElementById("login-modal");
  if (overlay) overlay.classList.add("open");
}

function closeLoginModal() {
  const overlay = document.getElementById("login-modal");
  if (overlay) overlay.classList.remove("open");
}

function updateUserUI(user) {
  currentUser = user;
  document.body.dataset.auth = user ? "logged-in" : "logged-out";

  const avatarEl = document.getElementById("sidebar-user-avatar");
  if (avatarEl) avatarEl.textContent = user ? (user.username?.charAt(0).toUpperCase() || "?") : "?";

  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) logoutBtn.style.display = user ? "inline-flex" : "none";
}

async function handleLogin(event) {
  event.preventDefault();
  const username = document.getElementById("modal-username")?.value ?? "";
  const password = document.getElementById("modal-password")?.value ?? "";

  document.getElementById("modal-login-status").textContent = "Connexion en cours...";
  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (response.status === 401) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      document.getElementById("modal-login-status").textContent = "Identifiants invalides";
      return;
    }
    if (!response.ok) {
      document.getElementById("modal-login-status").textContent = `Erreur ${response.status}`;
      return;
    }

    const data = await response.json();
    authToken = data.access_token;
    sessionStorage.setItem("omninet_token", authToken);
    closeLoginModal();

    const meResp = await fetch("/auth/me", {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (meResp.ok) {
      const me = await meResp.json();
      updateUserUI(me);
    }

    document.getElementById("modal-username").value = "";
    document.getElementById("modal-password").value = "";
    showToast("Connexion r\u00E9ussie", "success");
    refreshPageContent();
  } catch {
    document.getElementById("modal-login-status").textContent = "Erreur r\u00E9seau...";
  }
}

function handleLogout() {
  sessionStorage.removeItem("omninet_token");
  authToken = null;
  updateUserUI(null);
  showToast("D\u00E9connexion", "info");
  refreshPageContent();
}

/* ─── Sidebar ─── */

function initSidebar() {
  const page = document.body.dataset.page;
  if (page) {
    document.querySelectorAll(".sidebar-link").forEach((link) => {
      if (link.dataset.nav === page) link.classList.add("active");
    });
  }
}

/* ─── Skeleton ─── */

function showSkeleton(target) {
  const el = typeof target === "string" ? document.getElementById(target) : target;
  if (!el) return;
  el.innerHTML = "";
  const rows = Math.max(3, Math.floor(el.clientHeight / 60 || 3));
  const wrapper = document.createElement("div");
  wrapper.className = "skeleton-row";
  for (let i = 0; i < rows; i++) {
    const bar = document.createElement("div");
    bar.className = "skeleton";
    bar.style.width = `${60 + Math.random() * 35}%`;
    wrapper.appendChild(bar);
  }
  el.appendChild(wrapper);
}

function hideSkeleton(target) {
  const el = typeof target === "string" ? document.getElementById(target) : target;
  if (!el) return;
  const skeletons = el.querySelectorAll(".skeleton-row");
  skeletons.forEach((s) => s.remove());
}

/* ─── Sparkline ─── */

function renderSparkline(containerId, data, color = "#7c3aed") {
  const container = document.getElementById(containerId);
  if (!container || !Array.isArray(data) || data.length < 2) return;

  const w = container.clientWidth || 200;
  const h = 36;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const stepX = w / (data.length - 1);

  const points = data.map((v, i) => `${i * stepX},${h - ((v - min) / range) * (h - 4) - 2}`).join(" ");

  container.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <polyline fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
        points="${points}" opacity="0.8" />
      <polyline fill="none" stroke="${color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"
        points="${points}" opacity="0.12" />
      <linearGradient id="grad-${containerId}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${color}" stop-opacity="0.15" />
        <stop offset="100%" stop-color="${color}" stop-opacity="0" />
      </linearGradient>
      <polygon fill="url(#grad-${containerId})" points="0,${h} ${points} ${w},${h}" />
    </svg>
  `;
}

/* ─── Page Detection ─── */

function isDashboardPage() {
  return window.location.pathname === "/ui" || window.location.pathname === "/ui/";
}
function isAlertsPage() { return window.location.pathname.endsWith("/alerts"); }
function isEventsPage() { return window.location.pathname.endsWith("/events"); }
function isEndpointsPage() { return window.location.pathname.endsWith("/endpoints"); }
function isScansPage() { return window.location.pathname.endsWith("/scans"); }
function isAdminPage() { return window.location.pathname.includes("/admin/users"); }
function isSettingsPage() { return window.location.pathname.endsWith("/settings"); }

function getCurrentResource() {
  if (isAlertsPage()) return "alerts";
  if (isEventsPage()) return "events";
  if (isEndpointsPage()) return "telemetry/endpoints";
  return null;
}

/* ─── Generic Table ─── */

function renderTable(items) {
  const table = document.getElementById("results");
  if (!table) return;

  const wrapper = table.closest(".table-wrap");
  const area = wrapper || table.parentElement;
  hideSkeleton(area);
  table.replaceChildren();

  if (!Array.isArray(items) || items.length === 0) {
    updateResultCount(0);
    updatePaginationUi(1, 1);
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.textContent = "Aucune donn\u00E9e pour le moment";
    emptyCell.className = "empty-state";
    emptyCell.colSpan = Math.max(uiColumns.length, 4);
    emptyRow.appendChild(emptyCell);
    table.appendChild(emptyRow);
    return;
  }

  const columns = isAlertsPage()
    ? ["severity", "title", "endpoint_id", "status", "created_at"]
    : Object.keys(items[0]);

  const labels = isAlertsPage()
    ? { severity: "Sévérité", title: "Titre", endpoint_id: "Source", status: "Statut", created_at: "Date" }
    : {};

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = labels[column] || column;
    headerRow.appendChild(th);
  }
  if (isAlertsPage()) {
    const th = document.createElement("th");
    th.textContent = "Actions";
    headerRow.appendChild(th);
  }
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const item of items) {
    const row = document.createElement("tr");
    for (const column of columns) {
      const cell = document.createElement("td");
      const value = item?.[column] ?? "";
      if (isAlertsPage() && column === "created_at") {
        const date = new Date(value);
        cell.textContent = isNaN(date.getTime()) ? value : date.toLocaleString("fr-FR");
      } else {
        appendCellValue(cell, column, value);
      }
      row.appendChild(cell);
    }
    if (isAlertsPage()) {
      const cell = document.createElement("td");
      renderAlertActions(cell, item);
      row.appendChild(cell);
    }
    tbody.appendChild(row);
  }
  table.appendChild(tbody);
}

function appendCellValue(cell, column, value) {
  const colLower = column.toLowerCase();
  const isSeverity = colLower.includes("severity");
  const isStatus = colLower.includes("status");

  if (typeof value === "string" && (isSeverity || isStatus)) {
    const badge = document.createElement("span");
    const slug = value.toLowerCase();
    badge.className = `badge badge-${slug}`;
    if (slug === "critical" || slug === "new") badge.classList.add("pulse");
    badge.textContent = value;
    cell.appendChild(badge);
    return;
  }

  if (typeof value === "object" && value !== null) {
    cell.textContent = JSON.stringify(value);
    return;
  }

  cell.textContent = String(value);
}

function renderAlertActions(cell, alert) {
  const actions = document.createElement("div");
  actions.className = "alert-actions";

  if (alert.status === "new") {
    const ackBtn = document.createElement("button");
    ackBtn.className = "btn btn-ghost";
    ackBtn.textContent = "Ack";
    ackBtn.addEventListener("click", () => acknowledgeAlert(alert.alert_id));
    actions.appendChild(ackBtn);
  }
  if (alert.status === "acknowledged" || alert.status === "new") {
    const resBtn = document.createElement("button");
    resBtn.className = "btn btn-ghost";
    resBtn.textContent = "Resolve";
    resBtn.addEventListener("click", () => resolveAlert(alert.alert_id));
    actions.appendChild(resBtn);
  }

  cell.appendChild(actions);
}

async function acknowledgeAlert(id) {
  try {
    const resp = await fetch(`/alerts/${id}/acknowledge`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (resp.ok) {
      showToast("Alerte acquitt\u00E9e", "success");
      loadProtectedData();
    } else {
      showToast("Action non autoris\u00E9e", "error");
    }
  } catch {
    showToast("Erreur r\u00E9seau", "error");
  }
}

async function resolveAlert(id) {
  try {
    const resp = await fetch(`/alerts/${id}/resolve`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (resp.ok) {
      showToast("Alerte r\u00E9solue", "success");
      loadProtectedData();
    } else {
      showToast("Action non autoris\u00E9e", "error");
    }
  } catch {
    showToast("Erreur r\u00E9seau", "error");
  }
}

function applyAlertsFilter(items) {
  if (!Array.isArray(items)) return [];
  const select = document.getElementById("alert-status-filter");
  const selected = select?.value ?? "all";
  if (selected === "all") return items;
  return items.filter((item) => item?.status === selected);
}

/* ─── Data Loading ─── */

async function loadProtectedData() {
  if (!authToken) {
    showToast("Connectez-vous d'abord", "info");
    openLoginModal();
    return;
  }

  const resource = getCurrentResource();
  if (!resource) return;

  const table = document.getElementById("results");
  if (table) showSkeleton(table);

  try {
    const response = await fetch(`/${resource}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (response.status === 401) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      updateUserUI(null);
      showToast("Session expir\u00E9e, reconnectez-vous", "error");
      openLoginModal();
      return;
    }
    if (!response.ok) {
      showToast(`Erreur API (${response.status})`, "error");
      return;
    }
    let data = await response.json();
    if (isAlertsPage()) data = applyAlertsFilter(data);
    latestItems = Array.isArray(data) ? data : [];
    setupSortOptions(latestItems);
    applyLocalTableStateAndRender();
  } catch {
    showToast("Erreur r\u00E9seau", "error");
  }
}

function setupSortOptions(items) {
  const sortSelect = document.getElementById("sort-column");
  if (!sortSelect) return;
  const first = Array.isArray(items) && items.length > 0 ? items[0] : null;
  const allColumns = first ? Object.keys(first) : [];
  const columns = isAlertsPage()
    ? ["severity", "title", "endpoint_id", "status", "created_at"]
    : allColumns;
  uiColumns = allColumns;
  if (!columns.length) { sortSelect.replaceChildren(); tableState.sortColumn = ""; return; }

  const patterns = ["timestamp", "date", "severity", "status"];
  const suggested = isAlertsPage() ? "created_at" : columns.find((c) => patterns.some((p) => c.toLowerCase().includes(p)));
  const prev = tableState.sortColumn;
  const selected = columns.includes(prev) ? prev : suggested ?? columns[0];
  tableState.sortColumn = selected;

  sortSelect.replaceChildren();
  for (const col of columns) {
    const opt = document.createElement("option");
    opt.value = col;
    opt.textContent = col;
    if (col === selected) opt.selected = true;
    sortSelect.appendChild(opt);
  }
}

/* ─── Search, Sort, Paginate ─── */

function normalizeForSearch(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value).toLowerCase();
  return String(value).toLowerCase();
}

function filterItemsBySearch(items) {
  const term = tableState.search.trim().toLowerCase();
  if (!term) return items;
  return items.filter((item) =>
    Object.values(item ?? {}).some((v) => normalizeForSearch(v).includes(term))
  );
}

function compareValues(a, b) {
  const aD = Date.parse(String(a));
  const bD = Date.parse(String(b));
  if (!Number.isNaN(aD) && !Number.isNaN(bD)) return aD - bD;
  const aN = Number(a);
  const bN = Number(b);
  if (!Number.isNaN(aN) && !Number.isNaN(bN)) return aN - bN;
  return String(a).localeCompare(String(b), "fr", { sensitivity: "base" });
}

function sortItems(items) {
  const col = tableState.sortColumn;
  if (!col) return [...items];
  const dir = tableState.sortDirection === "asc" ? 1 : -1;
  return [...items].sort((a, b) => compareValues(a?.[col] ?? "", b?.[col] ?? "") * dir);
}

function paginateItems(items) {
  const ps = tableState.pageSize;
  const tp = Math.max(1, Math.ceil(items.length / ps));
  tableState.page = Math.min(tableState.page, tp);
  tableState.page = Math.max(1, tableState.page);
  const start = (tableState.page - 1) * ps;
  return { items: items.slice(start, start + ps), totalPages: tp, totalResults: items.length };
}

function updateResultCount(count) {
  const el = document.getElementById("results-count");
  if (!el) return;
  el.textContent = `${count} r\u00E9sultat${count > 1 ? "s" : ""}`;
}

function updatePaginationUi(page, totalPages) {
  const ind = document.getElementById("page-indicator");
  if (ind) ind.textContent = `Page ${page} / ${totalPages}`;
  const prev = document.getElementById("prev-page");
  const next = document.getElementById("next-page");
  if (prev) prev.disabled = page <= 1;
  if (next) next.disabled = page >= totalPages;
}

function applyLocalTableStateAndRender() {
  const filtered = filterItemsBySearch(latestItems);
  const sorted = sortItems(filtered);
  const pageData = paginateItems(sorted);
  updateResultCount(pageData.totalResults);
  updatePaginationUi(tableState.page, pageData.totalPages);
  renderTable(pageData.items);
}

function setupTableControls() {
  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      tableState.search = searchInput.value;
      tableState.page = 1;
      applyLocalTableStateAndRender();
    });
  }

  const sortSelect = document.getElementById("sort-column");
  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      tableState.sortColumn = sortSelect.value;
      tableState.page = 1;
      applyLocalTableStateAndRender();
    });
  }

  const dirSelect = document.getElementById("sort-direction");
  if (dirSelect) {
    dirSelect.addEventListener("change", () => {
      tableState.sortDirection = dirSelect.value === "asc" ? "asc" : "desc";
      tableState.page = 1;
      applyLocalTableStateAndRender();
    });
  }

  const pageSizeSelect = document.getElementById("page-size");
  if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", () => {
      const v = Number(pageSizeSelect.value);
      tableState.pageSize = [10, 25, 50].includes(v) ? v : 10;
      tableState.page = 1;
      applyLocalTableStateAndRender();
    });
  }

  const prevBtn = document.getElementById("prev-page");
  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      tableState.page = Math.max(1, tableState.page - 1);
      applyLocalTableStateAndRender();
    });
  }

  const nextBtn = document.getElementById("next-page");
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      tableState.page += 1;
      applyLocalTableStateAndRender();
    });
  }
}

/* ─── Alerts Auto-Refresh ─── */

function setupAlertsAutoRefresh() {
  const checkbox = document.getElementById("alerts-auto-refresh");
  if (!checkbox) return;

  checkbox.addEventListener("change", () => {
    if (alertsPollingIntervalId) {
      window.clearInterval(alertsPollingIntervalId);
      alertsPollingIntervalId = null;
    }
    if (checkbox.checked) {
      alertsPollingIntervalId = window.setInterval(() => loadProtectedData(), 15000);
      showToast("Auto-refresh activ\u00E9 (15s)", "info");
    }
  });

  const filterSelect = document.getElementById("alert-status-filter");
  if (filterSelect) {
    filterSelect.addEventListener("change", () => loadProtectedData());
  }
}

/* ─── Dashboard ─── */

async function fetchKPI() {
  try {
    const resp = await fetch("/reports/kpi", {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (resp.status === 401) throw new Error("unauthorized");
    if (!resp.ok) throw new Error("api-error");
    return resp.json();
  } catch (e) {
    if (e.message === "unauthorized") throw e;
    return null;
  }
}

function setCounter(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = String(value);
}

async function refreshDashboardCounters() {
  if (!authToken) {
    showToast("Connectez-vous d'abord", "info");
    openLoginModal();
    return;
  }

  try {
    const kpi = await fetchKPI();
    if (!kpi) {
      showToast("Impossible de r\u00E9cup\u00E9rer les KPI", "error");
      return;
    }

    const byStatus = kpi.alerts_by_status || {};
    const newAlerts = byStatus.new || 0;
    const ackAlerts = byStatus.acknowledged || 0;
    const totalEvents = kpi.total_events || 0;
    const totalEndpoints = kpi.total_endpoints || 0;
    const totalAlerts = kpi.total_alerts || 0;

    setCounter("count-alerts-new", newAlerts);
    setCounter("count-alerts-ack", ackAlerts);
    setCounter("count-events-total", totalEvents);
    setCounter("count-endpoints-total", totalEndpoints);

    renderCharts(kpi);
    renderSparklines(kpi);
    renderSideCharts(kpi);
    renderSources(kpi);
  } catch (e) {
    if (e.message === "unauthorized") {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      updateUserUI(null);
      showToast("Session expir\u00E9e", "error");
      openLoginModal();
      return;
    }
    showToast("Erreur dashboard", "error");
  }
}

function renderCharts(kpi) {
  renderSessionsChart(kpi);
}

function renderSparklines(kpi) {
  const timeline = kpi.alerts_timeline || kpi.events_timeline;
  if (timeline) {
    renderSparkline("sparkline-alerts", timeline, "#7c3aed");
  }
}

function renderSideCharts(kpi) {
  renderRadarChart("chart-radar", kpi);
  renderGauges(kpi);
}

/* ─── Main Sessions Line Chart ─── */

const WEEK_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

function renderSessionsChart(kpi) {
  const canvas = document.getElementById("chart-sessions");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const data = kpi.events_timeline || kpi.alerts_timeline || [];
  if (data.length < 2) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#9ca3af";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Pas assez de donn\u00E9es", canvas.width / 2, canvas.height / 2);
    return;
  }
  const labels = WEEK_LABELS.slice(0, data.length);
  const maxVal = Math.max(...data, 1);

  const W = canvas.width;
  const H = canvas.height;
  const pad = { top: 30, right: 30, bottom: 40, left: 40 };
  const cw = W - pad.left - pad.right;
  const ch = H - pad.top - pad.bottom;

  ctx.clearRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = "#f0f0f0";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (i * ch) / 4;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(W - pad.right, y);
    ctx.stroke();
    ctx.fillStyle = "#9ca3af";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(Math.round(maxVal - (maxVal * i) / 4).toString(), pad.left - 8, y + 4);
  }

  // Line
  const stepX = cw / (data.length - 1);
  const points = data.map((v, i) => ({
    x: pad.left + i * stepX,
    y: pad.top + ch - (v / maxVal) * ch,
  }));

  // Gradient fill
  const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + ch);
  gradient.addColorStop(0, "rgba(124, 58, 237, 0.12)");
  gradient.addColorStop(1, "rgba(124, 58, 237, 0)");
  ctx.beginPath();
  ctx.moveTo(points[0].x, pad.top + ch);
  points.forEach((p) => ctx.lineTo(p.x, p.y));
  ctx.lineTo(points[points.length - 1].x, pad.top + ch);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Stroke
  ctx.beginPath();
  points.forEach((p, i) => {
    i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y);
  });
  ctx.strokeStyle = "#7c3aed";
  ctx.lineWidth = 2.5;
  ctx.lineJoin = "round";
  ctx.stroke();

  // Dots
  points.forEach((p, i) => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = "#7c3aed";
    ctx.fill();
    ctx.strokeStyle = "white";
    ctx.lineWidth = 2;
    ctx.stroke();
  });

  // Tooltip highlight on highest point
  const maxIdx = data.indexOf(Math.max(...data));
  const tip = points[maxIdx];
  ctx.beginPath();
  ctx.arc(tip.x, tip.y, 6, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(124, 58, 237, 0.15)";
  ctx.fill();

  // Tooltip label
  const tooltipX = tip.x;
  const tooltipY = tip.y - 16;
  ctx.fillStyle = "#7c3aed";
  ctx.font = "bold 11px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(`+${data[maxIdx]}`, tooltipX, tooltipY);

  // X labels
  ctx.fillStyle = "#9ca3af";
  ctx.font = "10px sans-serif";
  ctx.textAlign = "center";
  labels.forEach((label, i) => {
    const x = pad.left + i * stepX;
    ctx.fillText(label, x, H - pad.bottom + 18);
  });

  // Week change
  const weekChangeEl = document.getElementById("chart-week-change");
  if (weekChangeEl && data.length >= 2) {
    const first = data[0];
    const last = data[data.length - 1];
    if (first > 0) {
      const pct = (((last - first) / first) * 100).toFixed(1);
      const sign = pct >= 0 ? "\u25B2" : "\u25BC";
      weekChangeEl.textContent = `${sign} ${Math.abs(pct)}% cette semaine`;
      weekChangeEl.style.color = pct >= 0 ? "var(--success)" : "var(--danger)";
    }
  }
}

/* ─── Radar Chart ─── */

const SEVERITY_LABELS = ["critical", "high", "medium", "low"];
const SEVERITY_NAMES = { critical: "Critique", high: "\u00C9lev\u00E9e", medium: "Moyenne", low: "Faible" };
const SEVERITY_COLORS = { critical: "#ef4444", high: "#f59e0b", medium: "#7c3aed", low: "#10b981" };

function renderRadarChart(canvasId, kpi) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const severity = kpi.alerts_by_severity || {};
  const maxCount = Math.max(...Object.values(severity), 1);
  const labels = SEVERITY_LABELS;
  const dataValues = labels.map((s) => severity[s] || 0);
  const count = labels.length;
  if (count < 3) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#9ca3af";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Pas assez de donn\u00E9es", canvas.width / 2, canvas.height / 2);
    return;
  }

  const W = canvas.width;
  const H = canvas.height;
  const cx = W / 2;
  const cy = H / 2 + 10;
  const radius = Math.min(cx, cy) - 30;
  const levels = 4;

  ctx.clearRect(0, 0, W, H);

  // Grid rings
  for (let l = 1; l <= levels; l++) {
    const r = (radius * l) / levels;
    ctx.beginPath();
    for (let i = 0; i <= count; i++) {
      const angle = (Math.PI * 2 * i) / count - Math.PI / 2;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Axis lines
  for (let i = 0; i < count; i++) {
    const angle = (Math.PI * 2 * i) / count - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
    ctx.strokeStyle = "#e5e7eb";
    ctx.stroke();
  }

  // Data polygon
  ctx.beginPath();
  for (let i = 0; i <= count; i++) {
    const idx = i % count;
    const angle = (Math.PI * 2 * idx) / count - Math.PI / 2;
    const value = dataValues[idx] / maxCount;
    const x = cx + radius * value * Math.cos(angle);
    const y = cy + radius * value * Math.sin(angle);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = "rgba(124, 58, 237, 0.12)";
  ctx.fill();
  ctx.strokeStyle = "#7c3aed";
  ctx.lineWidth = 2;
  ctx.stroke();

  // Labels
  ctx.fillStyle = "#6b7280";
  ctx.font = "10px sans-serif";
  ctx.textAlign = "center";
  labels.forEach((s, i) => {
    const angle = (Math.PI * 2 * i) / count - Math.PI / 2;
    const x = cx + (radius + 18) * Math.cos(angle);
    const y = cy + (radius + 18) * Math.sin(angle);
    ctx.fillText(SEVERITY_NAMES[s] || s, x, y + 3);
  });

  // Value labels on data points
  dataValues.forEach((v, i) => {
    const angle = (Math.PI * 2 * i) / count - Math.PI / 2;
    const value = v / maxCount;
    const x = cx + radius * value * Math.cos(angle);
    const y = cy + radius * value * Math.sin(angle);
    ctx.fillStyle = SEVERITY_COLORS[labels[i]] || "#7c3aed";
    ctx.font = "bold 10px sans-serif";
    ctx.fillText(String(v), x, y - 8);
  });
}

/* ─── Circular Gauges ─── */

function renderGauges(kpi) {
  const byStatus = kpi.alerts_by_status || {};
  const totalAlerts = kpi.total_alerts || 0;
  const totalEvents = kpi.total_events || 0;
  const resolved = byStatus.resolved || 0;
  const ack = byStatus.acknowledged || 0;

  const activity24h = totalEvents > 0 ? Math.round((kpi.events_last_24h || 0) / totalEvents * 100) : 0;
  const handledRate = totalAlerts > 0 ? Math.round(((resolved + ack) / totalAlerts) * 100) : 0;

  renderGauge("gauge-online", activity24h, "Activit\u00E9 24h");
  renderGauge("gauge-resolution", handledRate, "Taux trait.");

  setCounter("stat-resolved", resolved);
  const resolutionRate = totalAlerts > 0 ? Math.round((resolved / totalAlerts) * 100) : 0;
  setCounter("stat-resolution-rate", resolutionRate + "%");
  setCounter("stat-total-alerts", totalAlerts);
}

function renderSources(kpi) {
  const bySeverity = kpi.alerts_by_severity || {};
  const maxCount = Math.max(...Object.values(bySeverity), 1);

  for (const sev of ["critical", "high", "medium"]) {
    const count = bySeverity[sev] || 0;
    setCounter("count-severity-" + sev, count);
    const bar = document.getElementById("bar-severity-" + sev);
    if (bar) {
      bar.style.width = Math.round((count / maxCount) * 100) + "%";
    }
  }

  const legend = document.getElementById("severity-legend");
  if (legend) {
    const items = [
      { key: "critical", label: "Critique", color: "#ef4444" },
      { key: "high", label: "Élevée", color: "#f59e0b" },
      { key: "medium", label: "Moyenne", color: "#7c3aed" },
      { key: "low", label: "Faible", color: "#10b981" },
    ];
    legend.replaceChildren();
    for (const item of items) {
      const count = bySeverity[item.key] || 0;
      const el = document.createElement("div");
      el.className = "severity-legend-item";
      el.innerHTML = `
        <span class="severity-legend-dot" style="background:${item.color}"></span>
        <span class="severity-legend-label">${item.label}</span>
        <span class="severity-legend-count">${count}</span>
      `;
      legend.appendChild(el);
    }
  }
}

function renderGauge(containerId, percent, label) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (percent / 100) * circ;
  const color = percent > 70 ? "#10b981" : percent > 40 ? "#7c3aed" : "#f59e0b";

  container.innerHTML = `
    <svg width="100" height="100" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="${r}" fill="none" stroke="#f0f0f0" stroke-width="6" />
      <circle cx="50" cy="50" r="${r}" fill="none" stroke="${color}" stroke-width="6"
        stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
        stroke-linecap="round" transform="rotate(-90, 50, 50)"
        style="transition: stroke-dashoffset 0.8s ease" />
      <text x="50" y="46" text-anchor="middle" font-size="16" font-weight="700" fill="#1f2937">${percent}%</text>
      <text x="50" y="60" text-anchor="middle" font-size="8" fill="#6b7280">${label}</text>
    </svg>
  `;
}

/* ─── Admin: User Management ─── */

let editingUsername = null;

async function loadAdminUsers() {
  if (!authToken) {
    showToast("Connectez-vous d'abord", "info");
    openLoginModal();
    return;
  }

  const table = document.getElementById("user-results");
  if (!table) return;
  showSkeleton(table);

  try {
    const resp = await fetch("/auth/admin/users", {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (resp.status === 401) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      updateUserUI(null);
      showToast("Session expirée", "error");
      openLoginModal();
      return;
    }
    if (resp.status === 403) {
      showToast("Accès réservé aux administrateurs", "error");
      return;
    }
    if (!resp.ok) { showToast("Erreur API", "error"); return; }

    hideSkeleton(table);
    const users = await resp.json();
    renderUserTable(users);
  } catch {
    showToast("Erreur réseau", "error");
  }
}

function renderUserTable(users) {
  const table = document.getElementById("user-results");
  if (!table) return;
  table.replaceChildren();

  const countText = `${users.length} utilisateur${users.length > 1 ? "s" : ""}`;
  const countEl = document.getElementById("results-count");
  if (countEl) countEl.textContent = countText;
  const userCountEl = document.getElementById("user-count");
  if (userCountEl) userCountEl.textContent = countText;

  if (!users.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.textContent = "Aucun utilisateur";
    cell.className = "empty-state";
    cell.colSpan = 3;
    row.appendChild(cell);
    table.appendChild(row);
    return;
  }

  const thead = document.createElement("thead");
  thead.innerHTML = `<tr><th>Nom d'utilisateur</th><th>Rôle</th><th>Actions</th></tr>`;
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const user of users) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${user.username}</td>
      <td><span class="badge badge-${user.role === "admin" ? "critical" : "info"}">${user.role}</span></td>
      <td><div class="alert-actions"></div></td>
    `;
    const actions = row.querySelector(".alert-actions");

    const editBtn = document.createElement("button");
    editBtn.className = "btn btn-ghost";
    editBtn.textContent = "Modifier";
    editBtn.addEventListener("click", () => openEditUserModal(user));
    actions.appendChild(editBtn);

    if (user.username !== currentUser?.username) {
      const delBtn = document.createElement("button");
      delBtn.className = "btn btn-ghost";
      delBtn.textContent = "Supprimer";
      delBtn.style.color = "var(--danger)";
      delBtn.addEventListener("click", () => deleteUser(user.username));
      actions.appendChild(delBtn);
    }

    tbody.appendChild(row);
  }
  table.appendChild(tbody);
}

function openCreateUserModal() {
  editingUsername = null;
  document.getElementById("user-modal-title").textContent = "Nouvel utilisateur";
  document.getElementById("user-form-username").value = "";
  document.getElementById("user-form-username").disabled = false;
  document.getElementById("user-form-password").value = "";
  document.getElementById("user-form-password").required = true;
  document.getElementById("user-form-role").value = "analyst";
  document.getElementById("user-form-status").textContent = "";
  document.getElementById("user-modal").classList.add("open");
}

function openEditUserModal(user) {
  editingUsername = user.username;
  document.getElementById("user-modal-title").textContent = "Modifier : " + user.username;
  document.getElementById("user-form-username").value = user.username;
  document.getElementById("user-form-username").disabled = true;
  document.getElementById("user-form-password").value = "";
  document.getElementById("user-form-password").required = false;
  document.getElementById("user-form-role").value = user.role;
  document.getElementById("user-form-status").textContent = "Laissez le mot de passe vide pour ne pas le changer";
  document.getElementById("user-modal").classList.add("open");
}

function closeUserModal() {
  document.getElementById("user-modal").classList.remove("open");
  editingUsername = null;
}

async function handleUserFormSubmit(event) {
  event.preventDefault();
  if (!authToken) { openLoginModal(); return; }

  const username = document.getElementById("user-form-username").value.trim();
  const password = document.getElementById("user-form-password").value;
  const role = document.getElementById("user-form-role").value;
  const statusEl = document.getElementById("user-form-status");
  statusEl.textContent = "En cours...";

  try {
    if (editingUsername) {
      const body = { role };
      if (password) body.password = password;
      const resp = await fetch(`/auth/admin/users/${editingUsername}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${authToken}` },
        body: JSON.stringify(body),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        statusEl.textContent = err.detail || "Erreur modification";
        return;
      }
      showToast("Utilisateur modifié", "success");
    } else {
      const resp = await fetch("/auth/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ username, password, role }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        statusEl.textContent = err.detail || "Erreur création";
        return;
      }
      showToast("Utilisateur créé", "success");
    }
    closeUserModal();
    loadAdminUsers();
  } catch {
    showToast("Erreur réseau", "error");
  }
}

async function deleteUser(username) {
  if (!confirm(`Supprimer l'utilisateur "${username}" ?`)) return;
  try {
    const resp = await fetch(`/auth/admin/users/${username}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      showToast(err.detail || "Erreur suppression", "error");
      return;
    }
    showToast(`Utilisateur "${username}" supprimé`, "success");
    loadAdminUsers();
  } catch {
    showToast("Erreur réseau", "error");
  }
}

/* ─── Scan Submission ─── */

async function submitSimulatedScan(event) {
  event.preventDefault();
  if (!authToken) {
    showToast("Connectez-vous d'abord", "info");
    openLoginModal();
    return;
  }

  const endpointId = document.getElementById("scan-endpoint-id")?.value ?? "";
  const rawTarget = document.getElementById("scan-target")?.value ?? "";
  const scanType = document.getElementById("scan-type")?.value ?? "ping";
  const severity = document.getElementById("scan-severity")?.value ?? "low";
  const resultNode = document.getElementById("scan-result");

  const TYPE_MAP = { ping: "scan_ping", port: "scan_port", service: "scan_service" };
  const eventType = TYPE_MAP[scanType];
  if (!eventType) { showToast("Type de scan invalide", "error"); return; }

  const target = rawTarget.trim().slice(0, 128);
  const payload = {
    endpoint_id: endpointId,
    event_type: eventType,
    severity,
    source: "ui-scan-tool",
    description: `UI simulated ${scanType} scan on ${target}`,
    details: { target, simulated: true },
  };

  try {
    const response = await fetch("/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify(payload),
    });
    if (response.status === 401) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      updateUserUI(null);
      showToast("Session expir\u00E9e", "error");
      openLoginModal();
      return;
    }
    if (!response.ok) {
      showToast("Erreur cr\u00E9ation scan", "error");
      if (resultNode) resultNode.textContent = "Erreur cr\u00E9ation de l'\u00E9v\u00E9nement de scan.";
      return;
    }
    const created = await response.json();
    if (resultNode) resultNode.textContent = JSON.stringify(created, null, 2);
    showToast("Scan simul\u00E9 envoy\u00E9", "success");
  } catch {
    showToast("Erreur r\u00E9seau", "error");
  }
}

/* ─── Endpoint Cards ─── */

async function loadEndpoints() {
  if (!authToken) {
    showToast("Connectez-vous d'abord", "info");
    openLoginModal();
    return;
  }

  const grid = document.getElementById("endpoint-grid");
  if (!grid) return;
  showSkeleton(grid);

  try {
    const resp = await fetch("/telemetry/endpoints", {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (resp.status === 401) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      updateUserUI(null);
      showToast("Session expir\u00E9e", "error");
      openLoginModal();
      return;
    }
    if (!resp.ok) { showToast("Erreur API", "error"); return; }

    hideSkeleton(grid);
    const data = await resp.json();
    const endpoints = Array.isArray(data) ? data : [];

    grid.replaceChildren();
    if (endpoints.length === 0) {
      grid.innerHTML = '<div class="glass" style="padding:40px;text-align:center;color:var(--text-muted)">Aucun endpoint enregistr\u00E9</div>';
      return;
    }

    for (const ep of endpoints) {
      const card = document.createElement("div");
      card.className = "glass endpoint-card";
      const alive = ep.status === "alive";
      card.innerHTML = `
        <div class="endpoint-status">
          <span style="color:${alive ? 'var(--success)' : 'var(--text-muted)'}">${alive ? '\u25CF' : '\u25CB'}</span>
          ${alive ? 'Alive' : 'Dead'}
        </div>
        <h3>${ep.hostname || ep.endpoint_id}</h3>
        <p class="endpoint-meta">${ep.ip_address || '\u2014'} \u00B7 ${ep.os_info || '\u2014'}</p>
        <dl class="endpoint-stats">
          <dt>ID</dt>
          <dd>${ep.endpoint_id || '\u2014'}</dd>
          <dt>Agent</dt>
          <dd>${ep.agent_version || '\u2014'}</dd>
          <dt>Heartbeat</dt>
          <dd>${ep.last_seen ? new Date(ep.last_seen).toLocaleString('fr-FR') : '\u2014'}</dd>
          <dt>OS</dt>
          <dd>${ep.os_info || '\u2014'}</dd>
        </dl>
      `;
      grid.appendChild(card);
    }
  } catch {
    showToast("Erreur r\u00E9seau", "error");
  }
}

/* ─── Page Content Refresh ─── */

function refreshPageContent() {
  if (isDashboardPage() && authToken) refreshDashboardCounters();
  if (isAlertsPage() && authToken) loadProtectedData();
  if (isEventsPage() && authToken) loadProtectedData();
  if (isEndpointsPage() && authToken) loadEndpoints();
  if (isAdminPage() && authToken) loadAdminUsers();
  if (isSettingsPage() && authToken) refreshSettingsPage();
}

/* ─── Settings Page ─── */

async function refreshSettingsPage() {
  if (!authToken) {
    showToast("Connectez-vous d'abord", "info");
    openLoginModal();
    return;
  }

  const meResp = await fetch("/auth/me", {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  if (!meResp.ok) return;
  const me = await meResp.json();

  const usernameEl = document.getElementById("profile-username");
  const roleBadge = document.getElementById("profile-role-badge");
  const avatarEl = document.getElementById("profile-avatar");
  const sessionEl = document.getElementById("profile-session");

  if (usernameEl) usernameEl.textContent = me.username;
  if (roleBadge) {
    roleBadge.className = `badge badge-${me.role === "admin" ? "critical" : "info"}`;
    roleBadge.textContent = me.role === "admin" ? "Administrateur" : "Analyste";
  }
  if (avatarEl) avatarEl.textContent = me.username?.charAt(0).toUpperCase() || "?";
  if (sessionEl) {
    const token = authToken;
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const exp = payload.exp ? new Date(payload.exp * 1000).toLocaleString("fr-FR") : "—";
        sessionEl.textContent = `Expire le ${exp}`;
      } catch {
        sessionEl.textContent = "Session active";
      }
    }
  }

  const adminSection = document.getElementById("admin-section");
  const adminSectionTable = document.getElementById("admin-section-table");
  if (me.role === "admin") {
    if (adminSection) adminSection.style.display = "";
    if (adminSectionTable) adminSectionTable.style.display = "";
    loadAdminUsers();
  }
}

/* ─── Init ─── */

window.addEventListener("DOMContentLoaded", async () => {
  initSidebar();

  const loginModal = document.getElementById("login-modal");
  const loginForm = document.getElementById("modal-login-form");
  if (loginForm) loginForm.addEventListener("submit", handleLogin);

  const loginBtn = document.getElementById("btn-login");
  if (loginBtn) loginBtn.addEventListener("click", openLoginModal);

  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) logoutBtn.addEventListener("click", handleLogout);

  if (loginModal) {
    loginModal.addEventListener("click", (e) => {
      if (e.target === loginModal) closeLoginModal();
    });
  }

  if (authToken) {
    try {
      const meResp = await fetch("/auth/me", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (meResp.ok) {
        const me = await meResp.json();
        updateUserUI(me);
      } else {
        sessionStorage.removeItem("omninet_token");
        authToken = null;
      }
    } catch {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
    }
  }
  updateUserUI(currentUser);

  setupTableControls();

  if (isAlertsPage()) setupAlertsAutoRefresh();

  if (isDashboardPage()) {
    const refreshBtn = document.getElementById("refresh-dashboard");
    if (refreshBtn) refreshBtn.addEventListener("click", refreshDashboardCounters);
    if (authToken) {
      refreshDashboardCounters();
      window.setInterval(() => {
        if (authToken) refreshDashboardCounters();
      }, 30000);
    }
  }

  const scanForm = document.getElementById("scan-form");
  if (scanForm && isScansPage()) scanForm.addEventListener("submit", submitSimulatedScan);

  const loadEndpointsBtn = document.getElementById("load-endpoints");
  if (loadEndpointsBtn && isEndpointsPage()) loadEndpointsBtn.addEventListener("click", loadEndpoints);

  const loadBtn = document.getElementById("load-data");
  if (loadBtn) loadBtn.addEventListener("click", loadProtectedData);

  const isAdminOrSettings = () => isAdminPage() || isSettingsPage();

  const loadUsersBtn = document.getElementById("load-users");
  if (loadUsersBtn && isAdminOrSettings()) loadUsersBtn.addEventListener("click", loadAdminUsers);

  const createUserBtn = document.getElementById("btn-create-user");
  if (createUserBtn && isAdminOrSettings()) createUserBtn.addEventListener("click", openCreateUserModal);

  const userForm = document.getElementById("user-form");
  if (userForm && isAdminOrSettings()) userForm.addEventListener("submit", handleUserFormSubmit);

  const userModal = document.getElementById("user-modal");
  if (userModal) {
    userModal.addEventListener("click", (e) => {
      if (e.target === userModal) closeUserModal();
    });
  }

  const userSearch = document.getElementById("user-search");
  if (userSearch && isAdminOrSettings()) {
    userSearch.addEventListener("input", () => {
      const table = document.getElementById("user-results");
      if (!table) return;
      const term = userSearch.value.toLowerCase();
      Array.from(table.querySelectorAll("tbody tr")).forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(term) ? "" : "none";
      });
    });
  }

  refreshPageContent();
});
