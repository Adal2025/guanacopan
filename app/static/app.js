const BUSINESS_NAME = "Guanacopan Francés";
const BUSINESS_TITLE = "Orden de productos";
const BUSINESS_ADDRESS = "Entre, Avenida Jose Simeon Canas Sur 46, San Miguel.";
const BUSINESS_PHONE = "64435199";
const PREVIEW_LOGO = "/static/logo-gpf.jpg";
const SUPPLIER_DIRECTORY = window.SUPPLIER_DIRECTORY || {};

const state = {
  products: [],
  selectedSupplier: "",
  searchTerm: "",
  lines: [],
  orders: [],
  editingOrderId: null,
};

const elements = {
  supplierButtons: document.getElementById("supplierButtons"),
  productSearch: document.getElementById("productSearch"),
  searchMatches: document.getElementById("searchMatches"),
  orderLinesBody: document.getElementById("orderLinesBody"),
  orderForm: document.getElementById("orderForm"),
  generalNotes: document.getElementById("generalNotes"),
  saveOrderBtn: document.getElementById("saveOrderBtn"),
  discardOrderBtn: document.getElementById("discardOrderBtn"),
  cancelEditBtn: document.getElementById("cancelEditBtn"),
  editExportDropdown: document.getElementById("editExportDropdown"),
  itemsCount: document.getElementById("itemsCount"),
  previewContainer: document.getElementById("previewContainer"),
  ordersHistory: document.getElementById("ordersHistory"),
  openHistoryBtn: document.getElementById("openHistoryBtn"),
  closeHistoryBtn: document.getElementById("closeHistoryBtn"),
  historyModal: document.getElementById("historyModal"),
  flash: document.getElementById("flash"),
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindEvents();
  await Promise.all([loadProducts(), loadOrders()]);
  renderSupplierSelection();
  renderSearchMatches();
  renderOrderLines();
  renderPreview();
  syncEditorButtons();
}

