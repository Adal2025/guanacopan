from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps
from app.supplier_profiles import get_supplier_profile

BUSINESS_NAME = "Guanacopan Francés"
BUSINESS_TITLE = "Orden de productos"
BUSINESS_ADDRESS = "Entre, Avenida Jose Simeon Canas Sur 46, San Miguel."
BUSINESS_PHONE = "64435199"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = PROJECT_ROOT / "app" / "static" / "logo-gpf.jpg"

COLOR_RED = "#ee2524"
COLOR_RED_LINE = "#e78f8f"
COLOR_LIGHT_RED = "#fff3f3"
COLOR_TEXT = "#2a1515"
COLOR_BACKGROUND = "#ffffff"
COLOR_NOTES_TEXT = "#402121"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if bold:
        candidates = [
            PROJECT_ROOT / "app" / "static" / "fonts" / "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    else:
        candidates = [
            PROJECT_ROOT / "app" / "static" / "fonts" / "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue

    return ImageFont.load_default()


def _format_qty(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _font_height(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont) -> int:
    top, bottom = draw.textbbox((0, 0), "Ag", font=font)[1::2]
    return bottom - top


def _truncate_to_width(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.ImageFont, max_width: int) -> str:
    text = value.strip()
    if not text:
        return ""
    if draw.textlength(text, font=font) <= max_width:
        return text
    candidate = text
    while candidate and draw.textlength(f"{candidate}...", font=font) > max_width:
        candidate = candidate[:-1]
    return f"{candidate.rstrip()}..."


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.ImageFont,
    fill: str,
    max_lines: int | None = None,
    line_gap: int = 4,
) -> int:
    content = text.strip()
    if not content:
        return y

    words = content.split()
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _truncate_to_width(draw, lines[-1], font, max_width)

    line_h = _font_height(draw, font)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + line_gap
    return y


def _load_round_logo(size: int) -> Image.Image | None:
    try:
        logo = Image.open(LOGO_PATH).convert("RGB")
    except OSError:
        return None

    logo = ImageOps.fit(logo, (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    out.paste(logo, (0, 0), mask)
    return out


def build_order_image(order: dict[str, Any]) -> Image.Image:
    items: list[dict[str, Any]] = order.get("items", [])
    notes = _safe_text(order.get("notes")) or "Sin notas generales."

    dpi = 150
    width = int(8.5 * dpi)
    height = int(11 * dpi)
    image = Image.new("RGB", (width, height), COLOR_BACKGROUND)
    draw = ImageDraw.Draw(image)

    f_ticket = _load_font(20, bold=True)
    f_title = _load_font(86, bold=True)
    f_card_title = _load_font(27, bold=True)
    f_card = _load_font(22)
    f_table_head = _load_font(24, bold=True)
    f_table = _load_font(22)
    f_notes_title = _load_font(24, bold=True)
    f_notes = _load_font(21)

    margin_x = 52
    margin_y = 52

    order_number = str(order.get("id") or 0).zfill(4)
    date_text = _safe_text(order.get("created_at_local") or order.get("created_at"))
    supplier = _safe_text(order.get("supplier_name"))
    supplier_profile = get_supplier_profile(supplier)
    supplier_display_name = _safe_text(supplier_profile.get("display_name")) or supplier
    supplier_contact = _safe_text(supplier_profile.get("contact")) or "-"
    supplier_address = _safe_text(supplier_profile.get("address")) or "-"

    ticket_w = 260
    ticket_h = 116
    ticket_x = margin_x
    ticket_y = margin_y
    draw.rounded_rectangle(
        (ticket_x, ticket_y, ticket_x + ticket_w, ticket_y + ticket_h),
        radius=18,
        fill=COLOR_RED,
    )
    draw.text((ticket_x + 16, ticket_y + 24), f"Pedido #: {order_number}", font=f_ticket, fill="white")
    draw.text((ticket_x + 16, ticket_y + 64), f"Fecha: {date_text}", font=f_ticket, fill="white")

    title_text = "Formulario\nde Pedidos"
    title_box = draw.multiline_textbbox((0, 0), title_text, font=f_title, spacing=2, align="center")
    title_w = title_box[2] - title_box[0]
    title_h = title_box[3] - title_box[1]
    title_x = (width - title_w) // 2
    title_y = ticket_y + (ticket_h - title_h) // 2 - 4
    draw.multiline_text((title_x, title_y), title_text, font=f_title, fill="#181616", spacing=2, align="center")

    logo_size = 104
    logo_x = width - margin_x - logo_size
    logo_y = margin_y + 4
    draw.ellipse((logo_x, logo_y, logo_x + logo_size, logo_y + logo_size), fill="#fff8f8", outline=COLOR_RED_LINE, width=2)
    logo = _load_round_logo(logo_size - 8)
    if logo:
        image.paste(logo, (logo_x + 4, logo_y + 4), logo)

    cards_top = ticket_y + ticket_h + 34
    cards_gap = 28
    card_h = 186
    card_w = (width - (margin_x * 2) - cards_gap) // 2
    left_card = (margin_x, cards_top, margin_x + card_w, cards_top + card_h)
    right_card = (margin_x + card_w + cards_gap, cards_top, width - margin_x, cards_top + card_h)

    for box in (left_card, right_card):
        draw.rounded_rectangle(box, radius=24, fill="#fff", outline=COLOR_RED_LINE, width=2)

    draw.text((left_card[0] + 24, left_card[1] + 22), "Datos del Negocio", font=f_card_title, fill=COLOR_TEXT)
    y_left = left_card[1] + 68
    y_left = _draw_wrapped_text(draw, f"Nombre: {BUSINESS_NAME}", left_card[0] + 24, y_left, card_w - 48, f_card, COLOR_TEXT, max_lines=2)
    y_left = _draw_wrapped_text(draw, f"N° de contacto: {BUSINESS_PHONE}", left_card[0] + 24, y_left + 4, card_w - 48, f_card, COLOR_TEXT, max_lines=1)
    _draw_wrapped_text(draw, f"Dirección: {BUSINESS_ADDRESS}", left_card[0] + 24, y_left + 4, card_w - 48, f_card, COLOR_TEXT, max_lines=2)

    draw.text((right_card[0] + 24, right_card[1] + 22), "Datos del Proveedor", font=f_card_title, fill=COLOR_TEXT)
    y_right = right_card[1] + 68
    y_right = _draw_wrapped_text(
        draw,
        f"Nombre: {supplier_display_name}",
        right_card[0] + 24,
        y_right,
        card_w - 48,
        f_card,
        COLOR_TEXT,
        max_lines=2,
    )
    y_right = _draw_wrapped_text(
        draw,
        f"N° de contacto: {supplier_contact}",
        right_card[0] + 24,
        y_right + 4,
        card_w - 48,
        f_card,
        COLOR_TEXT,
        max_lines=1,
    )
    _draw_wrapped_text(
        draw,
        f"Dirección: {supplier_address}",
        right_card[0] + 24,
        y_right + 4,
        card_w - 48,
        f_card,
        COLOR_TEXT,
        max_lines=2,
    )

    table_top = cards_top + card_h + 28
    table_left = margin_x
    table_right = width - margin_x
    table_w = table_right - table_left

    notes_h = 142
    notes_gap = 24
    table_header_h = 48
    rows_count = max(1, len(items))

    available_rows_h = height - margin_y - notes_h - notes_gap - table_top - table_header_h
    row_h = max(20, min(36, int(available_rows_h / rows_count)))
    table_rows_h = row_h * rows_count
    table_bottom = table_top + table_header_h + table_rows_h

    draw.rounded_rectangle((table_left, table_top, table_right, table_bottom), radius=18, fill="#fff", outline=COLOR_RED_LINE, width=2)
    draw.rectangle((table_left, table_top, table_right, table_top + table_header_h), fill=COLOR_LIGHT_RED)
    draw.line((table_left, table_top + table_header_h, table_right, table_top + table_header_h), fill=COLOR_RED_LINE, width=2)

    qty_col_w = 155
    notes_col_w = 270
    qty_x = table_left + qty_col_w
    notes_x = table_right - notes_col_w
    draw.line((qty_x, table_top, qty_x, table_bottom), fill=COLOR_RED_LINE, width=2)
    draw.line((notes_x, table_top, notes_x, table_bottom), fill=COLOR_RED_LINE, width=2)

    draw.text((table_left + 18, table_top + 12), "Cantidad", font=f_table_head, fill=COLOR_TEXT)
    draw.text((qty_x + 18, table_top + 12), "Productos", font=f_table_head, fill=COLOR_TEXT)
    draw.text((notes_x + 18, table_top + 12), "Notas", font=f_table_head, fill=COLOR_TEXT)

    rows = items if items else [{"quantity": "", "product_name": "Sin productos seleccionados.", "note": ""}]
    row_y = table_top + table_header_h
    for item in rows:
        draw.line((table_left, row_y, table_right, row_y), fill="#f1c9c9", width=1)

        quantity_raw = item.get("quantity")
        quantity = _format_qty(float(quantity_raw)) if quantity_raw not in ("", None, 0) else ""
        product_name = _safe_text(item.get("product_name"))
        note = _safe_text(item.get("note"))

        draw.text((table_left + 18, row_y + 7), quantity, font=f_table, fill=COLOR_TEXT)
        draw.text((qty_x + 18, row_y + 7), _truncate_to_width(draw, product_name, f_table, notes_x - qty_x - 34), font=f_table, fill=COLOR_TEXT)
        draw.text((notes_x + 18, row_y + 7), _truncate_to_width(draw, note, f_table, table_right - notes_x - 34), font=f_table, fill=COLOR_TEXT)

        row_y += row_h
    draw.line((table_left, table_bottom, table_right, table_bottom), fill=COLOR_RED_LINE, width=2)

    notes_top = table_bottom + notes_gap
    notes_bottom = min(height - margin_y, notes_top + notes_h)
    draw.rounded_rectangle((table_left, notes_top, table_right, notes_bottom), radius=18, fill="#fff", outline=COLOR_RED_LINE, width=2)
    draw.text((table_left + 18, notes_top + 16), "Notas generales", font=f_notes_title, fill=COLOR_TEXT)
    _draw_wrapped_text(
        draw,
        notes,
        table_left + 18,
        notes_top + 54,
        table_w - 36,
        f_notes,
        COLOR_NOTES_TEXT,
        max_lines=4,
        line_gap=5,
    )

    return image


def build_order_jpg_bytes(order: dict[str, Any]) -> bytes:
    image = build_order_image(order)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def build_order_pdf_bytes(order: dict[str, Any]) -> bytes:
    image = build_order_image(order).convert("RGB")
    output = io.BytesIO()
    image.save(output, format="PDF", resolution=150.0)
    return output.getvalue()
