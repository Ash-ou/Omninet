let authToken = sessionStorage.getItem("omninet_token") || null;
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

function setStatus(message, isError = false) {
  const status = document.getElementById("status");
  if (!status) {
    return;
  }
  status.textContent = message;
  status.classList.toggle("error", isError);
}

function setLoading(isLoading) {
  const node = document.getElementById("loading-indicator");
  if (!node) {
    return;
  }
  node.classList.toggle("hidden", !isLoading);
}

function initActiveNav() {
  const page = document.body.dataset.page;
  if (!page) {
    return;
  }
  const navLinks = document.querySelectorAll("[data-nav]");
  for (const link of navLinks) {
    if (link.dataset.nav === page) {
      link.classList.add("active");
    }
  }
}

async function login(event) {
  event.preventDefault();

  const username = document.getElementById("username")?.value ?? "";
  const password = document.getElementById("password")?.value ?? "";

  setLoading(true);
  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (response.status === 401) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      setStatus("Erreur 401: identifiants invalides", true);
      return;
    }

    if (!response.ok) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      setStatus(`Erreur: login impossible (${response.status})`, true);
      return;
    }

    const data = await response.json();
    authToken = data.access_token;
    sessionStorage.setItem("omninet_token", authToken);
    setStatus("Connecté. Token conservé en mémoire de la page.");
  } catch (_error) {
    sessionStorage.removeItem("omninet_token");
    authToken = null;
    setStatus("Erreur réseau pendant le login", true);
  } finally {
    setLoading(false);
  }
}

function getCurrentResource() {
  if (window.location.pathname.endsWith("/alerts")) {
    return "alerts";
  }
  if (window.location.pathname.endsWith("/events")) {
    return "events";
  }
  if (window.location.pathname.endsWith("/endpoints")) {
    return "telemetry/endpoints";
  }
  return null;
}

function isAlertsPage() {
  return window.location.pathname.endsWith("/alerts");
}

function isDashboardPage() {
  return window.location.pathname === "/ui" || window.location.pathname === "/ui/";
}

function isScansPage() {
  return window.location.pathname.endsWith("/scans");
}

function renderTable(items) {
  const table = document.getElementById("results");
  if (!table) {
    return;
  }

  table.replaceChildren();

  if (!Array.isArray(items) || items.length === 0) {
    updateResultCount(0);
    updatePaginationUi(1, 1);
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.textContent = "Aucune donnée disponible pour le moment.";
    emptyCell.classList.add("empty-state");
    emptyCell.colSpan = 1;
    emptyRow.appendChild(emptyCell);
    table.appendChild(emptyRow);
    return;
  }

  const columns = Object.keys(items[0]);

  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const headerCell = document.createElement("th");
    headerCell.textContent = column;
    headerRow.appendChild(headerCell);
  }
  table.appendChild(headerRow);

  for (const item of items) {
    const row = document.createElement("tr");
    for (const column of columns) {
      const cell = document.createElement("td");
      const value = item?.[column] ?? "";
      appendCellValue(cell, column, value);
      row.appendChild(cell);
    }
    table.appendChild(row);
  }
}