function bindEvents() {
  elements.supplierButtons.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-supplier]");
    if (!button) {
      return;
    }

    const supplier = button.dataset.supplier;
    if (supplier === state.selectedSupplier) {
      return;
    }

    state.selectedSupplier = supplier;
    state.searchTerm = "";
    state.lines = [];
    state.editingOrderId = null;
    elements.productSearch.value = "";
    elements.productSearch.disabled = false;
    elements.generalNotes.value = "";

    renderSupplierSelection();
    renderSearchMatches();
    renderOrderLines();
    renderPreview();
    syncEditorButtons();
  });

  elements.productSearch.addEventListener("input", (event) => {
    state.searchTerm = event.target.value.trim();
    renderSearchMatches();
  });

  elements.searchMatches.addEventListener("click", (event) => {
    const button = event.target.closest('button[data-action="add-product"]');
    if (!button) {
      return;
    }

    addProductToLines(Number(button.dataset.productId));
    state.searchTerm = "";
    elements.productSearch.value = "";
    elements.productSearch.focus();

    renderSearchMatches();
    renderOrderLines();
    renderPreview();
  });

  elements.orderLinesBody.addEventListener("input", (event) => {
    const qtyInput = event.target.closest('input[data-action="qty"]');
    if (qtyInput) {
      const index = Number(qtyInput.dataset.index);
      const raw = qtyInput.value.trim();

      if (raw === "") {
        state.lines[index].quantity = 0;
        renderPreview();
        return;
      }

      const quantity = Number(raw.replace(",", "."));
      if (!Number.isFinite(quantity)) {
        return;
      }

      state.lines[index].quantity = round(quantity);
      renderPreview();
      return;
    }

    const noteInput = event.target.closest('input[data-action="note"]');
    if (!noteInput) {
      return;
    }

    const index = Number(noteInput.dataset.index);
    state.lines[index].note = noteInput.value;
    renderPreview();
  });

  elements.orderLinesBody.addEventListener("change", (event) => {
    const qtyInput = event.target.closest('input[data-action="qty"]');
    if (!qtyInput) {
      return;
    }

    const index = Number(qtyInput.dataset.index);
    const quantity = Number(qtyInput.value || 0);
    if (!quantity || quantity <= 0) {
      showFlash("La cantidad debe ser mayor a 0. El producto no se eliminó.", true);
    }

    renderOrderLines();
    renderPreview();
  });

  elements.orderLinesBody.addEventListener("click", (event) => {
    const button = event.target.closest('button[data-action="remove-line"]');
    if (!button) {
      return;
    }

    const index = Number(button.dataset.index);
    state.lines.splice(index, 1);
    renderOrderLines();
    renderPreview();
  });

  elements.ordersHistory.addEventListener("click", handleHistoryAction);

  elements.orderForm.addEventListener("submit", handleOrderSubmit);

  elements.cancelEditBtn.addEventListener("click", () => {
    clearEditor(true);
    showFlash("Edición cancelada.");
  });

  elements.discardOrderBtn.addEventListener("click", () => {
    if (state.editingOrderId) {
      return;
    }

    const hasDraft =
      state.lines.length > 0 ||
      Boolean(elements.generalNotes.value.trim());

    if (!hasDraft) {
      showFlash("No hay un pedido en curso para descartar.");
      return;
    }

    const confirmation = window.confirm(
      "¿Descartar el pedido en curso? Se perderán los cambios no guardados."
    );
    if (!confirmation) {
      return;
    }

    state.lines = [];
    state.searchTerm = "";
    elements.productSearch.value = "";
    elements.generalNotes.value = "";

    renderSearchMatches();
    renderOrderLines();
    renderPreview();
    syncEditorButtons();
    showFlash("Pedido en curso descartado.");
  });

  elements.generalNotes.addEventListener("input", () => {
    renderPreview();
    syncEditorButtons();
  });

  elements.editExportDropdown.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button || !state.editingOrderId) {
      return;
    }

    const orderId = state.editingOrderId;
    const action = button.dataset.action;

    if (action === "edit-export-pdf") {
      window.open(`/api/orders/${orderId}/export.pdf`, "_blank", "noopener");
      elements.editExportDropdown.open = false;
      return;
    }

    if (action === "edit-export-jpg") {
      window.open(`/api/orders/${orderId}/export.jpg`, "_blank", "noopener");
      elements.editExportDropdown.open = false;
    }
  });

  elements.openHistoryBtn.addEventListener("click", openHistoryModal);
  elements.closeHistoryBtn.addEventListener("click", closeHistoryModal);
  elements.historyModal.addEventListener("click", (event) => {
    if (event.target === elements.historyModal) {
      closeHistoryModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !elements.historyModal.classList.contains("hidden")) {
      closeHistoryModal();
    }
  });
}

function openHistoryModal() {
  elements.historyModal.classList.remove("hidden");
}

function closeHistoryModal() {
  elements.historyModal.classList.add("hidden");
}

function syncEditorButtons() {
  const hasNewDraft = state.lines.length > 0 || Boolean(elements.generalNotes.value.trim());

  if (state.editingOrderId) {
    elements.cancelEditBtn.classList.remove("hidden");
    elements.editExportDropdown.classList.remove("hidden");
    elements.discardOrderBtn.classList.add("hidden");
    if (!elements.saveOrderBtn.disabled) {
      elements.saveOrderBtn.textContent = "Guardar cambios";
    }
  } else {
    elements.cancelEditBtn.classList.add("hidden");
    elements.editExportDropdown.classList.add("hidden");
    elements.editExportDropdown.open = false;
    elements.discardOrderBtn.classList.toggle("hidden", !hasNewDraft);
    if (!elements.saveOrderBtn.disabled) {
      elements.saveOrderBtn.textContent = "Guardar pedido";
    }
  }
}

function getProductById(productId) {
  return state.products.find((product) => product.id === productId);
}

function getProductsBySupplier() {
  if (!state.selectedSupplier) {
    return [];
  }
  return state.products.filter((product) => product.supplier === state.selectedSupplier);
}

function getSearchMatches() {
  const term = state.searchTerm.toLowerCase();
  if (!state.selectedSupplier || !term) {
    return [];
  }

  return getProductsBySupplier()
    .filter((product) => product.name.toLowerCase().includes(term))
    .slice(0, 12);
}

function renderSupplierSelection() {
  const buttons = elements.supplierButtons.querySelectorAll("button[data-supplier]");
  for (const button of buttons) {
    button.classList.toggle("active", button.dataset.supplier === state.selectedSupplier);
  }
}

