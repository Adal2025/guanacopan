from __future__ import annotations

import os
import hashlib
import hmac
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database import (
    EXPECTED_SUPPLIERS,
    build_order_csv,
    create_order,
    delete_order,
    fetch_products,
    get_customer_order,
    get_order,
    init_db,
    list_customer_orders,
    list_orders,
    update_order,
)
from app.exporters import build_agenda_jpg_bytes, build_agenda_pdf_bytes, build_order_jpg_bytes, build_order_pdf_bytes
from app.schemas import AgendaExportRequest, CreateOrderRequest, CreateOrderResponse, OrderDetailOut, ProductOut
from app.supplier_profiles import SUPPLIER_PROFILES
from app.whatsapp import handle_customer_message, send_whatsapp_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("ORDERS_DB_PATH", str(PROJECT_ROOT / "data" / "orders.db"))
PRODUCTS_CSV_PATH = os.getenv("PRODUCTS_CSV_PATH", str(PROJECT_ROOT / "data" / "products.csv"))
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-secret")
APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "gpfSmiguel")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db(DB_PATH, PRODUCTS_CSV_PATH)
    yield


app = FastAPI(title="App de Pedidos", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    max_age=60 * 60 * 12,
)
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "app" / "templates"))


def _current_user(request: Request) -> str | None:
    value = request.session.get("user")
    return str(value) if value else None


def _require_user(request: Request) -> str:
    user = _current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user


