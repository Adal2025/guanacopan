from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
import urllib.error
import urllib.request
from difflib import SequenceMatcher
from typing import Any, TypeAlias

from app.database import (
    create_customer_order,
    delete_whatsapp_session,
    get_whatsapp_conversation,
    get_whatsapp_session,
    save_whatsapp_session,
    set_whatsapp_conversation_status,
    update_customer_order_items,
)

GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v25.0")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
logger = logging.getLogger(__name__)
WhatsAppReply: TypeAlias = str | dict[str, Any]

SUPPORTED_CITY = "San Miguel"

MENU_CATEGORIES = (
    ("desayunos", "Desayunos 6:00 AM a 9:00 AM"),
    ("panes", "Panes disponibles todo el dia"),
    ("extras", "Extras y complementos"),
    ("bebidas", "Bebidas"),
)

MENU_ITEMS = (
    {"sku": "DES-001", "category": "desayunos", "name": "Panfri", "price": 1.25},
    {"sku": "DES-002", "category": "desayunos", "name": "Companeros", "price": 1.50},
    {"sku": "DES-003", "category": "desayunos", "name": "Jamuevo", "price": 1.99},
    {"sku": "DES-004", "category": "desayunos", "name": "El Mananero", "price": 1.50},
    {"sku": "DES-005", "category": "desayunos", "name": "Panpollo", "price": 2.99},
    {"sku": "DES-006", "category": "desayunos", "name": "Panchori", "price": 1.99},
    {"sku": "PAN-001", "category": "panes", "name": "Senor Bistec", "price": 6.99},
    {"sku": "PAN-002", "category": "panes", "name": "Senora Milanesa", "price": 6.99},
    {"sku": "PAN-003", "category": "panes", "name": "El Tropicalito", "price": 5.50},
    {"sku": "PAN-004", "category": "panes", "name": "Guanacoburger", "price": 6.99},
    {"sku": "PAN-005", "category": "panes", "name": "Pansalchi", "price": 1.99},
    {"sku": "PAN-006", "category": "panes", "name": "El Pibe", "price": 3.99},
    {"sku": "PAN-007", "category": "panes", "name": "Jamancito", "price": 2.99},
    {"sku": "PAN-008", "category": "panes", "name": "Salchiloco", "price": 3.99},
    {"sku": "PAN-009", "category": "panes", "name": "Jamorty", "price": 3.99},
    {"sku": "PAN-010", "category": "panes", "name": "El Criollo", "price": 3.99},
    {"sku": "PAN-011", "category": "panes", "name": "Steak Sandwich", "price": 6.99},
    {"sku": "EXT-001", "category": "extras", "name": "Nachos Guanacos", "price": 2.99},
    {"sku": "EXT-002", "category": "extras", "name": "Nachos Premium", "price": 5.50},
    {"sku": "EXT-003", "category": "extras", "name": "Alitas Asadas 4 unidades", "price": 5.50},
    {"sku": "EXT-004", "category": "extras", "name": "Alitas Asadas 8 unidades", "price": 9.99},
    {"sku": "EXT-005", "category": "extras", "name": "Alitas Asadas 12 unidades", "price": 14.99},
    {"sku": "EXT-006", "category": "extras", "name": "Papas Fritas 4 onzas", "price": 1.50},
    {"sku": "EXT-007", "category": "extras", "name": "Papas Fritas 6 onzas", "price": 2.00},
    {"sku": "EXT-008", "category": "extras", "name": "Papas Fritas 8 onzas", "price": 3.00},
)

WELCOME_TEXT = (
    "Hola, bienvenido a Guanacopan Frances.\n\n"
    "Para iniciar tu pedido, elige tu ciudad:\n"
    "1. San Miguel"
)

HELP_TEXT = (
    "Comandos disponibles:\n"
    "- menu: ver categorias\n"
    "- ver: revisar tu pedido\n"
    "- agregar: agregar otro producto\n"
    "- confirmar: guardar el pedido\n"
    "- cancelar: borrar este pedido en curso"
)

HUMAN_HELP_KEYWORDS = {
    "asesor",
    "ayuda",
    "humano",
    "persona",
    "atencion",
    "atencion humana",
    "hablar con alguien",
    "quiero hablar con alguien",
}


def _post_whatsapp_payload(to_phone: str, payload: dict[str, Any]) -> bool:
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.error(
            "WhatsApp send skipped: missing env vars phone_number_id=%s access_token=%s",
            "set" if WHATSAPP_PHONE_NUMBER_ID else "missing",
            "set" if WHATSAPP_ACCESS_TOKEN else "missing",
        )
        return False

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            ok = 200 <= response.status < 300
            logger.info("WhatsApp send response status=%s to=%s", response.status, to_phone)
            return ok
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8", errors="replace")
        logger.error(
            "WhatsApp send failed status=%s to=%s body=%s",
            err.code,
            to_phone,
            error_body[:1200],
        )
        return False
    except (urllib.error.URLError, TimeoutError) as err:
        logger.error("WhatsApp send failed to=%s error=%s", to_phone, err)
        return False


