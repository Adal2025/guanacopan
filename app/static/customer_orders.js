const customerOrdersState = {
  orders: [],
  selectedOrderId: null,
  selectedPhone: "",
  chatPollTimer: null,
  isChatPolling: false,
};

const customerOrderElements = {
  refreshBtn: document.getElementById("refreshCustomerOrdersBtn"),
  count: document.getElementById("customerOrdersCount"),
  list: document.getElementById("customerOrdersList"),
  detail: document.getElementById("customerOrderDetail"),
  status: document.getElementById("customerOrderStatus"),
  flash: document.getElementById("flash"),
};

document.addEventListener("DOMContentLoaded", initCustomerOrders);

function initCustomerOrders() {
  customerOrderElements.refreshBtn.addEventListener("click", loadCustomerOrders);
  customerOrderElements.list.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-order-id]");
    if (!button) {
      return;
    }
    await loadCustomerOrderDetail(Number(button.dataset.orderId));
  });
  customerOrderElements.detail.addEventListener("submit", handleCustomerChatSubmit);
  customerOrderElements.detail.addEventListener("click", handleCustomerChatAction);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopCustomerChatPolling();
      return;
    }
    startCustomerChatPolling();
  });
  loadCustomerOrders();
}

async function loadCustomerOrders() {
  try {
    const response = await fetch("/api/customer-orders");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      throw new Error("No se pudieron cargar los pedidos.");
    }

    customerOrdersState.orders = await response.json();
    renderCustomerOrders();

    if (customerOrdersState.selectedOrderId) {
      await loadCustomerOrderDetail(customerOrdersState.selectedOrderId, false);
    }
  } catch (error) {
    showFlash(error.message || "Error cargando pedidos.", true);
  }
}

async function loadCustomerOrderDetail(orderId, showLoading = true) {
  customerOrdersState.selectedOrderId = orderId;
  renderCustomerOrders();

  if (showLoading) {
    customerOrderElements.detail.innerHTML = '<p class="muted">Cargando pedido...</p>';
  }

  try {
    const response = await fetch(`/api/customer-orders/${orderId}`);
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      const body = await response.json();
      throw new Error(body.detail || "No se pudo cargar el detalle.");
    }

    const order = await response.json();
    customerOrdersState.selectedPhone = order.customer_phone || "";
    renderCustomerOrderDetail(order);
    await loadCustomerConversation(order.customer_phone);
    startCustomerChatPolling();
  } catch (error) {
    showFlash(error.message || "Error cargando detalle.", true);
  }
}

async function loadCustomerConversation(phone, options = {}) {
  if (!phone) {
    return;
  }

  const log = document.getElementById("customerChatLog");
  const status = document.getElementById("customerChatStatus");
  if (log && !options.silent) {
    log.innerHTML = '<p class="muted">Cargando conversación...</p>';
  }

  try {
    const response = await fetch(`/api/whatsapp/conversations/${encodeURIComponent(phone)}/messages`);
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      throw new Error("No se pudo cargar la conversación.");
    }

    const payload = await response.json();
    renderCustomerConversation(payload);
    if (status) {
      status.textContent = getConversationStatusLabel(payload.conversation.status);
    }
  } catch (error) {
    showFlash(error.message || "Error cargando conversación.", true);
  }
}

function startCustomerChatPolling() {
  stopCustomerChatPolling();
  if (!customerOrdersState.selectedPhone || document.hidden) {
    return;
  }

  customerOrdersState.chatPollTimer = window.setInterval(async () => {
    if (customerOrdersState.isChatPolling || !customerOrdersState.selectedPhone) {
      return;
    }

    customerOrdersState.isChatPolling = true;
    try {
      await loadCustomerConversation(customerOrdersState.selectedPhone, { silent: true });
    } finally {
      customerOrdersState.isChatPolling = false;
    }
  }, 4000);
}

function stopCustomerChatPolling() {
  if (customerOrdersState.chatPollTimer) {
    window.clearInterval(customerOrdersState.chatPollTimer);
    customerOrdersState.chatPollTimer = null;
  }
}

function renderCustomerOrders() {
  const orders = customerOrdersState.orders;
  customerOrderElements.count.textContent = `${orders.length} ${orders.length === 1 ? "pedido" : "pedidos"}`;

  if (orders.length === 0) {
    customerOrderElements.list.innerHTML = '<p class="muted">Aún no hay pedidos de clientes.</p>';
    customerOrderElements.status.textContent = "Sin pedidos";
    return;
  }

  customerOrderElements.list.innerHTML = orders
    .map((order) => {
      const isActive = Number(order.id) === Number(customerOrdersState.selectedOrderId);
      return `
        <button type="button" class="customer-order-card ${isActive ? "active" : ""}" data-order-id="${order.id}">
          <span class="customer-order-card-top">
            <strong>Pedido #${order.id}</strong>
            <span>${formatMoney(order.total)}</span>
          </span>
          <span>${escapeHtml(order.customer_name || "Cliente WhatsApp")} · ${escapeHtml(order.city)}</span>
          <span>${escapeHtml(formatDate(order.created_at))} · ${order.item_count} ${Number(order.item_count) === 1 ? "línea" : "líneas"}</span>
          <span>${escapeHtml(order.customer_phone)}</span>
        </button>
      `;
    })
    .join("");
}

