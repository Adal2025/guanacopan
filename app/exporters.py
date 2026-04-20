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
COLOR_BORDER = "#dfc4b3"
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


def _draw_labeled_wrapped_text(
    draw: ImageDraw.ImageDraw,
    label: str,
    value: str,
    x: int,
    y: int,
    max_width: int,
    label_font: ImageFont.ImageFont,
    value_font: ImageFont.ImageFont,
    fill: str,
    max_lines: int | None = None,
    line_gap: int = 4,
) -> int:
    safe_value = value.strip() or "-"
    label_text = f"{label}: "
    label_width = int(draw.textlength(label_text, font=label_font))
    label_height = _font_height(draw, label_font)
    value_height = _font_height(draw, value_font)
    line_h = max(label_height, value_height)
    value_max_width = max(40, max_width - label_width)

    words = safe_value.split()
    if not words:
        words = ["-"]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        if draw.textlength(test, font=value_font) <= value_max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _truncate_to_width(draw, lines[-1], value_font, value_max_width)

    draw.text((x, y), label_text, font=label_font, fill=fill)
    draw.text((x + label_width, y), lines[0], font=value_font, fill=fill)
    y += line_h + line_gap

    for line in lines[1:]:
        draw.text((x + label_width, y), line, font=value_font, fill=fill)
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
    f_title = _load_font(76, bold=True)
    f_card_title = _load_font(27, bold=True)
    f_card = _load_font(22)
    f_card_label = _load_font(22, bold=True)
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

    logo_size = ticket_h
    logo_x = width - margin_x - logo_size
    logo_y = ticket_y
    draw.ellipse((logo_x, logo_y, logo_x + logo_size, logo_y + logo_size), fill="#fff8f8", outline=COLOR_RED_LINE, width=2)
    logo = _load_round_logo(logo_size - 8)
    if logo:
        image.paste(logo, (logo_x + 4, logo_y + 4), logo)

    title_text = "Formulario\nde Pedidos"
    title_spacing = 0
    title_box = draw.multiline_textbbox((0, 0), title_text, font=f_title, spacing=title_spacing, align="center")
    title_w = title_box[2] - title_box[0]
    title_h = title_box[3] - title_box[1]
    title_area_left = ticket_x + ticket_w + 32
    title_area_right = logo_x - 32
    title_area_center_x = (title_area_left + title_area_right) / 2
    title_area_center_y = ticket_y + (ticket_h / 2)
    title_x = int(title_area_center_x - (title_w / 2))
    title_y = int(title_area_center_y - (title_h / 2)) - 2
    draw.multiline_text((title_x, title_y), title_text, font=f_title, fill="#181616", spacing=title_spacing, align="center")

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
    y_left = _draw_labeled_wrapped_text(draw, "Nombre", BUSINESS_NAME, left_card[0] + 24, y_left, card_w - 48, f_card_label, f_card, COLOR_TEXT, max_lines=2)
    y_left = _draw_labeled_wrapped_text(draw, "N° de contacto", BUSINESS_PHONE, left_card[0] + 24, y_left + 4, card_w - 48, f_card_label, f_card, COLOR_TEXT, max_lines=1)
    _draw_labeled_wrapped_text(draw, "Dirección", BUSINESS_ADDRESS, left_card[0] + 24, y_left + 4, card_w - 48, f_card_label, f_card, COLOR_TEXT, max_lines=2)

    draw.text((right_card[0] + 24, right_card[1] + 22), "Datos del Proveedor", font=f_card_title, fill=COLOR_TEXT)
    y_right = right_card[1] + 68
    y_right = _draw_labeled_wrapped_text(
        draw,
        "Nombre",
        supplier_display_name,
        right_card[0] + 24,
        y_right,
        card_w - 48,
        f_card_label,
        f_card,
        COLOR_TEXT,
        max_lines=2,
    )
    y_right = _draw_labeled_wrapped_text(
        draw,
        "N° de contacto",
        supplier_contact,
        right_card[0] + 24,
        y_right + 4,
        card_w - 48,
        f_card_label,
        f_card,
        COLOR_TEXT,
        max_lines=1,
    )
    _draw_labeled_wrapped_text(
        draw,
        "Dirección",
        supplier_address,
        right_card[0] + 24,
        y_right + 4,
        card_w - 48,
        f_card_label,
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


def _draw_checkbox(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, checked: bool) -> None:
    draw.rounded_rectangle((x, y, x + size, y + size), radius=3, outline="#b88667", width=2, fill="#fff")
    if not checked:
        return
    draw.rounded_rectangle((x, y, x + size, y + size), radius=3, outline="#911a24", width=2, fill="#911a24")
    draw.line((x + 4, y + 8, x + 7, y + 12), fill="#fff", width=2)
    draw.line((x + 7, y + 12, x + 13, y + 4), fill="#fff", width=2)


def build_agenda_image(agenda: dict[str, Any]) -> Image.Image:
    dpi = 150
    width = int(8.5 * dpi)
    height = int(11 * dpi)
    image = Image.new("RGB", (width, height), "#f8efea")
    draw = ImageDraw.Draw(image)

    f_title = _load_font(40, bold=True)
    f_subtitle = _load_font(21, bold=True)
    f_label = _load_font(16, bold=True)
    f_body = _load_font(16)
    f_small = _load_font(15)
    f_table_head = _load_font(15, bold=True)
    f_summary_value = _load_font(34, bold=True)

    margin = int((1 / 2.54) * dpi)
    panel_radius = 18

    draw.rounded_rectangle((margin, margin, width - margin, height - margin), radius=panel_radius, fill="#fff8f4", outline="#8f1f29", width=3)

    head_y = margin + 12
    center_x = width // 2
    title = "GUANACOPAN FRANCES"
    title_bbox = draw.textbbox((0, 0), title, font=f_title)
    draw.text((center_x - (title_bbox[2] - title_bbox[0]) // 2, head_y), title, font=f_title, fill="#4a1717")

    subtitle = "Turno: AM"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=f_subtitle)
    subtitle_y = head_y + 46
    draw.text((center_x - (subtitle_bbox[2] - subtitle_bbox[0]) // 2, subtitle_y), subtitle, font=f_subtitle, fill="#4a1717")

    employee_label_x = width - margin - 240
    draw.text((employee_label_x, head_y + 8), "Empleado", font=f_label, fill="#6d4031")
    employee_box = (employee_label_x, head_y + 30, width - margin - 18, head_y + 64)
    draw.rounded_rectangle(employee_box, radius=8, fill="#fffdfb", outline=COLOR_BORDER, width=1)
    draw.text((employee_box[0] + 8, employee_box[1] + 6), _safe_text(agenda.get("employee_name")), font=f_body, fill="#4b1d1d")
    draw.polygon([(employee_box[2] - 16, employee_box[1] + 10), (employee_box[2] - 8, employee_box[1] + 10), (employee_box[2] - 12, employee_box[1] + 16)], fill="#6d4031")

    meta_top = subtitle_y + 40
    meta_left = margin + 14
    meta_mid_gap = 16
    summary_w = 220
    meta_right = width - margin - 14
    info_box = (meta_left, meta_top, meta_right - summary_w - meta_mid_gap, meta_top + 124)
    draw.rounded_rectangle(info_box, radius=14, fill="#fffdfb", outline=COLOR_BORDER, width=1)
    draw.text((info_box[0] + 12, info_box[1] + 12), f"Dia: {_safe_text(agenda.get('day_name'))}", font=f_body, fill="#4b1d1d")
    draw.text((info_box[0] + 12, info_box[1] + 40), f"Fecha: {_safe_text(agenda.get('date_text'))}", font=f_body, fill="#4b1d1d")
    draw.text((info_box[0] + 12, info_box[1] + 68), f"Hora entrada con uniforme: {_safe_text(agenda.get('entry_time'))}", font=f_body, fill="#4b1d1d")
    draw.text((info_box[0] + 12, info_box[1] + 96), f"Hora salida: {_safe_text(agenda.get('exit_time'))}", font=f_body, fill="#4b1d1d")

    stat_gap = 10
    stat_w = (summary_w - stat_gap) // 2
    stat1 = (info_box[2] + meta_mid_gap, meta_top + 10, info_box[2] + meta_mid_gap + stat_w, meta_top + 84)
    stat2 = (stat1[2] + stat_gap, meta_top + 10, stat1[2] + stat_gap + stat_w, meta_top + 84)
    for box, label, value in (
        (stat1, "COMPLETADAS", str(agenda.get("completed_count") or 0)),
        (stat2, "PENDIENTES", str(agenda.get("pending_count") or 0)),
    ):
        draw.rounded_rectangle(box, radius=14, fill="#f7e8de", outline=COLOR_BORDER, width=1)
        draw.text((box[0] + 10, box[1] + 10), label, font=f_small, fill="#8b5d45")
        draw.text((box[0] + 10, box[1] + 34), value, font=f_summary_value, fill="#7b1221")

    table_top = meta_top + 140
    table_left = margin + 14
    table_right = width - margin - 14
    table_width = table_right - table_left
    tasks: list[dict[str, Any]] = list(agenda.get("tasks", []))
    header_h = 32
    footer_h = 96
    available_h = height - margin - 16 - footer_h - table_top
    rows_count = max(1, len(tasks))
    row_h = max(24, min(34, available_h // rows_count))
    table_bottom = table_top + header_h + row_h * rows_count
    check_col_w = 56
    label_col_w = table_width - check_col_w

    draw.rounded_rectangle((table_left, table_top, table_right, table_bottom), radius=12, fill="#fffdfb", outline=COLOR_BORDER, width=1)
    draw.rectangle((table_left, table_top, table_right, table_top + header_h), fill="#f7e8de")
    draw.text((table_left + 8, table_top + 6), "RESPONSABILIDAD", font=f_table_head, fill="#4a1717")

    check_x = table_left + label_col_w
    draw.line((check_x, table_top, check_x, table_bottom), fill=COLOR_BORDER, width=1)
    draw.text((check_x + 6, table_top + 8), "CHECK", font=f_table_head, fill="#4a1717")

    y = table_top + header_h
    for task in tasks:
        draw.line((table_left, y, table_right, y), fill=COLOR_BORDER, width=1)
        label = _truncate_to_width(draw, _safe_text(task.get("label")), f_small, label_col_w - 12)
        draw.text((table_left + 6, y + 7), label, font=f_small, fill="#482120")
        _draw_checkbox(draw, check_x + 18, y + 6, 18, bool(task.get("checked")))
        y += row_h
    draw.line((table_left, table_bottom, table_right, table_bottom), fill=COLOR_BORDER, width=1)

    footer_top = table_bottom + 12
    footer_box = (table_left, footer_top, table_right, height - margin - 14)
    draw.rounded_rectangle(footer_box, radius=14, fill="#fffdfb", outline=COLOR_BORDER, width=1)
    draw.text((footer_box[0] + 12, footer_box[1] + 10), "CIERRE", font=f_label, fill="#6d4031")

    photo_y = footer_box[1] + 34
    photo_label = "Foto enviada al grupo:"
    draw.text((footer_box[0] + 12, photo_y), photo_label, font=f_body, fill="#4b1d1d")
    photo_label_w = int(draw.textlength(photo_label, font=f_body))
    checkbox_x = footer_box[0] + 12 + photo_label_w + 12
    _draw_checkbox(draw, checkbox_x, photo_y + 2, 16, bool(agenda.get("photo_sent")))
    draw.text((checkbox_x + 24, photo_y), "Si", font=f_body, fill="#4b1d1d")

    hour_y = photo_y + 24
    draw.text((footer_box[0] + 12, hour_y), "Hora", font=f_body, fill="#4b1d1d")
    hour_box = (footer_box[0] + 12, hour_y + 16, footer_box[0] + 320, hour_y + 38)
    draw.rounded_rectangle(hour_box, radius=7, fill="#fff", outline=COLOR_BORDER, width=1)
    draw.text((hour_box[0] + 8, hour_box[1] + 5), _safe_text(agenda.get("photo_hour")), font=f_small, fill="#4b1d1d")

    return image


def build_agenda_jpg_bytes(agenda: dict[str, Any]) -> bytes:
    image = build_agenda_image(agenda)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def build_agenda_pdf_bytes(agenda: dict[str, Any]) -> bytes:
    image = build_agenda_image(agenda).convert("RGB")
    output = io.BytesIO()
    image.save(output, format="PDF", resolution=150.0)
    return output.getvalue()