def send_whatsapp_text(to_phone: str, body: str) -> bool:
    return _post_whatsapp_payload(to_phone, _text_payload(to_phone, body))


def send_whatsapp_reply(to_phone: str, reply: WhatsAppReply) -> bool:
    if isinstance(reply, str):
        return send_whatsapp_text(to_phone, reply)
    payload = dict(reply.get("payload") or {})
    if not payload:
        return send_whatsapp_text(to_phone, whatsapp_reply_body(reply))
    return _post_whatsapp_payload(to_phone, payload)


def whatsapp_reply_body(reply: WhatsAppReply) -> str:
    if isinstance(reply, str):
        return reply
    return str(reply.get("body") or "")


def _text_payload(to_phone: str, body: str) -> dict[str, Any]:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": body[:4000]},
    }


def _button_reply(to_phone: str, body: str, buttons: list[tuple[str, str]]) -> dict[str, Any]:
    safe_buttons = [
        {
            "type": "reply",
            "reply": {"id": str(button_id)[:256], "title": str(title)[:20]},
        }
        for button_id, title in buttons[:3]
    ]
    return {
        "body": body,
        "payload": {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body[:1024]},
                "action": {"buttons": safe_buttons},
            },
        },
    }


def _list_reply(
    to_phone: str,
    body: str,
    button: str,
    section_title: str,
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    safe_rows = [
        {
            "id": str(row["id"])[:200],
            "title": str(row["title"])[:24],
            **({"description": str(row["description"])[:72]} if row.get("description") else {}),
        }
        for row in rows[:10]
    ]
    return {
        "body": body,
        "payload": {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": body[:1024]},
                "action": {
                    "button": button[:20],
                    "sections": [{"title": section_title[:24], "rows": safe_rows}],
                },
            },
        },
    }


def build_whatsapp_category_reply(to_phone: str) -> WhatsAppReply:
    rows = [
        {"id": category, "title": label[:24]}
        for category, label in MENU_CATEGORIES
    ]
    return _list_reply(to_phone, "Elige una categoria del menu:", "Ver categorias", "Menu", rows)


def handle_customer_message(db_path: str, phone: str, customer_name: str, incoming_text: str) -> list[WhatsAppReply]:
    text = incoming_text.strip()
    normalized = _normalize(text)
    session = get_whatsapp_session(db_path, phone)
    state = session["state"] if session else _new_state()
    stored_name = customer_name or (session["customer_name"] if session else "")
    conversation = get_whatsapp_conversation(db_path, phone)
    conversation_status = str((conversation or {}).get("status") or "bot")

    if conversation_status in {"human", "attention"} and normalized not in {"bot", "menu", "reiniciar", "cancelar"}:
        return []

    if state.get("human_mode") and normalized not in {"bot", "menu", "reiniciar", "cancelar"}:
        set_whatsapp_conversation_status(db_path, phone, "attention")
        return []

    if normalized in {"hola", "buenas", "inicio", "start"}:
        state = _new_state()
        save_whatsapp_session(db_path, phone, stored_name, state)
        return [_button_reply(phone, "Hola, bienvenido a Guanacopan Frances.\n\nPara iniciar tu pedido, elige tu ciudad:", [("san miguel", "San Miguel")])]

    if normalized in HUMAN_HELP_KEYWORDS:
        state["human_mode"] = True
        save_whatsapp_session(db_path, phone, stored_name, state)
        set_whatsapp_conversation_status(db_path, phone, "attention")
        return [
            "Claro, voy a pasar tu conversacion a nuestro equipo. "
            "Te responderemos por este mismo chat en breve."
        ]

    if normalized in {"ayuda", "help"}:
        return [HELP_TEXT]

    if normalized in {"cancelar", "salir", "reiniciar"}:
        delete_whatsapp_session(db_path, phone)
        return ["Listo, borre tu pedido en curso.\n\n" + WELCOME_TEXT]

    if normalized == "menu":
        if not state.get("city"):
            return [_button_reply(phone, "Para iniciar tu pedido, elige tu ciudad:", [("san miguel", "San Miguel")])]
        state["human_mode"] = False
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, stored_name, state)
        set_whatsapp_conversation_status(db_path, phone, "bot")
        return [build_whatsapp_category_reply(phone)]

    if normalized == "bot":
        state["human_mode"] = False
        save_whatsapp_session(db_path, phone, stored_name, state)
        set_whatsapp_conversation_status(db_path, phone, "bot")
        return ["Listo, el bot queda activo de nuevo.", build_whatsapp_category_reply(phone)]

    step = state.get("step") or "choose_city"
    if step == "choose_city":
        return _choose_city(db_path, phone, stored_name, state, text)
    if step == "choose_category":
        return _choose_category(db_path, phone, stored_name, state, text)
    if step == "choose_item":
        return _choose_item(db_path, phone, stored_name, state, text)
    if step == "enter_quantity":
        return _enter_quantity(db_path, phone, stored_name, state, text)
    if step == "review_order":
        return _review_order(db_path, phone, stored_name, state, text)

    state = _new_state()
    save_whatsapp_session(db_path, phone, stored_name, state)
    return [WELCOME_TEXT]


