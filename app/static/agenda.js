const EMPLOYEE_DETAILS = {
  Smith: "Seguimiento del turno de la manana con enfoque en apertura, servicio y cierre ordenado.",
  Marisela: "Control del turno de la manana con enfoque en limpieza, atencion y reporte final.",
};

const SHIFT_OPTIONS = {
  "am-leader": {
    label: "AM - Lider",
    schedule: "AM",
    taskSet: "am",
    entryTime: "9:30 am",
    exitTime: "4:00 pm",
  },
  "am-collaborator": {
    label: "AM - Colaborador",
    schedule: "AM",
    taskSet: "am",
    entryTime: "9:30 am",
    exitTime: "4:00 pm",
  },
  "pm-leader": {
    label: "PM - Lider",
    schedule: "PM",
    taskSet: "pm",
    entryTime: "3:00 pm",
    exitTime: "Cierre",
  },
  "pm-collaborator": {
    label: "PM - Colaborador",
    schedule: "PM",
    taskSet: "pm",
    entryTime: "3:00 pm",
    exitTime: "Cierre",
  },
};

const AM_AGENDA_TASKS = [
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

const PM_AGENDA_TASKS = [
  {
    section: true,
    parts: [{ text: "Inventario de " }, { text: "PROTEINAS", bold: true }, { text: " (" }, { text: "en porciones" }, { text: ")", bold: true }],
  },
  { parts: [{ text: "Steak Sandwich –  " }], fieldKey: "pm_steak_sandwich" },
  { parts: [{ text: "Tropicalito – " }], fieldKey: "pm_tropicalito" },
  { parts: [{ text: "Milanesa –  " }], fieldKey: "pm_milanesa" },
  { parts: [{ text: "Bistec – " }], fieldKey: "pm_bistec" },
  { parts: [{ text: "Premium - " }], fieldKey: "pm_premium" },
  { parts: [{ text: "Alitas – " }], fieldKey: "pm_alitas" },
  { section: true, parts: [{ text: "Inventario de ", bold: true }, { text: "ADERESOS:", bold: true }] },
  { parts: [{ text: "Jalapeño – " }], fieldKey: "pm_aderezo_jalapeno" },
  { parts: [{ text: "Cítrico – " }], fieldKey: "pm_citrico" },
  { parts: [{ text: "Chipotle –" }], fieldKey: "pm_chipotle" },
  { parts: [{ text: "Curtido – " }], fieldKey: "pm_curtido" },
  { parts: [{ text: "Cebolla criolla – " }], fieldKey: "pm_cebolla_criolla" },
  { parts: [{ text: "Jalapeño en vinagre – " }], fieldKey: "pm_jalapeno_vinagre" },
  { parts: [{ text: "Salsa Criolla" }], fieldKey: "pm_salsa_criolla" },
  { parts: [{ text: "Chimichurri" }], fieldKey: "pm_chimichurri" },
  { section: true, parts: [{ text: "Inventario de " }, { text: "VEGETALES", bold: true }] },
  { parts: [{ text: "Repollo" }], fieldKey: "pm_repollo" },
  { parts: [{ text: "Jalapeños" }], fieldKey: "pm_jalapenos" },
  { parts: [{ text: "Zanahoria" }], fieldKey: "pm_zanahoria" },
  { parts: [{ text: "Palmito" }], fieldKey: "pm_palmito" },
  { parts: [{ text: "Chile verde" }], fieldKey: "pm_chile_verde" },
  { parts: [{ text: "Tomates" }], fieldKey: "pm_tomates" },
  { parts: [{ text: "Cebolla blanca" }], fieldKey: "pm_cebolla_blanca" },
  { parts: [{ text: "Cebolla morada" }], fieldKey: "pm_cebolla_morada" },
  { parts: [{ text: "Limones" }], fieldKey: "pm_limones" },
  { parts: [{ text: "Cilantro" }], fieldKey: "pm_cilantro" },
  { parts: [{ text: "Perejil" }], fieldKey: "pm_perejil" },
  { parts: [{ text: "Apio" }], fieldKey: "pm_apio" },
  { parts: [{ text: "Rabano" }], fieldKey: "pm_rabano" },
  { section: true, parts: [{ text: "Inventario de " }, { text: "BEBIDAS", bold: true }] },
  { parts: [{ text: "Jamaica                    " }], fieldKey: "pm_jamaica" },
  { parts: [{ text: "Chan  " }], fieldKey: "pm_chan" },
  { parts: [{ text: "Sodas de sabores" }], fieldKey: "pm_sodas_sabores" },
  { parts: [{ text: "Coca Cola" }], fieldKey: "pm_coca_cola" },
  { parts: [{ text: "Agua en botella" }], fieldKey: "pm_agua_botella" },
  { parts: [{ text: "Agua garrafon" }], fieldKey: "pm_agua_garrafon" },
  { section: true, parts: [{ text: "Inventario de" }, { text: " PANES", bold: true }] },
  { parts: [{ text: "Baguette " }], fieldKey: "pm_baguette" },
  { parts: [{ text: "Pansalchi" }], fieldKey: "pm_pansalchi" },
  { parts: [{ text: "Pan francés" }], fieldKey: "pm_pan_frances" },
  { parts: [{ text: "Hamburguesas " }], fieldKey: "pm_hamburguesas" },
  { section: true, parts: [{ text: "OPERATIVO 3:00PM", bold: true }] },
  { parts: [{ text: "Recibir caja chica - abrir turno pm" }], fieldKey: "pm_recibir_caja" },
  { parts: [{ text: "Revisar mesa de trabajo (utensilios, especias, aceite, servilletas etc.)" }], fieldKey: "pm_mesa_trabajo" },
  { parts: [{ text: "Revisar el dining; servilleteros, alcohol gel, mesas y sillas limpias, piso limpio." }], fieldKey: "pm_dining" },
  { parts: [{ text: "Revisar aplicación de PedidosYa" }], fieldKey: "pm_pedidosya" },
  { parts: [{ text: "Revisar el aseo general de GPF " }], fieldKey: "pm_aseo_general" },
  {
    parts: [{ text: "Importante; " }, { text: "Familiarizarse con el menú de GPF", bold: true }, { text: " " }, { text: "(habrá pruebas)", italic: true }],
    fieldKey: "pm_menu_gpf",
  },
  { parts: [{ text: "Ofrecer cupones " }], fieldKey: "pm_ofrecer_cupones" },
  { parts: [{ text: "Cuatro personas o mas el cupón del 5 pan gratis" }], fieldKey: "pm_cupon_5_pan" },
  { parts: [{ text: "Reseñas en Google (QR disponible)" }], fieldKey: "pm_resenas_google" },
  { parts: [{ text: "Barrer la acera todos los días." }], fieldKey: "pm_barrer_acera" },
  { parts: [{ text: "Somos agradecidos por eso siempre dar las gracias cuando el cliente llega y cuando se va." }], fieldKey: "pm_agradecidos" },
  { parts: [{ text: "Corte de caja y cierre de turno." }], fieldKey: "pm_corte_caja" },
  { parts: [{ text: "Tomar foto al rexporte diario y enviarlo al grupo de WhatsApp: GPF TEAM" }], fieldKey: "pm_foto_rexporte" },
];

const AGENDA_TASK_SETS = {
  am: AM_AGENDA_TASKS,
  pm: PM_AGENDA_TASKS,
};

const AGENDA_STORAGE_VERSION = "v6";
const AM_FILLABLE_TASKS = {
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

const FILLABLE_TASK_SETS = {
  am: AM_FILLABLE_TASKS,
  pm: {},
};

const agendaElements = {
  createAgendaReportBtn: document.getElementById("createAgendaReportBtn"),
  shiftSelect: document.getElementById("shiftSelect"),
  employeeSelect: document.getElementById("employeeSelect"),
  agendaReportContent: document.getElementById("agendaReportContent"),
  dayNameText: document.getElementById("dayNameText"),
  dateText: document.getElementById("dateText"),
  entryTimeText: document.getElementById("entryTimeText"),
  exitTimeText: document.getElementById("exitTimeText"),
  agendaResponsibilityHeader: document.getElementById("agendaResponsibilityHeader"),
  agendaCheckHeader: document.getElementById("agendaCheckHeader"),
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
  shift: "",
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
  agendaState.shift = agendaElements.shiftSelect.value || "";
  agendaElements.dayNameText.textContent = "";
  agendaElements.dateText.textContent = "";

  agendaElements.createAgendaReportBtn.addEventListener("click", () => {
    agendaState.isReportOpen = true;
    if (canLoadAgendaState()) {
      loadAgendaState();
    } else {
      resetAgendaState();
    }
    renderAgenda();
  });

  agendaElements.shiftSelect.addEventListener("change", (event) => {
    agendaState.shift = event.target.value;
    if (agendaState.isReportOpen && canLoadAgendaState()) {
      loadAgendaState();
    } else if (agendaState.isReportOpen) {
      resetAgendaState();
    }
    renderAgenda();
  });

  agendaElements.employeeSelect.addEventListener("change", (event) => {
    agendaState.employee = event.target.value;
    if (agendaState.isReportOpen && canLoadAgendaState()) {
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

function canLoadAgendaState() {
  return Boolean(agendaState.employee && agendaState.shift);
}

function getShiftConfig(shift = agendaState.shift) {
  return SHIFT_OPTIONS[shift] || null;
}

function getCurrentTasks(shift = agendaState.shift) {
  const shiftConfig = getShiftConfig(shift);
  if (!shiftConfig) {
    return [];
  }
  return AGENDA_TASK_SETS[shiftConfig.taskSet] || [];
}

function getCurrentFillableTasks(shift = agendaState.shift) {
  const shiftConfig = getShiftConfig(shift);
  if (!shiftConfig) {
    return {};
  }
  return FILLABLE_TASK_SETS[shiftConfig.taskSet] || {};
}

function isCheckableTask(task) {
  return !(typeof task === "object" && task?.section);
}

function getCheckableTasks(tasks = getCurrentTasks()) {
  return tasks.filter((task) => isCheckableTask(task));
}

function getStorageKey() {
  if (!agendaState.employee || !agendaState.shift) {
    return "";
  }
  const currentDate = getCurrentDate().toISOString().slice(0, 10);
  return `agenda-diaria:${AGENDA_STORAGE_VERSION}:${agendaState.employee}:${agendaState.shift}:${currentDate}`;
}

function getReportsStorageKey() {
  return `agenda-diaria:${AGENDA_STORAGE_VERSION}:reports`;
}

function getCheckKey(taskIndex) {
  return String(taskIndex);
}

function loadAgendaState() {
  if (!canLoadAgendaState()) {
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
  const shiftLabel = getShiftConfig()?.label || "Sin turno";
  return `${agendaState.employee || "Sin empleado"} - ${shiftLabel} - ${getCurrentDateText()}`;
}

function buildAgendaExportPayload() {
  const tasks = getCurrentTasks();
  const shiftConfig = getShiftConfig();
  const completedCount = Object.values(agendaState.checks).filter(Boolean).length;
  const totalChecks = getCheckableTasks(tasks).length;
  return {
    employee_name: agendaState.employee,
    shift_label: shiftConfig?.label || "",
    day_name: getCurrentDayName(),
    date_text: getCurrentDateText(),
    entry_time: shiftConfig?.entryTime || "",
    exit_time: shiftConfig?.exitTime || "",
    completed_count: completedCount,
    pending_count: totalChecks - completedCount,
    photo_sent: agendaState.photoSent,
    photo_hour: agendaState.photoHour,
    tasks: tasks.map((task, taskIndex) => ({
      label: getResolvedTaskLabel(taskIndex, agendaState.fillValues, agendaState.shift),
      label_parts: getResolvedTaskParts(taskIndex, agendaState.fillValues, agendaState.shift),
      checkable: isCheckableTask(task),
      checked: Boolean(agendaState.checks[getCheckKey(taskIndex)]),
    })),
  };
}

function saveCurrentReport() {
  if (!agendaState.employee || !agendaState.shift) {
    return;
  }

  const reports = getSavedReports();
  const tasks = getCurrentTasks();
  const shiftConfig = getShiftConfig();
  const completedCount = Object.values(agendaState.checks).filter(Boolean).length;
  const totalChecks = getCheckableTasks(tasks).length;
  for (const [key, value] of Object.entries(agendaState.checks)) {
    if (value) {
      agendaState.lockedChecks[key] = true;
    }
  }

  const report = {
    id: `${agendaState.employee}-${agendaState.shift}-${getCurrentDate().toISOString().slice(0, 10)}`,
    employee: agendaState.employee,
    shift: agendaState.shift,
    shiftLabel: shiftConfig?.label || "",
    dayName: getCurrentDayName(),
    dateText: getCurrentDateText(),
    name: getCurrentReportName(),
    completedChecks: completedCount,
    totalChecks,
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
  agendaElements.shiftSelect.value = "";
  agendaState.employee = "";
  agendaState.shift = "";
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
            <p>${escapeHtml(report.employee)} · ${escapeHtml(report.shiftLabel || report.shift || "")} · ${escapeHtml(report.dayName || "")} · ${escapeHtml(report.dateText || "")} · ${report.completedChecks}/${report.totalChecks} checks</p>
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
    agendaState.shift = report.shift || "am-leader";
    agendaElements.employeeSelect.value = report.employee;
    agendaElements.shiftSelect.value = agendaState.shift;
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
  const shiftConfig = getShiftConfig(report.shift || "am-leader");
  const tasks = getCurrentTasks(report.shift || "am-leader");
  const payload = {
    employee_name: report.employee,
    shift_label: report.shiftLabel || shiftConfig?.label || "",
    day_name: report.dayName || getCurrentDayName(),
    date_text: report.dateText || getCurrentDateText(),
    entry_time: shiftConfig?.entryTime || "",
    exit_time: shiftConfig?.exitTime || "",
    completed_count: report.completedChecks,
    pending_count: report.totalChecks - report.completedChecks,
    photo_sent: Boolean(report.photoSent),
    photo_hour: report.photoHour || "",
    tasks: tasks.map((task, taskIndex) => ({
      label: getResolvedTaskLabel(taskIndex, report.fillValues || {}, report.shift || "am-leader"),
      label_parts: getResolvedTaskParts(taskIndex, report.fillValues || {}, report.shift || "am-leader"),
      checkable: isCheckableTask(task),
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
  const hasShift = Boolean(agendaState.shift);
  const shiftConfig = getShiftConfig();
  const tasks = getCurrentTasks();
  const isPmShift = shiftConfig?.taskSet === "pm";
  agendaElements.employeeTitle.textContent = agendaState.employee || "Sin empleado";
  agendaElements.employeeDescription.textContent =
    hasEmployee ? (EMPLOYEE_DETAILS[agendaState.employee] || "") : "";
  agendaElements.dayNameText.textContent = agendaState.isReportOpen ? getCurrentDayName() : "";
  agendaElements.dateText.textContent = agendaState.isReportOpen ? getCurrentDateText() : "";
  agendaElements.entryTimeText.textContent = agendaState.isReportOpen ? (shiftConfig?.entryTime || "") : "";
  agendaElements.exitTimeText.textContent = agendaState.isReportOpen ? (shiftConfig?.exitTime || "") : "";
  agendaElements.agendaResponsibilityHeader.textContent = isPmShift ? "RESPONSABILIDAD/DESEMPENO" : "RESPONSABILIDAD";
  agendaElements.agendaCheckHeader.textContent = isPmShift ? "check" : "CHECK";
  agendaElements.agendaReportContent.classList.toggle("hidden", !agendaState.isReportOpen);

  agendaElements.agendaTableBody.innerHTML = tasks.map((task, taskIndex) => {
    const key = getCheckKey(taskIndex);
    const checked = Boolean(agendaState.checks[key]);
    const locked = Boolean(agendaState.lockedChecks[key] && checked);
    const checkable = isCheckableTask(task);

    return `
      <tr class="${checkable ? "" : "agenda-section-row"}">
        <td class="agenda-task-label">${renderTaskLabel(taskIndex)}</td>
        <td class="agenda-check-cell">
          ${checkable ? `
            <label class="agenda-table-check">
              <input
                type="checkbox"
                data-role="agenda-check"
                data-key="${key}"
                ${checked ? "checked" : ""}
                ${locked ? "disabled" : ""}
              />
            </label>
          ` : ""}
        </td>
      </tr>
    `;
  }).join("");

  agendaElements.photoSentYes.checked = agendaState.photoSent;
  agendaElements.photoHourInput.value = agendaState.photoHour;

  agendaElements.saveReportBtn.disabled = !hasEmployee || !hasShift;
  renderSummary();
}

function renderSummary() {
  const totalChecks = getCheckableTasks().length;
  const completedChecks = Object.values(agendaState.checks).filter(Boolean).length;
  const safeCompleted = Math.min(completedChecks, totalChecks);
  const pendingChecks = Math.max(totalChecks - safeCompleted, 0);
  const percent = totalChecks ? Math.round((safeCompleted / totalChecks) * 100) : 0;

  agendaElements.completedCount.textContent = String(safeCompleted);
  agendaElements.pendingCount.textContent = String(pendingChecks);
  agendaElements.progressBar.style.width = `${percent}%`;
}

function renderTaskLabel(taskIndex) {
  const task = getCurrentTasks()[taskIndex];
  if (typeof task === "object" && task?.parts) {
    const content = task.parts.map(renderTaskPart).join("");
    if (!task.fieldKey) {
      return content;
    }

    const value = escapeHtml(agendaState.fillValues[task.fieldKey] || "");
    return `${content}<input type="text" class="agenda-inline-input agenda-write-input" data-role="agenda-fill" data-fill-key="${task.fieldKey}" value="${value}" placeholder="Escribir" />`;
  }

  const config = getCurrentFillableTasks()[taskIndex];
  const baseLabel = getCurrentTasks()[taskIndex];
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

function renderTaskPart(part) {
  const text = escapeHtml(part.text || "");
  if (part.bold) {
    return `<strong>${text}</strong>`;
  }
  if (part.italic) {
    return `<em>${text}</em>`;
  }
  return text;
}

function getResolvedTaskLabel(taskIndex, values, shift = agendaState.shift) {
  const task = getCurrentTasks(shift)[taskIndex];
  if (typeof task === "object" && task?.parts) {
    const label = task.parts.map((part) => part.text || "").join("");
    if (!task.fieldKey) {
      return label;
    }
    const value = String(values[task.fieldKey] || "").trim() || "____________________";
    return `${label} ${value}`;
  }

  const config = getCurrentFillableTasks(shift)[taskIndex];
  const baseLabel = getCurrentTasks(shift)[taskIndex];
  if (!config) {
    return baseLabel;
  }

  return config.fields
    .map((field, index) => `${config.parts[index] || ""}${String(values[field] || "").trim() || "______"}`)
    .join("") + (config.parts[config.parts.length - 1] || "");
}

function getResolvedTaskParts(taskIndex, values, shift = agendaState.shift) {
  const task = getCurrentTasks(shift)[taskIndex];
  if (typeof task === "object" && task?.parts) {
    const parts = task.parts.map((part) => ({ ...part }));
    if (task.fieldKey) {
      const value = String(values[task.fieldKey] || "").trim() || "____________________";
      parts.push({ text: ` ${value}` });
    }
    return parts;
  }

  return [{ text: getResolvedTaskLabel(taskIndex, values, shift) }];
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
