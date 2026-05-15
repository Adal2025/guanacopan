const customerOrdersState = {
  orders: [],
  selectedOrderId: null,
  selectedPhone: "",
  chatPollTimer: null,
  orderPollTimer: null,
  isChatPolling: false,
  isOrderPolling: false,
  hasLoadedOrders: false,
  knownOrderIds: new Set(),
  unseenOrderIds: new Set(),
};

const WHATSAPP_COVER_MESSAGE = "Bienvenido a GuanacoPan";
const BUSINESS_LOGO = "/static/logo-gpf.jpg";

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
  customerOrderElements.refreshBtn.addEventListener("click", () => {
    requestNotificationPermission();
    loadCustomerOrders();
  });
  customerOrderElements.list.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-order-id]");
    if (!button) {
      return;
    }
    const orderId = Number(button.dataset.orderId);
    customerOrdersState.unseenOrderIds.delete(orderId);
    await loadCustomerOrderDetail(orderId);
  });
  customerOrderElements.detail.addEventListener("submit", handleCustomerChatSubmit);
  customerOrderElements.detail.addEventListener("click", handleCustomerChatAction);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopCustomerChatPolling();
      return;
    }
    startCustomerChatPolling();
    loadCustomerOrders({ silent: true });
  });
  loadCustomerOrders();
  startCustomerOrderPolling();
}