function renderCustomerOrderDetail(order) {
  customerOrderElements.status.textContent = `Pedido #${order.id}`;

  const rows = order.items
    .map(
      (item) => `
        <tr>
          <td>${escapeHtml(item.quantity)}</td>
          <td>
            <strong>${escapeHtml(item.item_name)}</strong>
            <span class="customer-item-sku">${escapeHtml(item.item_sku)}</span>
          </td>
          <td>${formatMoney(item.unit_price)}</td>
          <td>${formatMoney(item.line_total)}</td>
        </tr>
      `
    )
    .join("");

  customerOrderElements.detail.innerHTML = `
    <section class="customer-order-summary">
      <div>
        <span>Cliente</span>
        <strong>${escapeHtml(order.customer_name || "Cliente WhatsApp")}</strong>
      </div>
      <div>
        <span>Teléfono</span>
        <strong>${escapeHtml(order.customer_phone)}</strong>
      </div>
      <div>
        <span>Ciudad</span>
        <strong>${escapeHtml(order.city)}</strong>
      </div>
      <div>
        <span>Fecha</span>
        <strong>${escapeHtml(formatDate(order.created_at))}</strong>
      </div>
    </section>

    <div class="table-wrap customer-detail-table-wrap">
      <table class="customer-detail-table">
        <thead>
          <tr>
            <th>Cant.</th>
            <th>Producto</th>
            <th>Precio</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>

    <section class="customer-order-total">
      <span>Total del pedido</span>
      <strong>${formatMoney(order.total)}</strong>
    </section>

    <section class="preview-notes-box">
      <h4>Notas</h4>
      <p>${escapeHtml(order.notes || "Sin notas.")}</p>
    </section>

    <section class="customer-chat-panel">
      <div class="customer-orders-head">
        <h2>WhatsApp del cliente</h2>
        <span id="customerChatStatus" class="badge">Cargando</span>
      </div>
      <div id="customerChatLog" class="customer-chat-log">
        <p class="muted">Cargando conversación...</p>
      </div>
      <form id="customerChatForm" class="customer-chat-form">
        <textarea id="customerChatMessage" rows="3" placeholder="Escribir respuesta para el cliente"></textarea>
        <div class="customer-chat-actions">
          <button type="button" class="ghost-btn" data-action="resume-bot">Reanudar bot</button>
          <button type="submit">Enviar respuesta</button>
        </div>
      </form>
    </section>
  `;
}

function renderCustomerConversation(payload) {
  const log = document.getElementById("customerChatLog");
  if (!log) {
    return;
  }

  const messages = payload.messages || [];
  const shouldStickToBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 80;
  if (messages.length === 0) {
    log.innerHTML = '<p class="muted">No hay mensajes guardados para este cliente todavía.</p>';
    return;
  }

  log.innerHTML = messages
    .map((message) => {
      const outbound = message.direction === "outbound";
      const sender = message.sender === "bot" ? "Bot" : message.sender.startsWith("staff:") ? "Equipo" : "Cliente";
      return `
        <article class="customer-chat-message ${outbound ? "outbound" : "inbound"} ${message.sent_ok ? "" : "failed"}">
          <p>${escapeHtml(message.body).replaceAll("\n", "<br>")}</p>
          <span>${escapeHtml(sender)} · ${escapeHtml(formatDate(message.created_at))}${message.sent_ok ? "" : " · No enviado"}</span>
        </article>
      `;
    })
    .join("");
  if (shouldStickToBottom) {
    log.scrollTop = log.scrollHeight;
  }
}

async function handleCustomerChatSubmit(event) {
  if (event.target.id !== "customerChatForm") {
    return;
  }
  event.preventDefault();

  const input = document.getElementById("customerChatMessage");
  const message = input.value.trim();
  if (!message) {
    showFlash("Escribe una respuesta antes de enviar.", true);
    return;
  }

  try {
    const response = await fetch(`/api/whatsapp/conversations/${encodeURIComponent(customerOrdersState.selectedPhone)}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail || "No se pudo enviar la respuesta.");
    }

    input.value = "";
    await loadCustomerConversation(customerOrdersState.selectedPhone);
    showFlash("Respuesta enviada.");
  } catch (error) {
    showFlash(error.message || "Error enviando respuesta.", true);
  }
}

async function handleCustomerChatAction(event) {
  const button = event.target.closest("button[data-action]");
  if (!button || button.dataset.action !== "resume-bot") {
    return;
  }

  try {
    const response = await fetch(`/api/whatsapp/conversations/${encodeURIComponent(customerOrdersState.selectedPhone)}/resume-bot`, {
      method: "POST",
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail || "No se pudo reanudar el bot.");
    }

    await loadCustomerConversation(customerOrdersState.selectedPhone);
    showFlash("Bot reanudado para este cliente.");
  } catch (error) {
    showFlash(error.message || "Error reanudando bot.", true);
  }
}

function getConversationStatusLabel(status) {
  if (status === "attention") {
    return "Necesita atención";
  }
  if (status === "human") {
    return "Atención humana";
  }
  return "Bot activo";
}

function formatMoney(value) {
  const number = Number(value || 0);
  return number.toLocaleString("es-SV", {
    style: "currency",
    currency: "USD",
  });
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value || "";
  }
  return date.toLocaleString("es-SV", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function showFlash(message, isError = false) {
  customerOrderElements.flash.textContent = message;
  customerOrderElements.flash.classList.remove("error", "show");

  if (isError) {
    customerOrderElements.flash.classList.add("error");
  }

  customerOrderElements.flash.classList.add("show");
  setTimeout(() => customerOrderElements.flash.classList.remove("show"), 2400);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