def _new_state() -> dict[str, Any]:
    return {"step": "choose_city", "city": "", "items": []}


def _choose_city(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    if _normalize(text) not in {"1", "san miguel"}:
        return [
            _button_reply(
                phone,
                "Por el momento solo atendemos pedidos en San Miguel.\n\nElige tu ciudad:",
                [("san miguel", "San Miguel")],
            )
        ]

    state["step"] = "choose_category"
    state["city"] = SUPPORTED_CITY
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [f"Perfecto, ciudad: {SUPPORTED_CITY}.", build_whatsapp_category_reply(phone)]


def _choose_category(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    category = _resolve_category(text)
    if not category:
        return ["No reconoci esa categoria.", build_whatsapp_category_reply(phone)]

    items = _items_by_category(category)
    if not items:
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [
            "Todavia no tengo bebidas cargadas en el menu.\n"
            "Cuando me pases esa lista, las agrego aqui.",
            build_whatsapp_category_reply(phone),
        ]

    state["step"] = "choose_item"
    state["category"] = category
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [_build_item_menu_reply(phone, category)]


def _choose_item(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    normalized = _normalize(text)
    if normalized == "ver":
        state["step"] = "review_order"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [_build_review_reply(phone, state)]

    item = _resolve_menu_item(state.get("category", ""), text)
    if not item:
        return ["No encontre ese producto.", _build_item_menu_reply(phone, str(state.get("category") or ""))]

    state["step"] = "enter_quantity"
    state["pending_item"] = item
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [
        _button_reply(
            phone,
            f"{item['name']} - ${item['price']:.2f}\nCuantas unidades deseas?",
            [("1", "1"), ("2", "2"), ("3", "3")],
        )
    ]


def _enter_quantity(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    quantity = _parse_quantity(text)
    if quantity <= 0:
        return ["La cantidad debe ser mayor a cero. Ejemplo: 1, 2 o 3."]

    item = dict(state.get("pending_item") or {})
    if not item:
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [build_whatsapp_category_reply(phone)]

    items = list(state.get("items") or [])
    existing = next((line for line in items if line["sku"] == item["sku"]), None)
    if existing:
        existing["quantity"] = round(float(existing["quantity"]) + quantity, 2)
    else:
        items.append(
            {
                "sku": item["sku"],
                "name": item["name"],
                "unit_price": item["price"],
                "quantity": quantity,
            }
        )

    state["items"] = items
    state["step"] = "review_order"
    state.pop("pending_item", None)
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [
        f"Agregado: {quantity:g} x {item['name']}.\n\n"
        + _build_order_summary(state),
        _build_review_reply(phone, state),
    ]


def _review_order(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    normalized = _normalize(text)
    if normalized == "agregar":
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [build_whatsapp_category_reply(phone)]
    if normalized == "ver":
        return [_build_review_reply(phone, state)]
    if normalized == "confirmar":
        return _confirm_order(db_path, phone, customer_name, state)

    return [
        "No entendi esa respuesta.\n\n"
        + _build_order_summary(state),
        _build_review_reply(phone, state),
    ]


def _confirm_order(db_path: str, phone: str, customer_name: str, state: dict[str, Any]) -> list[WhatsAppReply]:
    items = list(state.get("items") or [])
    if not items:
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return ["Tu pedido aun no tiene productos.", build_whatsapp_category_reply(phone)]

    try:
        existing_order_id = int(state.get("customer_order_id") or 0)
        if existing_order_id:
            result = update_customer_order_items(
                db_path,
                order_id=existing_order_id,
                customer_name=customer_name,
                city=str(state.get("city") or SUPPORTED_CITY),
                notes="Pedido actualizado por WhatsApp",
                items=items,
            )
        else:
            result = create_customer_order(
                db_path,
                customer_phone=phone,
                customer_name=customer_name,
                city=str(state.get("city") or SUPPORTED_CITY),
                notes="Pedido recibido por WhatsApp",
                items=items,
            )
    except ValueError as err:
        return [f"No pude guardar el pedido: {err}"]

    delete_whatsapp_session(db_path, phone)
    return [
        f"Pedido #{result['order_id']} {'actualizado' if state.get('customer_order_id') else 'recibido'} correctamente.\n"
        f"Ciudad: {result['city']}\n"
        f"Total: ${result['total']:.2f}\n\n"
        "Gracias por comprar en Guanacopan Frances. El equipo revisara tu pedido."
    ]


def _build_category_menu() -> str:
    options = "\n".join(
        f"{index}. {label}" for index, (_, label) in enumerate(MENU_CATEGORIES, start=1)
    )
    return "Elige una categoria del menu:\n" + options


def _build_item_menu(category: str) -> str:
    items = _items_by_category(category)
    category_label = _category_label(category)
    lines = [f"{index}. {item['name']} - ${item['price']:.2f}" for index, item in enumerate(items, start=1)]
    return f"{category_label}:\n" + "\n".join(lines) + "\n\nResponde con el numero o nombre del producto."


def _build_item_menu_reply(to_phone: str, category: str) -> WhatsAppReply:
    items = _items_by_category(category)
    if not items:
        return _build_item_menu(category)
    rows = [
        {
            "id": str(index),
            "title": item["name"],
            "description": f"${item['price']:.2f}",
        }
        for index, item in enumerate(items, start=1)
    ]
    return _list_reply(to_phone, f"{_category_label(category)}:", "Ver productos", "Productos", rows)


def _build_review_reply(to_phone: str, state: dict[str, Any]) -> WhatsAppReply:
    return _button_reply(
        to_phone,
        _build_order_summary(state) + "\n\nQue deseas hacer?",
        [("agregar", "Agregar"), ("confirmar", "Confirmar"), ("cancelar", "Cancelar")],
    )


def _build_order_summary(state: dict[str, Any]) -> str:
    items = list(state.get("items") or [])
    if not items:
        return "Tu pedido aun no tiene productos."

    total = _order_total(items)
    lines = "\n".join(
        f"- {item['quantity']:g} x {item['name']} (${_line_total(item):.2f})"
        for item in items
    )
    return f"Tu pedido en {state.get('city') or SUPPORTED_CITY}:\n{lines}\n\nTotal: ${total:.2f}"


def _resolve_category(text: str) -> str | None:
    normalized = _normalize(text)
    by_number = {str(index): category for index, (category, _) in enumerate(MENU_CATEGORIES, start=1)}
    if normalized in by_number:
        return by_number[normalized]

    for category, label in MENU_CATEGORIES:
        keys = {_normalize(category), _normalize(label)}
        if normalized in keys or any(normalized in key for key in keys):
            return category
    return None


def _resolve_menu_item(category: str, text: str) -> dict[str, Any] | None:
    items = _items_by_category(category)
    index = _parse_int(text)
    if index and 1 <= index <= len(items):
        return dict(items[index - 1])

    query = _normalize(text)
    exact = [item for item in items if _normalize(item["name"]) == query]
    if exact:
        return dict(exact[0])

    contains = [item for item in items if query in _normalize(item["name"])]
    if len(contains) == 1:
        return dict(contains[0])

    scored = [
        (SequenceMatcher(None, query, _normalize(item["name"])).ratio(), item)
        for item in items
    ]
    best_score, best_item = max(scored, default=(0, None), key=lambda pair: pair[0])
    if best_item and best_score >= 0.55:
        return dict(best_item)
    return None


def _items_by_category(category: str) -> list[dict[str, Any]]:
    return [dict(item) for item in MENU_ITEMS if item["category"] == category]


def _category_label(category: str) -> str:
    return next((label for key, label in MENU_CATEGORIES if key == category), "Menu")


def _order_total(items: list[dict[str, Any]]) -> float:
    return round(sum(_line_total(item) for item in items), 2)


def _line_total(item: dict[str, Any]) -> float:
    return round(float(item["quantity"]) * float(item["unit_price"]), 2)


def _normalize(value: str) -> str:
    no_accents = unicodedata.normalize("NFKD", value)
    ascii_text = no_accents.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def _parse_quantity(text: str) -> float:
    match = re.search(r"\d+(?:[\.,]\d+)?", text)
    if not match:
        return 0
    try:
        return round(float(match.group(0).replace(",", ".")), 2)
    except ValueError:
        return 0


def _parse_int(text: str) -> int | None:
    match = re.search(r"\d+", text)
    if not match:
        return None
    return int(match.group(0))