function appendCellValue(cell, column, value) {
  const isSeverityColumn = column.toLowerCase().includes("severity");
  const isStatusColumn = column.toLowerCase().includes("status");

  if (typeof value === "string" && (isSeverityColumn || isStatusColumn)) {
    const badge = document.createElement("span");
    badge.classList.add("badge");
    const slug = value.toLowerCase();
    badge.classList.add(
      isSeverityColumn ? `badge-severity-${slug}` : `badge-status-${slug}`,
    );
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

async function loadProtectedData() {
  if (!authToken) {
    setStatus("Connectez-vous d'abord.", true);
    return;
  }

  const resource = getCurrentResource();
  if (!resource) {
    setStatus("Cette page ne charge pas de ressource API.");
    return;
  }

  setLoading(true);
  try {
    const response = await fetch(`/${resource}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    if (response.status === 401) {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      setStatus("Erreur 401: token invalide ou expiré", true);
      return;
    }

    if (!response.ok) {
      setStatus(`Erreur API (${response.status})`, true);
      return;
    }

    let data = await response.json();
    if (isAlertsPage()) {
      data = applyAlertsFilter(data);
    }
    latestItems = Array.isArray(data) ? data : [];
    setupSortOptions(latestItems);
    applyLocalTableStateAndRender();
    setStatus("Données chargées.");
  } catch (_error) {
    setStatus("Erreur réseau lors du chargement", true);
  } finally {
    setLoading(false);
  }
}

function setupSortOptions(items) {
  const sortSelect = document.getElementById("sort-column");
  if (!sortSelect) {
    return;
  }

  const firstItem = Array.isArray(items) && items.length > 0 ? items[0] : null;
  const columns = firstItem ? Object.keys(firstItem) : [];
  uiColumns = columns;

  if (columns.length === 0) {
    sortSelect.replaceChildren();
    tableState.sortColumn = "";
    return;
  }

  const priorityPatterns = ["timestamp", "date", "severity", "status"];
  const suggested = columns.find((column) =>
    priorityPatterns.some((pattern) => column.toLowerCase().includes(pattern)),
  );

  const previous = tableState.sortColumn;
  const selected = columns.includes(previous) ? previous : suggested ?? columns[0];
  tableState.sortColumn = selected;

  sortSelect.replaceChildren();
  for (const column of columns) {
    const option = document.createElement("option");
    option.value = column;
    option.textContent = column;
    if (column === selected) {
      option.selected = true;
    }
    sortSelect.appendChild(option);
  }
}

function normalizeForSearch(value) {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "object") {
    return JSON.stringify(value).toLowerCase();
  }
  return String(value).toLowerCase();
}

function filterItemsBySearch(items) {
  const term = tableState.search.trim().toLowerCase();
  if (!term) {
    return items;
  }

  return items.filter((item) => {
    for (const value of Object.values(item ?? {})) {
      if (normalizeForSearch(value).includes(term)) {
        return true;
      }
    }
    return false;
  });
}

function compareValues(left, right) {
  const leftDate = Date.parse(String(left));
  const rightDate = Date.parse(String(right));
  if (!Number.isNaN(leftDate) && !Number.isNaN(rightDate)) {
    return leftDate - rightDate;
  }

  const leftNumber = Number(left);
  const rightNumber = Number(right);
  if (!Number.isNaN(leftNumber) && !Number.isNaN(rightNumber)) {
    return leftNumber - rightNumber;
  }

  return String(left).localeCompare(String(right), "fr", { sensitivity: "base" });
}

function sortItems(items) {
  const column = tableState.sortColumn;
  if (!column) {
    return [...items];
  }

  const direction = tableState.sortDirection === "asc" ? 1 : -1;
  return [...items].sort((a, b) => {
    const left = a?.[column] ?? "";
    const right = b?.[column] ?? "";
    return compareValues(left, right) * direction;
  });
}

function paginateItems(items) {
  const pageSize = tableState.pageSize;
  const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
  tableState.page = Math.min(tableState.page, totalPages);
  tableState.page = Math.max(1, tableState.page);

  const startIndex = (tableState.page - 1) * pageSize;
  return {
    items: items.slice(startIndex, startIndex + pageSize),
    totalPages,
    totalResults: items.length,
  };
}

function updateResultCount(totalResults) {
  const node = document.getElementById("results-count");
  if (!node) {
    return;
  }
  const suffix = totalResults > 1 ? "résultats" : "résultat";
  node.textContent = `${totalResults} ${suffix}`;
}

function updatePaginationUi(page, totalPages) {
  const indicator = document.getElementById("page-indicator");
  if (indicator) {
    indicator.textContent = `Page ${page} / ${totalPages}`;
  }

  const prevButton = document.getElementById("prev-page");
  const nextButton = document.getElementById("next-page");
  if (prevButton) {
    prevButton.disabled = page <= 1;
  }
  if (nextButton) {
    nextButton.disabled = page >= totalPages;
  }
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

  const directionSelect = document.getElementById("sort-direction");
  if (directionSelect) {
    directionSelect.addEventListener("change", () => {
      tableState.sortDirection = directionSelect.value === "asc" ? "asc" : "desc";
      tableState.page = 1;
      applyLocalTableStateAndRender();
    });
  }

  const pageSizeSelect = document.getElementById("page-size");
  if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", () => {
      const parsed = Number(pageSizeSelect.value);
      tableState.pageSize = [10, 25, 50].includes(parsed) ? parsed : 10;
      tableState.page = 1;
      applyLocalTableStateAndRender();
    });
  }

  const prevButton = document.getElementById("prev-page");
  if (prevButton) {
    prevButton.addEventListener("click", () => {
      tableState.page = Math.max(1, tableState.page - 1);
      applyLocalTableStateAndRender();
    });
  }

  const nextButton = document.getElementById("next-page");
  if (nextButton) {
    nextButton.addEventListener("click", () => {
      tableState.page += 1;
      applyLocalTableStateAndRender();
    });
  }
}

function applyAlertsFilter(items) {
  if (!Array.isArray(items)) {
    return [];
  }

  const select = document.getElementById("alert-status-filter");
  const selected = select?.value ?? "all";
  if (selected === "all") {
    return items;
  }

  return items.filter((item) => item?.status === selected);
}

function setupAlertsAutoRefresh() {
  const checkbox = document.getElementById("alerts-auto-refresh");
  const select = document.getElementById("alert-status-filter");
  if (!checkbox) {
    return;
  }

  checkbox.addEventListener("change", () => {
    if (alertsPollingIntervalId) {
      window.clearInterval(alertsPollingIntervalId);
      alertsPollingIntervalId = null;
    }

    if (checkbox.checked) {
      alertsPollingIntervalId = window.setInterval(() => {
        loadProtectedData();
      }, 15000);
      setStatus("Auto-refresh alertes activé (15s).");
    } else {
      setStatus("Auto-refresh alertes désactivé.");
    }
  });

  if (select) {
    select.addEventListener("change", () => {
      loadProtectedData();
    });
  }
}

async function fetchProtectedList(resource) {
  const response = await fetch(`/${resource}`, {
    headers: { Authorization: `Bearer ${authToken}` },
  });

  if (response.status === 401) {
    sessionStorage.removeItem("omninet_token");
    authToken = null;
    throw new Error("unauthorized");
  }
  if (!response.ok) {
    throw new Error(`api-${response.status}`);
  }
  return response.json();
}

function setCounter(id, value) {
  const node = document.getElementById(id);
  if (!node) {
    return;
  }
  node.textContent = String(value);
}

async function refreshDashboardCounters() {
  if (!authToken) {
    setStatus("Connectez-vous d'abord.", true);
    return;
  }

  setLoading(true);
  try {
    const kpiData = await fetchKPI();
    if (!kpiData) {
      setStatus("Erreur: impossible de récupérer les KPI", true);
      return;
    }

    // Utilisation uniquement des données KPI (évite les fetchs redondants)
    const alertsByStatus = kpiData.alerts_by_status || {};
    setCounter("count-alerts-new", alertsByStatus.new || 0);
    setCounter("count-alerts-ack", alertsByStatus.acknowledged || 0);
    setCounter("count-events-total", kpiData.total_events || 0);
    setCounter("count-endpoints-total", kpiData.total_endpoints || 0);
    setCounter("count-scans-total", kpiData.total_scans || 0);
    setCounter("count-events-24h", kpiData.events_last_24h || 0);

    renderCharts(kpiData);

    setStatus("Compteurs mis à jour via KPI.");
  } catch (error) {
    if (error instanceof Error && error.message === "unauthorized") {
      sessionStorage.removeItem("omninet_token");
      authToken = null;
      setStatus("Erreur 401: token invalide ou expiré", true);
      return;
    }
    setStatus("Erreur pendant le refresh dashboard", true);
  } finally {
    setLoading(false);
  }
}

async function fetchKPI() {
  try {
    const response = await fetch("/reports/kpi", {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    if (response.status === 401) {
      throw new Error("unauthorized");
    }
    if (!response.ok) {
      throw new Error(`api-${response.status}`);
    }
    return response.json();
  } catch (error) {
    if (error instanceof Error && error.message === "unauthorized") {
      throw error;
    }
    setStatus("Erreur lors de la récupération des KPI", true);
    return null;
  }
}

function renderCharts(kpiData) {
  if (!kpiData) {
    return;
  }

  // Graphe en barres : alertes par sévérité
  const severityCanvas = document.getElementById("chart-alerts-severity");
  if (severityCanvas) {
    renderBarChart(severityCanvas, kpiData.alerts_by_severity, "Sévérité");
  }

  // Graphe camembert : alertes par statut
  const statusCanvas = document.getElementById("chart-alerts-status");
  if (statusCanvas) {
    renderPieChart(statusCanvas, kpiData.alerts_by_status, "Statut");
  }
}

function renderBarChart(canvas, data, labelKey) {
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }

  const keys = Object.keys(data);
  const values = Object.values(data);
  const maxValue = Math.max(...values, 1);

  const chartWidth = canvas.width - 60;
  const chartHeight = canvas.height - 60;
  const barWidth = Math.min(50, (chartWidth / keys.length) - 10);
  const barSpacing = (chartWidth - (barWidth * keys.length)) / (keys.length + 1);

  // Effacer le canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Couleurs selon la sévérité (palette cohérente thème sombre)
  const severityColors = {
    critical: "#ef4444",
    high: "#f97316",
    medium: "#eab308",
    low: "#22c55e",
    info: "#3b82f6",
  };

  // Dessiner les barres
  keys.forEach((key, index) => {
    const barHeight = (values[index] / maxValue) * chartHeight;
    const x = barSpacing + index * (barWidth + barSpacing);
    const y = canvas.height - 40 - barHeight;

    // Couleur avec gradient
    const color = severityColors[key.toLowerCase()] || "#6b7280";
    ctx.fillStyle = color;
    ctx.fillRect(x, y, barWidth, barHeight);

    // Effet de brillance en haut de la barre
    const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
    gradient.addColorStop(0, "rgba(255,255,255,0.2)");
    gradient.addColorStop(1, "rgba(0,0,0,0.1)");
    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, barWidth, barHeight);

    // Valeur au-dessus de la barre
    ctx.fillStyle = "#d1d5db";
    ctx.font = "bold 12px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(values[index].toString(), x + barWidth / 2, y - 8);

    // Étiquette en dessous (axe X)
    ctx.fillStyle = "#9ca3af";
    ctx.font = "11px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(key, x + barWidth / 2, canvas.height - 20);
  });

  // Axe Y (lignes de référence)
  ctx.strokeStyle = "#374151";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = canvas.height - 40 - (i * chartHeight / 4);
    ctx.beginPath();
    ctx.moveTo(30, y);
    ctx.lineTo(canvas.width - 20, y);
    ctx.stroke();

    // Valeur de référence
    ctx.fillStyle = "#9ca3af";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText(Math.round((maxValue * i) / 4).toString(), 25, y + 4);
  }

  // Label axe Y
  ctx.save();
  ctx.fillStyle = "#9ca3af";
  ctx.font = "10px sans-serif";
  ctx.textAlign = "center";
  ctx.translate(10, canvas.height / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("Nombre d'alertes", 0, 0);
  ctx.restore();

  // Label axe X
  ctx.fillStyle = "#9ca3af";
  ctx.font = "11px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(labelKey, canvas.width / 2, canvas.height - 5);
}

function renderPieChart(canvas, data, labelKey) {
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }

  const keys = Object.keys(data);
  const values = Object.values(data);
  const total = values.reduce((sum, val) => sum + val, 0);

  if (total === 0) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#9ca3af";
    ctx.font = "14px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Aucune donnée", canvas.width / 2, canvas.height / 2);
    return;
  }

  const centerX = canvas.width * 0.35;
  const centerY = canvas.height / 2;
  const radius = Math.min(centerX, centerY) - 20;

  // Effacer le canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Couleurs pour les statuts (palette cohérente thème sombre)
  const statusColors = {
    new: "#3b82f6",
    acknowledged: "#a855f7",
    resolved: "#10b981",
  };

  // Dessiner le camembert
  let startAngle = -Math.PI / 2;
  keys.forEach((key, index) => {
    const sliceAngle = (values[index] / total) * 2 * Math.PI;
    const endAngle = startAngle + sliceAngle;

    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, radius, startAngle, endAngle);
    ctx.closePath();

    const color = statusColors[key.toLowerCase()] || "#6b7280";
    ctx.fillStyle = color;
    ctx.fill();

    // Bordure plus foncée
    ctx.strokeStyle = "rgba(0,0,0,0.2)";
    ctx.lineWidth = 2;
    ctx.stroke();

    startAngle = endAngle;
  });

  // Légende à droite du camembert
  const legendX = canvas.width * 0.65;
  const legendStartY = centerY - (keys.length * 25) / 2;
  ctx.textAlign = "left";

  keys.forEach((key, index) => {
    const legendY = legendStartY + index * 25;
    const percentage = ((values[index] / total) * 100).toFixed(1);

    // Carré de couleur
    const color = statusColors[key.toLowerCase()] || "#6b7280";
    ctx.fillStyle = color;
    ctx.fillRect(legendX, legendY - 8, 16, 16);

    // Texte de légende avec pourcentage
    ctx.fillStyle = "#d1d5db";
    ctx.font = "12px sans-serif";
    ctx.fillText(`${key} (${percentage}%)`, legendX + 24, legendY + 4);

    // Valeur numérique
    ctx.fillStyle = "#9ca3af";
    ctx.font = "10px sans-serif";
    ctx.fillText(`${values[index]} alertes`, legendX + 24, legendY + 16);
  });

  // Total au centre du camembert
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 18px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(total.toString(), centerX, centerY + 6);
  ctx.fillStyle = "#9ca3af";
  ctx.font = "10px sans-serif";
  ctx.fillText("Total", centerX, centerY + 20);
}

async function submitSimulatedScan(event) {
  event.preventDefault();
  if (!authToken) {
    setStatus("Connectez-vous d'abord.", true);
    return;
  }

  const endpointId = document.getElementById("scan-endpoint-id")?.value ?? "";
  const rawTarget = document.getElementById("scan-target")?.value ?? "";
  const scanType = document.getElementById("scan-type")?.value ?? "ping";
  const severity = document.getElementById("scan-severity")?.value ?? "low";
  const resultNode = document.getElementById("scan-result");

  const SCAN_EVENT_TYPE_MAP = {
    ping: "scan_ping",
    port: "scan_port",
    service: "scan_service",
  };

  const eventType = SCAN_EVENT_TYPE_MAP[scanType];
  if (!eventType) {
    setStatus("Type de scan invalide.", true);
    return;
  }

  const MAX_TARGET_LENGTH = 128;
  const target = rawTarget.trim().slice(0, MAX_TARGET_LENGTH);

  const payload = {
    endpoint_id: endpointId,
    event_type: eventType,
    severity,
    source: "ui-scan-tool",
    description: `UI simulated ${scanType} scan on ${target}`,
    details: { target, simulated: true },
  };

  setLoading(true);
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
      setStatus("Erreur 401: token invalide ou expiré", true);
      return;
    }

    if (!response.ok) {
      setStatus(`Erreur création event scan (${response.status})`, true);
      if (resultNode) {
        resultNode.textContent = "Échec création event scan.";
      }
      return;
    }

    const created = await response.json();
    if (resultNode) {
      resultNode.textContent = JSON.stringify(created, null, 2);
    }
    setStatus("Scan simulé envoyé via /events.");
  } catch (_error) {
    setStatus("Erreur réseau pendant le scan simulé", true);
  } finally {
    setLoading(false);
  }
}

window.addEventListener("DOMContentLoaded", () => {
  initActiveNav();

  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", login);
  }

  const loadButton = document.getElementById("load-data");
  if (loadButton) {
    loadButton.addEventListener("click", loadProtectedData);
  }

  setupTableControls();

  if (isAlertsPage()) {
    setupAlertsAutoRefresh();
  }

  const refreshDashboardButton = document.getElementById("refresh-dashboard");
  if (refreshDashboardButton && isDashboardPage()) {
    refreshDashboardButton.addEventListener("click", refreshDashboardCounters);
  }

  const scanForm = document.getElementById("scan-form");
  if (scanForm && isScansPage()) {
    scanForm.addEventListener("submit", submitSimulatedScan);
  }

  // Auto-refresh KPI toutes les 30 secondes sur le dashboard
  if (isDashboardPage()) {
    const kpiRefreshInterval = window.setInterval(() => {
      if (authToken) {
        refreshDashboardCounters();
      }
    }, 30000);

    // Nettoyage lors du déchargement de la page
    window.addEventListener("beforeunload", () => {
      window.clearInterval(kpiRefreshInterval);
    });
  }
});
