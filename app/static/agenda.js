const EMPLOYEE_DETAILS = {
  Smith: "Seguimiento del turno de la manana con enfoque en apertura, servicio y cierre ordenado.",
  Marisela: "Control del turno de la manana con enfoque en limpieza, atencion y reporte final.",
};

const AGENDA_TASKS = [
  "Apertura del local",
  "Limpieza inicial estacion de trabajo",
  "Preparacion sistema de cobro (revisar efectivo de caja chica) $________",
  "Activacion de PedidosYa (asegurarse conectar a la electricidad)",
  "Preparacion de ingredientes (calentar)",
  "Colocar insumos, servilletas, pajillas, aceite, especias, menus y utensilios en mesa de trabajo",
  "Preparar dining area. Limpiar mesas y sillas. Limpiar y rellenar los servilleteros, botes de alcohol gel",
  "Barrer y trapear (manchas) del area del dining",
  "Recoger basura de la acera",
  "Inventario de panes Baguette: ______  Frances: ______  Pansalchi: ______  GuanaBurger: ______",
  "Refrigerador (area de preparacion)",
  "Rellenar botes de aderezos y mantener 10 frasquitos de ketchup (para llevar)",
  "Preparar vegetales (cortar) zanahoria, chile verde, cebolla",
  "Revisar que la pila tenga suficiente agua",
  "Revision de banos",
  "Limpiar las mesas, inmediatamente despues de que el cliente se ha ido.",
  "Ofrecer los combos, cuando el cliente esta indeciso.",
  "Siempre dar cupones a los clientes nuevos.",
  "Familiarizarse con el menu de GPF (habra pruebas)",
  "Somos agradecidos por eso siempre dar las gracias cuando el cliente llega y cuando se va.",
  "Corte de caja y entrega al siguiente turno a las 3:00 pm.",
  "Tomar foto al reporte diario y enviarlo al grupo de WhatsApp: GPF TEAM",
  "Limpieza de la vitrina. Dejar en orden la estacion de trabajo, el area del dining, refrigerador y bodega.",
];

const AGENDA_STORAGE_VERSION = "v4";
const FILLABLE_TASKS = {
  2: {
    parts: [
      "Preparacion sistema de cobro (revisar efectivo de caja chica) $",
      "",
    ],
    fields: ["cash_amount"],
    placeholders: ["Monto"],
  },
  9: {
    parts: [
      "Inventario de panes Baguette: ",
      "  Frances: ",
      "  Pansalchi: ",
      "  GuanaBurger: ",
      "",
    ],
    fields: ["baguette", "frances", "pansalchi", "guanaburger"],
    placeholders: ["Cantidad", "Cantidad", "Cantidad", "Cantidad"],
  },
};

const agendaElements = {
  createAgendaReportBtn: document.getElementById("createAgendaReportBtn"),
  employeeSelect: document.getElementById("employeeSelect"),
  agendaReportContent: document.getElementById("agendaReportContent"),
  dayNameText: document.getElementById("dayNameText"),
  dateText: document.getElementById("dateText"),
  agendaTableBody: document.getElementById("agendaTableBody"),
  completedCount: document.getElementById("completedCount"),
  pendingCount: document.getElementById("pendingCount"),
  progressBar: document.getElementById("progressBar"),
  employeeTitle: document.getElementById("employeeTitle"),
  employeeDescription: document.getElementById("employeeDescription"),
  photoSentYes: document.getElementById("photoSentYes"),
  photoHourInput: document.getElementById("photoHourInput"),
  openAgendaHistoryBtn: document.getElementById("openAgendaHistoryBtn"),
  closeAgendaHistoryBtn: document.getElementById("closeAgendaHistoryBtn"),
  agendaHistoryModal: document.getElementById("agendaHistoryModal"),
  agendaReportsList: document.getElementById("agendaReportsList"),
  saveSuccessPopup: document.getElementById("saveSuccessPopup"),
  saveReportBtn: document.getElementById("saveReportBtn"),
};