function renderSearchMatches() {
  const matches = getSearchMatches();

  if (!state.selectedSupplier) {
    elements.searchMatches.innerHTML = '<p class="muted">Primero selecciona un proveedor.</p>';
    elements.productSearch.disabled = true;
    return;
  }

  elements.productSearch.disabled = false;

  if (!state.searchTerm) {
    elements.searchMatches.innerHTML = "";
    return;
  }

  if (matches.length === 0) {
    elements.searchMatches.innerHTML = '<p class="muted">No hay coincidencias para ese proveedor.</p>';
    return;
  }

  elements.searchMatches.innerHTML = matches
    .map(
      (product) => `
        <button type="button" class="suggestion-btn" data-action="add-product" data-product-id="${product.id}">
          ${escapeHtml(product.name)}
        </button>
      `
    )
    .join("");
}

function renderOrderLines() {
  if (state.lines.length === 0) {
    elements.orderLinesBody.innerHTML =
      '<tr class="empty-row"><td colspan="4" class="muted center">Aún no has seleccionado productos.</td></tr>';
    elements.itemsCount.textContent = "0 líneas";
    syncEditorButtons();
    return;
  }

  elements.orderLinesBody.innerHTML = state.lines
    .map((line, index) => {
      const invalidQty = !line.quantity || line.quantity <= 0;
      return `
        <tr class="${invalidQty ? "line-invalid" : ""}">
          <td data-label="Cantidad">
            <input
              type="number"
              min="0.01"
              step="0.01"
              value="${invalidQty ? "" : line.quantity}"
              data-action="qty"
              data-index="${index}"
            />
          </td>
          <td data-label="Producto"><strong>${escapeHtml(line.name)}</strong></td>
          <td data-label="Notas">
            <input
              type="text"
              placeholder="Nota de línea"
              value="${escapeHtml(line.note || "")}" 
              data-action="note"
              data-index="${index}"
            />
          </td>
          <td data-label="Acción">
            <button type="button" class="remove-btn" data-action="remove-line" data-index="${index}">Quitar</button>
          </td>
        </tr>
      `;
    })
    .join("");

  elements.itemsCount.textContent = `${state.lines.length} líneas`;
  syncEditorButtons();
}

function renderPreview() {
  if (!state.selectedSupplier) {
    elements.previewContainer.innerHTML = '<p class="muted">Selecciona un proveedor para iniciar la orden.</p>';
    return;
  }

  const orderDate = formatOrderDate(new Date());
  const orderNumber = String(state.editingOrderId || 0).padStart(4, "0");
  const supplierProfile = getSupplierProfile(state.selectedSupplier);
  const notesText = elements.generalNotes.value.trim();
  const notesHtml = notesText ? escapeHtml(notesText).replaceAll("\n", "<br>") : "Sin notas generales.";
  const rowsHtml =
    state.lines.length === 0
      ? `
        <tr class="empty-row">
          <td data-label="Cantidad"></td>
          <td data-label="Productos">Sin productos seleccionados.</td>
          <td data-label="Notas"></td>
        </tr>
      `
      : state.lines
          .map(
            (line) => `
              <tr>
                <td data-label="Cantidad">${line.quantity > 0 ? line.quantity : ""}</td>
                <td data-label="Productos">${escapeHtml(line.name)}</td>
                <td data-label="Notas">${escapeHtml(line.note || "")}</td>
              </tr>
            `
          )
          .join("");

  elements.previewContainer.innerHTML = `
    <article class="preview-doc">
      <header class="preview-top">
        <div class="preview-ticket">
          <p><strong>Pedido #:</strong> ${escapeHtml(orderNumber)}</p>
          <p><strong>Fecha:</strong> ${escapeHtml(orderDate)}</p>
        </div>
        <h3 class="preview-form-title">Formulario de Pedidos</h3>
        <img src="${PREVIEW_LOGO}" alt="Logo ${escapeHtml(BUSINESS_NAME)}" class="preview-form-logo" />
      </header>

      <section class="preview-cards">
        <article class="preview-card">
          <h4>Datos del Negocio</h4>
          <p><strong>Nombre:</strong> ${escapeHtml(BUSINESS_NAME)}</p>
          <p><strong>N° de contacto:</strong> ${escapeHtml(BUSINESS_PHONE)}</p>
          <p><strong>Dirección:</strong> ${escapeHtml(BUSINESS_ADDRESS)}</p>
        </article>
        <article class="preview-card">
          <h4>Datos del Proveedor</h4>
          <p><strong>Nombre:</strong> ${escapeHtml(supplierProfile.display_name)}</p>
          <p><strong>N° de contacto:</strong> ${escapeHtml(supplierProfile.contact)}</p>
          <p><strong>Dirección:</strong> ${escapeHtml(supplierProfile.address)}</p>
        </article>
      </section>

      <section class="preview-table-wrap">
        <table class="preview-table">
          <thead>
            <tr>
              <th>Cantidad</th>
              <th>Productos</th>
              <th>Notas</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </section>

      <section class="preview-notes-box">
        <h4>Notas generales</h4>
        <p>${notesHtml}</p>
      </section>
    </article>
  `;
}

