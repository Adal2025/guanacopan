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

MAIN_OPTIONS = (
    ("ordenar_ahora", "Ordenar ahora"),
    ("ver_menu", "Ver menu"),
    ("promociones", "Promociones"),
    ("ubicacion", "Ubicacion"),
    ("hablar", "Hablar con alguien"),
)

ORDER_TYPES = (
    ("recoger", "Recoger en local"),
    ("comer_local", "Comer en el local"),
    ("delivery", "Consultar delivery"),
)

MENU_CATEGORIES = (
    ("panes", "Panes"),
    ("combos", "Combos"),
    ("alitas", "Alitas"),
    ("nachos", "Nachos"),
    ("bebidas", "Bebidas"),
)

MENU_ITEMS = (
    {"sku": "PAN-011", "category": "panes", "name": "Steak Sandwich", "price": 6.99, "has_bread": True},
    {"sku": "DES-005", "category": "panes", "name": "Panpollo", "price": 2.99, "has_bread": True},
    {"sku": "PAN-005", "category": "panes", "name": "Pansalchi", "price": 1.99, "has_bread": True},
    {"sku": "PAN-008", "category": "panes", "name": "Salchiloco", "price": 3.99, "has_bread": True},
    {"sku": "PAN-010", "category": "panes", "name": "El Criollo", "price": 3.99, "has_bread": True},
    {"sku": "EXT-003", "category": "alitas", "name": "Alitas", "price": 5.50, "has_bread": False},
    {"sku": "EXT-001", "category": "nachos", "name": "Nachos", "price": 2.99, "has_bread": False},
    {"sku": "BEB-001", "category": "bebidas", "name": "Bebidas", "price": 0.00, "has_bread": False},
)

CUSTOMIZATION_OPTIONS = (
    ("clasico", "Clasico GPF"),
    ("cebolla_caramelizada", "Cebolla caramelizada"),
    ("cebolla_fresca", "Cebolla fresca"),
    ("doble_cebolla", "Doble cebolla"),
    ("sin_cebolla", "Sin cebolla"),
    ("personalizado", "Personalizado"),
)

BREAD_OPTIONS = (
    ("pan_tostadito", "Pan tostadito"),
    ("medio_tostadito", "Medio tostadito"),
    ("solo_calientito", "Solo calientito"),
)

COMBO_OPTIONS = (
    ("solo", "Solo producto", 0.00),
    ("papas_soda", "Papas + soda", 2.00),
    ("papas_fresco", "Papas + fresco natural", 2.50),
)

PAYMENT_METHODS = (
    ("efectivo", "Efectivo"),
    ("transferencia", "Transferencia"),
    ("tarjeta_local", "Tarjeta en local"),
)