async function loadCustomerOrders(options = {}) {
  try {
    const response = await fetch("/api/customer-orders");
    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }
    if (!response.ok) {
      throw new Error("No se pudieron cargar los pedidos.");
    }

    const orders = await response.json();
    const incomingIds = new Set(orders.map((order) => Number(order.id)));
    const newOrders = orders.filter((order) => !customerOrdersState.knownOrderIds.has(Number(order.id)));
    if (customerOrdersState.hasLoadedOrders && newOrders.length > 0) {
      for (const order of newOrders) {
        customerOrdersState.unseenOrderIds.add(Number(order.id));
      }
      notifyNewCustomerOrders(newOrders);
    }

    customerOrdersState.orders = orders;
    customerOrdersState.knownOrderIds = incomingIds;
    customerOrdersState.hasLoadedOrders = true;
    renderCustomerOrders();

    if (customerOrdersState.selectedOrderId && !options.silent) {
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

function startCustomerOrderPolling() {
  stopCustomerOrderPolling();
  customerOrdersState.orderPollTimer = window.setInterval(async () => {
    if (customerOrdersState.isOrderPolling) {
      return;
    }

    customerOrdersState.isOrderPolling = true;
    try {
      await loadCustomerOrders({ silent: true });
    } finally {
      customerOrdersState.isOrderPolling = false;
    }
  }, 5000);
}

function stopCustomerOrderPolling() {
  if (customerOrdersState.orderPollTimer) {
    window.clearInterval(customerOrdersState.orderPollTimer);
    customerOrdersState.orderPollTimer = null;
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
      const isNew = customerOrdersState.unseenOrderIds.has(Number(order.id));
      return `
        <button type="button" class="customer-order-card ${isActive ? "active" : ""} ${isNew ? "new" : ""}" data-order-id="${order.id}">
          <span class="customer-order-card-top">
            <strong>Pedido #${order.id}</strong>
            <span>${formatMoney(order.total)}</span>
          </span>
          ${isNew ? '<span class="new-order-pill">Nuevo</span>' : ""}
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
        <div class="customer-bot-actions" aria-label="Acciones rápidas del bot">
          <button type="button" class="ghost-btn" data-action="bot-initial">Inicio</button>
          <button type="button" class="ghost-btn" data-action="bot-order">Ordenar</button>
          <button type="button" class="ghost-btn" data-action="send-menu">Menú</button>
          <button type="button" class="ghost-btn" data-action="bot-promotions">Promos</button>
          <button type="button" class="ghost-btn" data-action="bot-location">Ubicación</button>
          <button type="button" class="ghost-btn" data-action="bot-unavailable">Sin stock + menú</button>
        </div>
        <div class="customer-chat-actions">
          <button type="button" class="ghost-btn confirm-order-btn" data-action="confirm-order">Confirmar pedido</button>
          <span class="customer-chat-actions-right">
            <button type="button" class="ghost-btn" data-action="resume-bot">Reanudar bot</button>
            <button type="submit">Enviar respuesta</button>
          </span>
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
      const internal = message.direction === "internal" || message.sender === "internal";
      const sender = internal ? "Orden interna" : message.sender === "bot" ? "Bot" : message.sender.startsWith("staff:") ? "Equipo" : "Cliente";
      if (message.sender === "bot" && message.body.includes(WHATSAPP_COVER_MESSAGE)) {
        return renderWhatsAppCoverMessage(message, sender, outbound, internal);
      }
      return `
        <article class="customer-chat-message ${outbound ? "outbound" : "inbound"} ${internal ? "internal" : ""} ${message.sent_ok ? "" : "failed"}">
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

function renderWhatsAppCoverMessage(message, sender, outbound, internal) {
  return `
    <article class="customer-chat-message customer-chat-cover ${outbound ? "outbound" : "inbound"} ${internal ? "internal" : ""} ${message.sent_ok ? "" : "failed"}">
      <div class="whatsapp-cover-card">
        <div class="whatsapp-cover-hero">
          <img src="${BUSINESS_LOGO}" alt="Logo GuanacoPan" />
          <div>
            <strong>GuanacoPan</strong>
            <span>El pan que nos une.</span>
          </div>
        </div>
        <div class="whatsapp-cover-copy">
          <strong>Bienvenido a GuanacoPan</strong>
          <p>El pan que nos une.</p>
          <p>¿Qué deseas hacer?</p>
          <ol>
            <li>Ordenar ahora</li>
            <li>Ver menú</li>
            <li>Promociones</li>
            <li>Ubicación</li>
            <li>Hablar con alguien</li>
          </ol>
        </div>
        <div class="whatsapp-cover-cta">Ordenar ahora</div>
      </div>
      <span>${escapeHtml(sender)} · ${escapeHtml(formatDate(message.created_at))}${message.sent_ok ? "" : " · No enviado"}</span>
    </article>
  `;
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
  if (!button) {
    return;
  }

  try {
    let response;
    if (button.dataset.action === "resume-bot") {
      response = await fetch(`/api/whatsapp/conversations/${encodeURIComponent(customerOrdersState.selectedPhone)}/resume-bot`, {
        method: "POST",
      });
    } else if (button.dataset.action === "confirm-order") {
      response = await sendCustomerOrderConfirmation();
    } else if (button.dataset.action === "send-menu" || button.dataset.action.startsWith("bot-")) {
      const botAction = getBotActionName(button.dataset.action);
      response = await fetch(`/api/customer-orders/${encodeURIComponent(customerOrdersState.selectedOrderId)}/bot-actions/${encodeURIComponent(botAction)}`, {
        method: "POST",
      });
    } else {
      return;
    }
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.detail || "No se pudo completar la acción.");
    }

    await loadCustomerConversation(customerOrdersState.selectedPhone);
    showFlash(getActionSuccessMessage(button.dataset.action));
  } catch (error) {
    showFlash(error.message || "Error actualizando el chat.", true);
  }
}

async function sendCustomerOrderConfirmation() {
  const input = document.getElementById("customerChatMessage");
  const estimate = input.value.trim();
  const message = estimate
    ? `Pedido confirmado ✅\n\nTiempo estimado: ${estimate}\nEspera aproximada: 15 a 20 minutos.\n\nGracias por ordenar en GuanacoPan.`
    : "Pedido confirmado ✅\n\nEspera aproximada: 15 a 20 minutos.\nEstamos preparando tu orden y te avisaremos por este chat cuando esté lista.\n\nGracias por ordenar en GuanacoPan.";

  const response = await fetch(`/api/whatsapp/conversations/${encodeURIComponent(customerOrdersState.selectedPhone)}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (response.ok && input) {
    input.value = "";
    await fetch(`/api/whatsapp/conversations/${encodeURIComponent(customerOrdersState.selectedPhone)}/resume-bot`, {
      method: "POST",
    });
  }
  return response;
}

function getActionSuccessMessage(action) {
  if (action === "resume-bot") {
    return "Bot reanudado para este cliente.";
  }
  if (action === "confirm-order") {
    return "Pedido confirmado al cliente.";
  }
  return "Mensaje del bot enviado.";
}

function getBotActionName(action) {
  const actions = {
    "send-menu": "menu",
    "bot-initial": "initial",
    "bot-order": "order",
    "bot-promotions": "promotions",
    "bot-location": "location",
    "bot-unavailable": "unavailable",
  };
  return actions[action] || "menu";
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

function notifyNewCustomerOrders(newOrders) {
  const count = newOrders.length;
  const message = count === 1 ? `Nuevo pedido #${newOrders[0].id}` : `${count} pedidos nuevos`;
  showFlash(message);
  playOrderNotificationSound();

  const originalTitle = document.title;
  document.title = `(${count}) ${message}`;
  window.setTimeout(() => {
    document.title = originalTitle;
  }, 6000);

  if ("Notification" in window && Notification.permission === "granted") {
    const order = newOrders[0];
    new Notification(message, {
      body: `${order.customer_name || "Cliente WhatsApp"} · ${formatMoney(order.total)}`,
    });
  }
}

function requestNotificationPermission() {
  if (!("Notification" in window) || Notification.permission !== "default") {
    return;
  }
  Notification.requestPermission().catch(() => {});
}

function playOrderNotificationSound() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) {
    return;
  }

  try {
    const audioContext = new AudioContext();
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(880, audioContext.currentTime);
    gain.gain.setValueAtTime(0.001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.08, audioContext.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.32);
    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.34);
  } catch (error) {
    // Some browsers block audio until the user interacts with the page.
  }
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