function renderOrders() {
  if (state.orders.length === 0) {
    elements.ordersHistory.innerHTML = '<p class="muted">No hay pedidos guardados todavía.</p>';
    return;
  }

  elements.ordersHistory.innerHTML = state.orders
    .map((order) => {
      const createdDate = new Date(order.created_at);
      const when = Number.isNaN(createdDate.getTime())
        ? order.created_at
        : createdDate.toLocaleString("es-SV", {
            dateStyle: "short",
            timeStyle: "short",
          });

      return `
        <article class="history-item">
          <div>
            <p><strong>Pedido #${order.id}</strong> · ${escapeHtml(order.supplier_name)}</p>
            <p>${escapeHtml(order.employee_name)} · ${escapeHtml(when)} · ${order.item_count} líneas</p>
          </div>
          <div class="history-actions">
            <details class="export-dropdown">
              <summary class="ghost-btn action-btn">Exportar</summary>
              <div class="export-dropdown-menu">
                <button type="button" class="ghost-btn action-btn" data-action="export-pdf" data-order-id="${order.id}">PDF</button>
                <button type="button" class="ghost-btn action-btn" data-action="export-jpg" data-order-id="${order.id}">JPG</button>
              </div>
            </details>
            <button type="button" class="ghost-btn action-btn" data-action="edit-order" data-order-id="${order.id}">Editar</button>
            <button type="button" class="danger-btn action-btn" data-action="delete-order" data-order-id="${order.id}">Borrar</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function addProductToLines(productId) {
  const product = getProductById(productId);
  if (!product) {
    return;
  }

  const existing = state.lines.find((line) => line.product_id === product.id);
  if (existing) {
    existing.quantity = round((existing.quantity || 0) + 1);
    return;
  }

  state.lines.push({
    product_id: product.id,
    name: product.name,
    quantity: 1,
    note: "",
  });
}

async function handleHistoryAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }

  const action = button.dataset.action;
  const orderId = Number(button.dataset.orderId);

  if (action === "export-pdf") {
    window.open(`/api/orders/${orderId}/export.pdf`, "_blank", "noopener");
    return;
  }

  if (action === "export-jpg") {
    window.open(`/api/orders/${orderId}/export.jpg`, "_blank", "noopener");
    return;
  }

  if (action === "edit-order") {
    closeHistoryModal();
    await loadOrderForEdit(orderId);
    return;
  }

  if (action === "delete-order") {
    await removeOrder(orderId);
  }
}

async function loadOrderForEdit(orderId) {
  try {
    const response = await fetch(`/api/orders/${orderId}`);
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      const body = await response.json();
      throw new Error(body.detail || "No se pudo cargar el pedido.");
    }

    const detail = await response.json();
    state.editingOrderId = detail.id;
    state.selectedSupplier = detail.supplier_name;
    state.lines = detail.items.map((item) => ({
      product_id: item.product_id,
      name: item.product_name,
      quantity: item.quantity,
      note: item.note || "",
    }));

    state.searchTerm = "";
    elements.productSearch.value = "";
    elements.productSearch.disabled = false;
    elements.generalNotes.value = detail.notes || "";

    renderSupplierSelection();
    renderSearchMatches();
    renderOrderLines();
    renderPreview();
    syncEditorButtons();

    window.scrollTo({ top: 0, behavior: "smooth" });
    showFlash(`Editando pedido #${orderId}`);
  } catch (error) {
    showFlash(error.message || "Error cargando pedido.", true);
  }
}

async function removeOrder(orderId) {
  const confirmation = window.confirm(`¿Seguro que deseas borrar el pedido #${orderId}?`);
  if (!confirmation) {
    return;
  }

  try {
    const response = await fetch(`/api/orders/${orderId}`, { method: "DELETE" });
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      const body = await response.json();
      throw new Error(body.detail || "No se pudo borrar el pedido.");
    }

    if (state.editingOrderId === orderId) {
      clearEditor(true);
    }

    await loadOrders();
    showFlash(`Pedido #${orderId} eliminado.`);
  } catch (error) {
    showFlash(error.message || "Error borrando pedido.", true);
  }
}