WELCOME_TEXT = (
    "Bienvenido a GuanacoPan 😏\n"
    "El pan que nos une.\n\n"
    "¿Que deseas hacer?\n\n"
    "1. Ordenar ahora\n"
    "2. Ver menu\n"
    "3. Promociones\n"
    "4. Ubicacion\n"
    "5. Hablar con alguien"
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


def is_internal_whatsapp_reply(reply: WhatsAppReply) -> bool:
    return isinstance(reply, dict) and bool(reply.get("internal"))


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
    return _list_reply(to_phone, "¿Que se te antoja?", "Ver opciones", "Categorias", rows)


def build_whatsapp_initial_reply(to_phone: str) -> WhatsAppReply:
    rows = [{"id": option_id, "title": title} for option_id, title in MAIN_OPTIONS]
    return _list_reply(to_phone, WELCOME_TEXT, "Elegir", "GuanacoPan", rows)


def build_whatsapp_order_type_reply(to_phone: str) -> WhatsAppReply:
    return _button_reply(
        to_phone,
        "¿Tu pedido es para?",
        [(option_id, title) for option_id, title in ORDER_TYPES],
    )


def build_whatsapp_promotions_reply() -> str:
    return (
        "Promociones GuanacoPan 🔥\n\n"
        "Por hoy consulta con el equipo las promociones disponibles. "
        "Tambien puedes ordenar y te contamos si aplica alguna promo."
    )


def build_whatsapp_location_reply() -> str:
    return (
        "Estamos en San Miguel.\n\n"
        "Escribenos si necesitas indicaciones exactas o toca 'Hablar con alguien' "
        "para que el equipo te oriente."
    )


def build_unavailable_product_reply(to_phone: str) -> list[WhatsAppReply]:
    return [
        "Por el momento no tenemos disponible ese producto. Te invitamos a seleccionar otra opcion.",
        build_whatsapp_category_reply(to_phone),
    ]


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
        return [build_whatsapp_initial_reply(phone)]

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
        return ["Listo, borre tu pedido en curso.", build_whatsapp_initial_reply(phone)]

    if normalized == "menu":
        state["human_mode"] = False
        state["step"] = "main_menu"
        save_whatsapp_session(db_path, phone, stored_name, state)
        set_whatsapp_conversation_status(db_path, phone, "bot")
        return [build_whatsapp_initial_reply(phone)]

    if normalized == "bot":
        state["human_mode"] = False
        save_whatsapp_session(db_path, phone, stored_name, state)
        set_whatsapp_conversation_status(db_path, phone, "bot")
        return ["Listo, el bot queda activo de nuevo.", build_whatsapp_initial_reply(phone)]

    step = state.get("step") or "main_menu"
    if step == "main_menu":
        return _handle_main_menu(db_path, phone, stored_name, state, text)
    if step == "choose_order_type":
        return _choose_order_type(db_path, phone, stored_name, state, text)
    if step == "choose_category":
        return _choose_category(db_path, phone, stored_name, state, text)
    if step == "choose_item":
        return _choose_item(db_path, phone, stored_name, state, text)
    if step == "choose_customization":
        return _choose_customization(db_path, phone, stored_name, state, text)
    if step == "choose_bread":
        return _choose_bread(db_path, phone, stored_name, state, text)
    if step == "choose_combo":
        return _choose_combo(db_path, phone, stored_name, state, text)
    if step == "review_order":
        return _review_order(db_path, phone, stored_name, state, text)
    if step == "enter_customer_name":
        return _enter_customer_name(db_path, phone, stored_name, state, text)
    if step == "enter_pickup_time":
        return _enter_pickup_time(db_path, phone, stored_name, state, text)
    if step == "choose_payment":
        return _choose_payment(db_path, phone, stored_name, state, text)

    state = _new_state()
    save_whatsapp_session(db_path, phone, stored_name, state)
    return [build_whatsapp_initial_reply(phone)]


def _new_state() -> dict[str, Any]:
    return {"step": "main_menu", "city": SUPPORTED_CITY, "items": []}


def _handle_main_menu(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    option = _resolve_option(text, MAIN_OPTIONS)
    if not option:
        return ["No reconoci esa opcion.", build_whatsapp_initial_reply(phone)]

    if option == "ordenar_ahora":
        state.update({"step": "choose_order_type", "city": SUPPORTED_CITY, "items": []})
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [build_whatsapp_order_type_reply(phone)]
    if option == "ver_menu":
        return [_build_public_menu(), build_whatsapp_initial_reply(phone)]
    if option == "promociones":
        return [build_whatsapp_promotions_reply(), build_whatsapp_initial_reply(phone)]
    if option == "ubicacion":
        return [build_whatsapp_location_reply(), build_whatsapp_initial_reply(phone)]

    state["human_mode"] = True
    save_whatsapp_session(db_path, phone, customer_name, state)
    set_whatsapp_conversation_status(db_path, phone, "attention")
    return [
        "Claro, voy a pasar tu conversacion a nuestro equipo. "
        "Te responderemos por este mismo chat en breve."
    ]


def _choose_order_type(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    order_type = _resolve_option(text, ORDER_TYPES)
    if not order_type:
        return ["No reconoci el tipo de pedido.", build_whatsapp_order_type_reply(phone)]

    state["step"] = "choose_category"
    state["tipo_pedido"] = _option_label(order_type, ORDER_TYPES)
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [build_whatsapp_category_reply(phone)]


def _choose_category(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    category = _resolve_option(text, MENU_CATEGORIES)
    if not category:
        return ["No reconoci esa categoria.", build_whatsapp_category_reply(phone)]

    state["step"] = "choose_item"
    state["category"] = category
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [_build_item_menu_reply(phone)]


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

    item = _resolve_menu_item(text)
    if not item:
        return ["No encontre ese producto.", _build_item_menu_reply(phone)]

    state["step"] = "choose_customization"
    state["pending_item"] = item
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [_build_customization_reply(phone, item)]


def _choose_customization(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    customization = _resolve_option(text, CUSTOMIZATION_OPTIONS)
    if not customization:
        item = dict(state.get("pending_item") or {})
        return ["No reconoci esa personalizacion.", _build_customization_reply(phone, item)]

    item = dict(state.get("pending_item") or {})
    if not item:
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [build_whatsapp_category_reply(phone)]

    item["customization"] = _option_label(customization, CUSTOMIZATION_OPTIONS)
    state["pending_item"] = item
    state["step"] = "choose_bread" if item.get("has_bread") else "choose_combo"
    save_whatsapp_session(db_path, phone, customer_name, state)
    if item.get("has_bread"):
        return [_build_bread_reply(phone)]
    return [_build_combo_reply(phone)]


def _choose_bread(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    bread = _resolve_option(text, BREAD_OPTIONS)
    if not bread:
        return ["No reconoci esa opcion de pan.", _build_bread_reply(phone)]

    item = dict(state.get("pending_item") or {})
    if not item:
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [build_whatsapp_category_reply(phone)]

    item["bread"] = _option_label(bread, BREAD_OPTIONS)
    state["pending_item"] = item
    state["step"] = "choose_combo"
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [_build_combo_reply(phone)]


def _choose_combo(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    combo = _resolve_combo(text)
    if not combo:
        return ["No reconoci esa opcion de combo.", _build_combo_reply(phone)]

    item = dict(state.get("pending_item") or {})
    if not item:
        state["step"] = "choose_category"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return [build_whatsapp_category_reply(phone)]

    combo_id, combo_label, combo_price = combo
    item["combo"] = combo_label
    item["combo_id"] = combo_id
    item["unit_price"] = round(float(item["price"]) + float(combo_price), 2)
    item["quantity"] = 1
    item["name"] = _format_item_name(item)

    items = list(state.get("items") or [])
    items.append(item)
    state["items"] = items
    state["step"] = "review_order"
    state.pop("pending_item", None)
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [
        "Producto agregado ✅\n\n"
        "Tu orden actual:\n\n"
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
        if not list(state.get("items") or []):
            return ["Tu pedido aun no tiene productos.", build_whatsapp_category_reply(phone)]
        state["step"] = "enter_customer_name"
        save_whatsapp_session(db_path, phone, customer_name, state)
        return ["Para confirmar tu pedido, compartenos tu nombre:"]

    return [
        "No entendi esa respuesta.\n\n"
        + _build_order_summary(state),
        _build_review_reply(phone, state),
    ]


def _enter_customer_name(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    name = text.strip()
    if len(name) < 2:
        return ["Escribenos tu nombre para confirmar el pedido:"]

    state["nombre_cliente"] = name
    state["step"] = "enter_pickup_time"
    save_whatsapp_session(db_path, phone, customer_name, state)
    return ["¿A que hora deseas retirar o recibir tu pedido?"]


def _enter_pickup_time(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    pickup_time = text.strip()
    if len(pickup_time) < 2:
        return ["Indicanos la hora de retiro o atencion:"]

    state["hora_retiro"] = pickup_time
    state["step"] = "choose_payment"
    save_whatsapp_session(db_path, phone, customer_name, state)
    return [_build_payment_reply(phone)]


def _choose_payment(
    db_path: str,
    phone: str,
    customer_name: str,
    state: dict[str, Any],
    text: str,
) -> list[WhatsAppReply]:
    payment = _resolve_option(text, PAYMENT_METHODS)
    if not payment:
        return ["No reconoci ese metodo de pago.", _build_payment_reply(phone)]

    state["metodo_pago"] = _option_label(payment, PAYMENT_METHODS)
    save_whatsapp_session(db_path, phone, customer_name, state)
    return _confirm_order(db_path, phone, customer_name, state)


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
                customer_name=str(state.get("nombre_cliente") or customer_name),
                city=str(state.get("city") or SUPPORTED_CITY),
                notes=_build_order_notes(state),
                items=items,
            )
        else:
            result = create_customer_order(
                db_path,
                customer_phone=phone,
                customer_name=str(state.get("nombre_cliente") or customer_name),
                city=str(state.get("city") or SUPPORTED_CITY),
                notes=_build_order_notes(state),
                items=items,
            )
    except ValueError as err:
        return [f"No pude guardar el pedido: {err}"]

    delete_whatsapp_session(db_path, phone)
    customer_display_name = str(state.get("nombre_cliente") or customer_name or "cliente")
    return [
        f"Gracias, {customer_display_name} ✅\n\n"
        "Recibimos tu orden:\n\n"
        f"{_build_order_summary(state)}\n\n"
        f"Tipo de pedido: {state.get('tipo_pedido') or 'Pendiente'}\n"
        f"Pago: {state.get('metodo_pago') or 'Pendiente'}\n\n"
        "Un miembro del equipo confirmara tu tiempo estimado.",
        {"internal": True, "body": _build_internal_order_message(state)},
    ]


def _build_category_menu() -> str:
    options = "\n".join(
        f"{index}. {label}" for index, (_, label) in enumerate(MENU_CATEGORIES, start=1)
    )
    return "¿Que se te antoja?\n" + options


def _build_public_menu() -> str:
    lines = [f"{index}. {item['name']} - ${item['price']:.2f}" for index, item in enumerate(MENU_ITEMS, start=1)]
    return "Menu GuanacoPan:\n" + "\n".join(lines)


def _build_item_menu() -> str:
    items = list(MENU_ITEMS)
    lines = [f"{index}. {item['name']} - ${item['price']:.2f}" for index, item in enumerate(items, start=1)]
    return "Elige tu producto:\n" + "\n".join(lines)


def _build_item_menu_reply(to_phone: str) -> WhatsAppReply:
    items = list(MENU_ITEMS)
    rows = [
        {
            "id": str(index),
            "title": item["name"],
            "description": f"${item['price']:.2f}",
        }
        for index, item in enumerate(items, start=1)
    ]
    return _list_reply(to_phone, "Elige tu producto:", "Ver productos", "Productos", rows)


def _build_customization_reply(to_phone: str, item: dict[str, Any]) -> WhatsAppReply:
    item_name = str(item.get("name") or "tu producto")
    rows = [{"id": option_id, "title": label} for option_id, label in CUSTOMIZATION_OPTIONS]
    return _list_reply(to_phone, f"¿Como quieres {item_name}?", "Elegir estilo", "Personalizacion", rows)


def _build_bread_reply(to_phone: str) -> WhatsAppReply:
    return _button_reply(
        to_phone,
        "¿Como quieres el pan?",
        [(option_id, label) for option_id, label in BREAD_OPTIONS],
    )


def _build_combo_reply(to_phone: str) -> WhatsAppReply:
    return _button_reply(
        to_phone,
        "¿Lo quieres en combo?",
        [("solo", "Solo producto"), ("papas_soda", "Papas + soda"), ("papas_fresco", "Papas + fresco")],
    )


def _build_payment_reply(to_phone: str) -> WhatsAppReply:
    return _button_reply(
        to_phone,
        "Metodo de pago:",
        [(option_id, label) for option_id, label in PAYMENT_METHODS],
    )


def _build_review_reply(to_phone: str, state: dict[str, Any]) -> WhatsAppReply:
    rows = [
        {"id": "agregar", "title": "Agregar otro"},
        {"id": "ver", "title": "Ver mi orden"},
        {"id": "confirmar", "title": "Confirmar pedido"},
        {"id": "cancelar", "title": "Cancelar"},
    ]
    return _list_reply(
        to_phone,
        _build_order_summary(state) + "\n\n¿Que deseas hacer ahora?",
        "Elegir",
        "Orden actual",
        rows,
    )


def _build_order_summary(state: dict[str, Any]) -> str:
    items = list(state.get("items") or [])
    if not items:
        return "Tu pedido aun no tiene productos."

    total = _order_total(items)
    lines = "\n".join(f"- {item['name']}" for item in items)
    return f"{lines}\n\nTotal: ${total:.2f}"


def _build_order_notes(state: dict[str, Any]) -> str:
    return (
        f"Tipo de pedido: {state.get('tipo_pedido') or 'Pendiente'}\n"
        f"Nombre: {state.get('nombre_cliente') or 'Pendiente'}\n"
        f"Hora de retiro: {state.get('hora_retiro') or 'Pendiente'}\n"
        f"Metodo de pago: {state.get('metodo_pago') or 'Pendiente'}\n\n"
        f"Orden:\n{_build_order_summary(state)}"
    )


def _build_internal_order_message(state: dict[str, Any]) -> str:
    return (
        "🚨 NUEVA ORDEN GPF\n\n"
        f"Cliente: {state.get('nombre_cliente') or 'Pendiente'}\n"
        f"Tipo: {state.get('tipo_pedido') or 'Pendiente'}\n"
        f"Pago: {state.get('metodo_pago') or 'Pendiente'}\n\n"
        "ORDEN:\n"
        f"{_build_order_summary(state)}\n\n"
        "Estado: Pendiente de confirmar"
    )


def _format_item_name(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("name") or ""),
        str(item.get("customization") or ""),
        str(item.get("bread") or ""),
        str(item.get("combo") or ""),
    ]
    return " | ".join(part for part in parts if part)


def _resolve_option(text: str, options: tuple[tuple[str, str], ...]) -> str | None:
    normalized = _normalize(text)
    by_number = {str(index): option_id for index, (option_id, _) in enumerate(options, start=1)}
    if normalized in by_number:
        return by_number[normalized]

    for option_id, label in options:
        keys = {_normalize(option_id), _normalize(label)}
        if normalized in keys or any(normalized in key for key in keys):
            return option_id
    return None


def _option_label(option_id: str, options: tuple[tuple[str, str], ...]) -> str:
    return next((label for key, label in options if key == option_id), option_id)


def _resolve_combo(text: str) -> tuple[str, str, float] | None:
    normalized = _normalize(text)
    by_number = {str(index): option for index, option in enumerate(COMBO_OPTIONS, start=1)}
    if normalized in by_number:
        return by_number[normalized]
    for option_id, label, price in COMBO_OPTIONS:
        keys = {_normalize(option_id), _normalize(label)}
        if normalized in keys or any(normalized in key for key in keys):
            return (option_id, label, price)
    return None


def _resolve_menu_item(text: str) -> dict[str, Any] | None:
    items = list(MENU_ITEMS)
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