const agendaState = {
  employee: "",
  isReportOpen: false,
  checks: {},
  lockedChecks: {},
  photoSent: false,
  photoHour: "",
  fillValues: {},
};

let savePopupTimeoutId = null;

document.addEventListener("DOMContentLoaded", initAgenda);

function initAgenda() {
  if (!agendaElements.employeeSelect) {
    return;
  }

  agendaState.employee = agendaElements.employeeSelect.value || "";
  agendaElements.dayNameText.textContent = "";
  agendaElements.dateText.textContent = "";

  agendaElements.createAgendaReportBtn.addEventListener("click", () => {
    agendaState.isReportOpen = true;
    if (agendaState.employee) {
      loadAgendaState();
    } else {
      resetAgendaState();
    }
    renderAgenda();
  });

  agendaElements.employeeSelect.addEventListener("change", (event) => {
    agendaState.employee = event.target.value;
    if (agendaState.isReportOpen && agendaState.employee) {
      loadAgendaState();
    } else if (agendaState.isReportOpen) {
      resetAgendaState();
    }
    renderAgenda();
  });

  agendaElements.agendaTableBody.addEventListener("change", (event) => {
    const checkbox = event.target.closest('input[data-role="agenda-check"]');
    if (!checkbox) {
      return;
    }

    if (!checkbox.checked && agendaState.lockedChecks[checkbox.dataset.key]) {
      checkbox.checked = true;
      return;
    }

    agendaState.checks[checkbox.dataset.key] = checkbox.checked;
    persistAgendaState();
    renderSummary();
  });

  agendaElements.agendaTableBody.addEventListener("input", (event) => {
    const input = event.target.closest('input[data-role="agenda-fill"]');
    if (!input) {
      return;
    }
    agendaState.fillValues[input.dataset.fillKey] = input.value;
    persistAgendaState();
  });

  agendaElements.photoSentYes.addEventListener("change", () => {
    agendaState.photoSent = agendaElements.photoSentYes.checked;
    persistAgendaState();
  });

  agendaElements.photoHourInput.addEventListener("input", () => {
    agendaState.photoHour = agendaElements.photoHourInput.value;
    persistAgendaState();
  });

  agendaElements.saveReportBtn.addEventListener("click", saveCurrentReport);
  agendaElements.openAgendaHistoryBtn.addEventListener("click", openAgendaHistory);
  agendaElements.closeAgendaHistoryBtn.addEventListener("click", closeAgendaHistory);
  agendaElements.agendaHistoryModal.addEventListener("click", (event) => {
    if (event.target === agendaElements.agendaHistoryModal) {
      closeAgendaHistory();
    }
  });
  agendaElements.agendaReportsList.addEventListener("click", handleHistoryAction);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !agendaElements.agendaHistoryModal.classList.contains("hidden")) {
      closeAgendaHistory();
    }
  });

  renderAgenda();
}

function getCurrentDate() {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return now;
}