function clearEditor(keepSupplier = false) {
  state.editingOrderId = null;
  state.lines = [];
  elements.generalNotes.value = "";

  if (!keepSupplier) {
    state.selectedSupplier = "";
    state.searchTerm = "";
    elements.productSearch.value = "";
    elements.productSearch.disabled = true;
  }

  renderSupplierSelection();
  renderSearchMatches();
  renderOrderLines();
  renderPreview();
  syncEditorButtons();
}

async function loadProducts() {
  try {
    const response = await fetch("/api/products");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      throw new Error("No se pudo cargar el catálogo.");
    }

    state.products = await response.json();
  } catch (error) {
    showFlash(error.message || "Error cargando productos.", true);
  }
}

async function loadOrders() {
  try {
    const response = await fetch("/api/orders");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      throw new Error("No se pudo cargar el historial.");
    }

    state.orders = await response.json();
    renderOrders();
  } catch (error) {
    showFlash(error.message || "Error cargando historial.", true);
  }
}

async function handleOrderSubmit(event) {
  event.preventDefault();

  if (!state.selectedSupplier) {
    showFlash("Selecciona un proveedor.", true);
    return;
  }

  if (state.lines.length === 0) {
    showFlash("Agrega al menos un producto.", true);
    return;
  }

  const hasInvalidQty = state.lines.some((line) => !line.quantity || Number(line.quantity) <= 0);
  if (hasInvalidQty) {
    showFlash("Hay líneas con cantidad vacía o inválida. Corrige antes de guardar.", true);
    return;
  }

  const items = state.lines.map((line) => ({
    product_id: line.product_id,
    quantity: line.quantity,
    note: line.note,
  }));

  const payload = {
    supplier_name: state.selectedSupplier,
    notes: elements.generalNotes.value.trim(),
    items,
  };

  const isEditing = Boolean(state.editingOrderId);
  const url = isEditing ? `/api/orders/${state.editingOrderId}` : "/api/orders";
  const method = isEditing ? "PUT" : "POST";

  elements.saveOrderBtn.disabled = true;
  elements.saveOrderBtn.textContent = "Guardando...";

  try {
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }

    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail || "No se pudo guardar el pedido.");
    }

    state.editingOrderId = null;
    state.lines = [];
    elements.generalNotes.value = "";

    renderOrderLines();
    renderPreview();
    syncEditorButtons();
    await loadOrders();

    showFlash(isEditing ? `Pedido #${body.order_id} actualizado.` : `Pedido #${body.order_id} guardado correctamente.`);
  } catch (error) {
    showFlash(error.message || "Error guardando pedido.", true);
  } finally {
    elements.saveOrderBtn.disabled = false;
    syncEditorButtons();
  }
}

function showFlash(message, isError = false) {
  elements.flash.textContent = message;
  elements.flash.classList.remove("error", "show");

  if (isError) {
    elements.flash.classList.add("error");
  }

  elements.flash.classList.add("show");
  setTimeout(() => elements.flash.classList.remove("show"), 2400);
}

function formatOrderDate(date) {
  return date.toLocaleString("es-SV", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function getSupplierProfile(supplierName) {
  const normalized = String(supplierName || "").trim();
  const profile = SUPPLIER_DIRECTORY[normalized];
  if (!profile) {
    return {
      display_name: normalized || "-",
      contact: "-",
      address: "-",
    };
  }

  return {
    display_name: profile.display_name || normalized || "-",
    contact: profile.contact || "-",
    address: profile.address || "-",
  };
}

function round(value) {
  return Math.round(value * 100) / 100;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