def _with_local_datetime(order: dict) -> dict:
    created_at = str(order.get("created_at") or "")
    try:
        dt = datetime.fromisoformat(created_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        order["created_at_local"] = dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        order["created_at_local"] = created_at
    return order


def _is_valid_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if not WHATSAPP_APP_SECRET:
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        WHATSAPP_APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


def _extract_whatsapp_messages(payload: dict) -> list[dict[str, str]]:
    parsed_messages: list[dict[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            contacts_by_phone = {
                str(contact.get("wa_id") or ""): str((contact.get("profile") or {}).get("name") or "")
                for contact in value.get("contacts", [])
            }
            for message in value.get("messages", []):
                phone = str(message.get("from") or "")
                text = _extract_whatsapp_text(message)
                if not phone or not text:
                    continue
                parsed_messages.append(
                    {
                        "phone": phone,
                        "customer_name": contacts_by_phone.get(phone, ""),
                        "text": text,
                    }
                )
    return parsed_messages


def _extract_whatsapp_text(message: dict) -> str:
    message_type = message.get("type")
    if message_type == "text":
        return str((message.get("text") or {}).get("body") or "").strip()
    if message_type == "button":
        return str((message.get("button") or {}).get("text") or "").strip()
    if message_type == "interactive":
        interactive = message.get("interactive") or {}
        if interactive.get("type") == "list_reply":
            reply = interactive.get("list_reply") or {}
            return str(reply.get("id") or reply.get("title") or "").strip()
        if interactive.get("type") == "button_reply":
            reply = interactive.get("button_reply") or {}
            return str(reply.get("id") or reply.get("title") or "").strip()
    return ""


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/whatsapp/webhook")
def verify_whatsapp_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token and token == WHATSAPP_VERIFY_TOKEN and challenge:
        return Response(content=challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Token de verificacion invalido.")


@app.post("/api/whatsapp/webhook")
async def receive_whatsapp_webhook(request: Request) -> dict[str, bool]:
    raw_body = await request.body()
    if not _is_valid_meta_signature(raw_body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(status_code=403, detail="Firma invalida.")

    try:
        payload = await request.json()
    except ValueError as err:
        raise HTTPException(status_code=400, detail="JSON invalido.") from err

    for incoming in _extract_whatsapp_messages(payload):
        replies = handle_customer_message(
            DB_PATH,
            phone=incoming["phone"],
            customer_name=incoming["customer_name"],
            incoming_text=incoming["text"],
        )
        for reply in replies:
            send_whatsapp_text(incoming["phone"], reply)

    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if _current_user(request):
        return RedirectResponse(url="/app", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    if _current_user(request):
        return RedirectResponse(url="/app", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    username = username.strip()
    if username == APP_USERNAME and password == APP_PASSWORD:
        request.session["user"] = username
        return RedirectResponse(url="/app", status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "Usuario o contraseña incorrectos."},
        status_code=401,
    )


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/app", response_class=HTMLResponse)
def app_page(request: Request) -> HTMLResponse:
    user = _current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "menu.html",
        {
            "user": user,
        },
    )


@app.get("/compras", response_class=HTMLResponse)
def purchases_page(request: Request) -> HTMLResponse:
    user = _current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "suppliers": list(EXPECTED_SUPPLIERS),
            "supplier_profiles": SUPPLIER_PROFILES,
        },
    )


@app.get("/agenda-diaria", response_class=HTMLResponse)
def daily_agenda_page(request: Request) -> HTMLResponse:
    user = _current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "agenda.html",
        {
            "user": user,
        },
    )


@app.get("/pedidos-clientes", response_class=HTMLResponse)
def customer_orders_page(request: Request) -> HTMLResponse:
    user = _current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "customer_orders.html",
        {
            "user": user,
        },
    )


@app.get("/api/session")
def get_session(request: Request) -> dict[str, str]:
    user = _require_user(request)
    return {"user": user}


@app.get("/api/products", response_model=list[ProductOut])
def get_products(request: Request) -> list[ProductOut]:
    _require_user(request)
    products = fetch_products(DB_PATH)
    return [ProductOut(**product) for product in products]


@app.get("/api/orders")
def get_orders(request: Request) -> list[dict]:
    _require_user(request)
    return list_orders(DB_PATH)


@app.get("/api/customer-orders")
def get_customer_orders(request: Request) -> list[dict]:
    _require_user(request)
    return list_customer_orders(DB_PATH)


@app.get("/api/customer-orders/{order_id}")
def get_customer_order_detail(request: Request, order_id: int) -> dict:
    _require_user(request)
    try:
        return get_customer_order(DB_PATH, order_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@app.post("/api/orders", response_model=CreateOrderResponse)
def post_order(request: Request, payload: CreateOrderRequest) -> CreateOrderResponse:
    user = _require_user(request)
    try:
        result = create_order(
            DB_PATH,
            employee_name=user,
            supplier_name=payload.supplier_name,
            notes=payload.notes,
            items=[item.model_dump() for item in payload.items],
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    return CreateOrderResponse(**result)


@app.get("/api/orders/{order_id}", response_model=OrderDetailOut)
def get_order_detail(request: Request, order_id: int) -> OrderDetailOut:
    _require_user(request)
    try:
        order = get_order(DB_PATH, order_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return OrderDetailOut(**order)


@app.put("/api/orders/{order_id}", response_model=CreateOrderResponse)
def put_order(request: Request, order_id: int, payload: CreateOrderRequest) -> CreateOrderResponse:
    user = _require_user(request)
    try:
        result = update_order(
            DB_PATH,
            order_id=order_id,
            employee_name=user,
            supplier_name=payload.supplier_name,
            notes=payload.notes,
            items=[item.model_dump() for item in payload.items],
        )
    except ValueError as err:
        status = 404 if "no encontrado" in str(err).lower() else 400
        raise HTTPException(status_code=status, detail=str(err)) from err
    return CreateOrderResponse(**result)


@app.delete("/api/orders/{order_id}")
def remove_order(request: Request, order_id: int) -> dict[str, bool]:
    _require_user(request)
    try:
        delete_order(DB_PATH, order_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    return {"ok": True}


@app.get("/api/orders/{order_id}/export.csv")
def export_order(request: Request, order_id: int):
    _require_user(request)
    try:
        csv_content = build_order_csv(DB_PATH, order_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err

    filename = f"pedido_{order_id}.csv"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/orders/{order_id}/export.pdf")
def export_order_pdf(request: Request, order_id: int):
    _require_user(request)
    try:
        order = _with_local_datetime(get_order(DB_PATH, order_id))
        binary = build_order_pdf_bytes(order)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err

    filename = f"pedido_{order_id}.pdf"
    return Response(
        content=binary,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/orders/{order_id}/export.jpg")
def export_order_jpg(request: Request, order_id: int):
    _require_user(request)
    try:
        order = _with_local_datetime(get_order(DB_PATH, order_id))
        binary = build_order_jpg_bytes(order)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err

    filename = f"pedido_{order_id}.jpg"
    return Response(
        content=binary,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/agenda/export.pdf")
def export_agenda_pdf(request: Request, payload: AgendaExportRequest):
    _require_user(request)
    binary = build_agenda_pdf_bytes(payload.model_dump())
    filename = f'agenda_{payload.employee_name}_{payload.date_text.lower().replace(" ", "_")}.pdf'
    return Response(
        content=binary,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/agenda/export.jpg")
def export_agenda_jpg(request: Request, payload: AgendaExportRequest):
    _require_user(request)
    binary = build_agenda_jpg_bytes(payload.model_dump())
    filename = f'agenda_{payload.employee_name}_{payload.date_text.lower().replace(" ", "_")}.jpg'
    return Response(
        content=binary,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