function getCurrentDayName() {
  const value = getCurrentDate().toLocaleDateString("es-SV", { weekday: "long" });
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function getCurrentDateText() {
  const now = getCurrentDate();
  const day = now.getDate();
  const month = now.toLocaleDateString("es-SV", { month: "long" });
  const year = now.getFullYear();
  return `${day} de ${month} ${year}`;
}

function getStorageKey() {
  if (!agendaState.employee) {
    return "";
  }
  const currentDate = getCurrentDate().toISOString().slice(0, 10);
  return `agenda-diaria:${AGENDA_STORAGE_VERSION}:${agendaState.employee}:${currentDate}`;
}

function getReportsStorageKey() {
  return `agenda-diaria:${AGENDA_STORAGE_VERSION}:reports`;
}

function getCheckKey(taskIndex) {
  return String(taskIndex);
}

function loadAgendaState() {
  if (!agendaState.employee) {
    resetAgendaState();
    return;
  }

  try {
    const raw = window.localStorage.getItem(getStorageKey());
    const parsed = raw ? JSON.parse(raw) : {};
    agendaState.checks = parsed.checks || {};
    agendaState.lockedChecks = parsed.lockedChecks || {};
    agendaState.photoSent = Boolean(parsed.photoSent);
    agendaState.photoHour = parsed.photoHour || "";
    agendaState.fillValues = parsed.fillValues || {};
  } catch {
    agendaState.checks = {};
    agendaState.lockedChecks = {};
    agendaState.photoSent = false;
    agendaState.photoHour = "";
    agendaState.fillValues = {};
  }
}

function persistAgendaState() {
  const storageKey = getStorageKey();
  if (!storageKey) {
    return;
  }

  try {
    window.localStorage.setItem(
      storageKey,
      JSON.stringify({
        checks: agendaState.checks,
        lockedChecks: agendaState.lockedChecks,
        photoSent: agendaState.photoSent,
        photoHour: agendaState.photoHour,
        fillValues: agendaState.fillValues,
      })
    );
  } catch {
    // Si el navegador no permite guardar, la vista sigue funcionando en memoria.
  }
}

function clearAgendaStateStorage() {
  const storageKey = getStorageKey();
  if (!storageKey) {
    return;
  }

  try {
    window.localStorage.removeItem(storageKey);
  } catch {
    // Ignorar si el navegador bloquea almacenamiento.
  }
}

function getSavedReports() {
  try {
    const raw = window.localStorage.getItem(getReportsStorageKey());
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistSavedReports(reports) {
  try {
    window.localStorage.setItem(getReportsStorageKey(), JSON.stringify(reports));
  } catch {
    // Ignorar si el navegador bloquea almacenamiento.
  }
}

function getCurrentReportName() {
  return `${agendaState.employee || "Sin empleado"} - ${getCurrentDateText()}`;
}

function buildAgendaExportPayload() {
  const completedCount = Object.values(agendaState.checks).filter(Boolean).length;
  return {
    employee_name: agendaState.employee,
    day_name: getCurrentDayName(),
    date_text: getCurrentDateText(),
    entry_time: "9:30 am",
    exit_time: "4:00 pm",
    completed_count: completedCount,
    pending_count: AGENDA_TASKS.length - completedCount,
    photo_sent: agendaState.photoSent,
    photo_hour: agendaState.photoHour,
    tasks: AGENDA_TASKS.map((label, taskIndex) => ({
      label: getResolvedTaskLabel(taskIndex, agendaState.fillValues),
      checked: Boolean(agendaState.checks[getCheckKey(taskIndex)]),
    })),
  };
}

function saveCurrentReport() {
  if (!agendaState.employee) {
    return;
  }

  const reports = getSavedReports();
  const completedCount = Object.values(agendaState.checks).filter(Boolean).length;
  for (const [key, value] of Object.entries(agendaState.checks)) {
    if (value) {
      agendaState.lockedChecks[key] = true;
    }
  }

  const report = {
    id: `${agendaState.employee}-${getCurrentDate().toISOString().slice(0, 10)}`,
    employee: agendaState.employee,
    dayName: getCurrentDayName(),
    dateText: getCurrentDateText(),
    name: getCurrentReportName(),
    completedChecks: completedCount,
    totalChecks: AGENDA_TASKS.length,
    savedAt: new Date().toISOString(),
    checks: { ...agendaState.checks },
    lockedChecks: { ...agendaState.lockedChecks },
    photoSent: agendaState.photoSent,
    photoHour: agendaState.photoHour,
    fillValues: { ...agendaState.fillValues },
  };

  const nextReports = [report, ...reports.filter((item) => item.id !== report.id)];
  persistSavedReports(nextReports);
  clearAgendaStateStorage();
  agendaState.isReportOpen = false;
  agendaElements.employeeSelect.value = "";
  agendaState.employee = "";
  resetAgendaState();
  persistAgendaState();
  renderAgenda();
  renderReportsHistory();
  showSavePopup();
}

function openAgendaHistory() {
  renderReportsHistory();
  agendaElements.agendaHistoryModal.classList.remove("hidden");
}

function closeAgendaHistory() {
  agendaElements.agendaHistoryModal.classList.add("hidden");
}

function renderReportsHistory() {
  const reports = getSavedReports();
  if (reports.length === 0) {
    agendaElements.agendaReportsList.innerHTML = '<p class="muted">No hay reportes guardados todavía.</p>';
    return;
  }

  agendaElements.agendaReportsList.innerHTML = reports
    .map((report) => {
      const when = new Date(report.savedAt).toLocaleString("es-SV", {
        dateStyle: "short",
        timeStyle: "short",
      });
      return `
        <article class="history-item">
          <div>
            <p><strong>${escapeHtml(report.name)}</strong></p>
            <p>${escapeHtml(report.employee)} · ${escapeHtml(report.dayName || "")} · ${escapeHtml(report.dateText || "")} · ${report.completedChecks}/${report.totalChecks} checks</p>
            <p>Guardado: ${escapeHtml(when)}</p>
          </div>
          <div class="history-actions">
            <button type="button" class="ghost-btn action-btn" data-action="load-report" data-report-id="${report.id}">Cargar</button>
            <details class="export-dropdown">
              <summary class="ghost-btn action-btn">Exportar</summary>
              <div class="export-dropdown-menu">
                <button type="button" class="ghost-btn action-btn" data-action="export-report-pdf" data-report-id="${report.id}">PDF</button>
                <button type="button" class="ghost-btn action-btn" data-action="export-report-jpg" data-report-id="${report.id}">JPG</button>
              </div>
            </details>
            <button type="button" class="danger-btn action-btn" data-action="delete-report" data-report-id="${report.id}">Borrar</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function handleHistoryAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const action = button.dataset.action;
  const reportId = button.dataset.reportId;
  const reports = getSavedReports();
  const report = reports.find((item) => item.id === reportId);

  if (action === "delete-report") {
    persistSavedReports(reports.filter((item) => item.id !== reportId));
    renderReportsHistory();
    return;
  }

  if ((action === "export-report-pdf" || action === "export-report-jpg") && report) {
    const format = action === "export-report-pdf" ? "pdf" : "jpg";
    exportSavedReport(report, format);
    return;
  }

  if (action === "load-report" && report) {
    agendaState.isReportOpen = true;
    agendaState.employee = report.employee;
    agendaElements.employeeSelect.value = report.employee;
    agendaState.checks = report.checks || {};
    agendaState.lockedChecks = report.lockedChecks || buildLockedChecksFromReport(report.checks || {});
    agendaState.photoSent = Boolean(report.photoSent);
    agendaState.photoHour = report.photoHour || "";
    agendaState.fillValues = report.fillValues || {};
    renderAgenda();
    closeAgendaHistory();
  }
}

async function exportSavedReport(report, format) {
  const payload = {
    employee_name: report.employee,
    day_name: report.dayName || getCurrentDayName(),
    date_text: report.dateText || getCurrentDateText(),
    entry_time: "9:30 am",
    exit_time: "4:00 pm",
    completed_count: report.completedChecks,
    pending_count: report.totalChecks - report.completedChecks,
    photo_sent: Boolean(report.photoSent),
    photo_hour: report.photoHour || "",
    tasks: AGENDA_TASKS.map((label, taskIndex) => ({
      label: getResolvedTaskLabel(taskIndex, report.fillValues || {}),
      checked: Boolean((report.checks || {})[getCheckKey(taskIndex)]),
    })),
  };

  const response = await fetch(`/api/agenda/export.${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    window.alert("No se pudo exportar el reporte.");
    return;
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${report.name.replaceAll(" ", "_")}.${format}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function renderAgenda() {
  const hasEmployee = Boolean(agendaState.employee);
  agendaElements.employeeTitle.textContent = agendaState.employee || "Sin empleado";
  agendaElements.employeeDescription.textContent =
    hasEmployee ? (EMPLOYEE_DETAILS[agendaState.employee] || "") : "";
  agendaElements.dayNameText.textContent = agendaState.isReportOpen ? getCurrentDayName() : "";
  agendaElements.dateText.textContent = agendaState.isReportOpen ? getCurrentDateText() : "";
  agendaElements.agendaReportContent.classList.toggle("hidden", !agendaState.isReportOpen);

  agendaElements.agendaTableBody.innerHTML = AGENDA_TASKS.map((task, taskIndex) => {
    const key = getCheckKey(taskIndex);
    const checked = Boolean(agendaState.checks[key]);
    const locked = Boolean(agendaState.lockedChecks[key] && checked);

    return `
      <tr>
        <td class="agenda-task-label">${renderTaskLabel(taskIndex)}</td>
        <td class="agenda-check-cell">
          <label class="agenda-table-check">
            <input
              type="checkbox"
              data-role="agenda-check"
              data-key="${key}"
              ${checked ? "checked" : ""}
              ${locked ? "disabled" : ""}
            />
          </label>
        </td>
      </tr>
    `;
  }).join("");

  agendaElements.photoSentYes.checked = agendaState.photoSent;
  agendaElements.photoHourInput.value = agendaState.photoHour;

  agendaElements.saveReportBtn.disabled = !hasEmployee;
  renderSummary();
}

function renderSummary() {
  const totalChecks = AGENDA_TASKS.length;
  const completedChecks = Object.values(agendaState.checks).filter(Boolean).length;
  const safeCompleted = Math.min(completedChecks, totalChecks);
  const pendingChecks = Math.max(totalChecks - safeCompleted, 0);
  const percent = totalChecks ? Math.round((safeCompleted / totalChecks) * 100) : 0;

  agendaElements.completedCount.textContent = String(safeCompleted);
  agendaElements.pendingCount.textContent = String(pendingChecks);
  agendaElements.progressBar.style.width = `${percent}%`;
}

function renderTaskLabel(taskIndex) {
  const config = FILLABLE_TASKS[taskIndex];
  const baseLabel = AGENDA_TASKS[taskIndex];
  if (!config) {
    return escapeHtml(baseLabel);
  }

  return config.fields
    .map((field, index) => {
      const prefix = escapeHtml(config.parts[index] || "");
      const value = escapeHtml(agendaState.fillValues[field] || "");
      const placeholder = escapeHtml(config.placeholders[index] || "");
      const input = `<input type="text" class="agenda-inline-input" data-role="agenda-fill" data-fill-key="${field}" value="${value}" placeholder="${placeholder}" />`;
      return `${prefix}${input}`;
    })
    .join("") + escapeHtml(config.parts[config.parts.length - 1] || "");
}

function getResolvedTaskLabel(taskIndex, values) {
  const config = FILLABLE_TASKS[taskIndex];
  const baseLabel = AGENDA_TASKS[taskIndex];
  if (!config) {
    return baseLabel;
  }

  return config.fields
    .map((field, index) => `${config.parts[index] || ""}${String(values[field] || "").trim() || "______"}`)
    .join("") + (config.parts[config.parts.length - 1] || "");
}

function buildLockedChecksFromReport(checks) {
  return Object.fromEntries(
    Object.entries(checks).filter(([, value]) => Boolean(value)).map(([key]) => [key, true])
  );
}

function resetAgendaState() {
  agendaState.checks = {};
  agendaState.lockedChecks = {};
  agendaState.photoSent = false;
  agendaState.photoHour = "";
  agendaState.fillValues = {};
}

function showSavePopup() {
  if (!agendaElements.saveSuccessPopup) {
    return;
  }

  agendaElements.saveSuccessPopup.classList.remove("hidden");
  if (savePopupTimeoutId) {
    window.clearTimeout(savePopupTimeoutId);
  }

  savePopupTimeoutId = window.setTimeout(() => {
    agendaElements.saveSuccessPopup.classList.add("hidden");
    savePopupTimeoutId = null;
  }, 1400);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
