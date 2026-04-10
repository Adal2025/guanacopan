from __future__ import annotations

import io
import textwrap
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BUSINESS_NAME = "Guanacopan Francés"
BUSINESS_TITLE = "Orden de productos"
BUSINESS_ADDRESS = "Entre, Avenida Jose Simeon Canas Sur 46, San Miguel."
BUSINESS_PHONE = "64435199"

COLOR_RED = "#f00000"
COLOR_MAROON = "#501010"
COLOR_GOLD = "#c07030"
COLOR_CREAM = "#f8f2e6"
COLOR_TEXT = "#2e1414"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
        )

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue

    return ImageFont.load_default()


def _format_qty(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def build_order_image(order: dict[str, Any]) -> Image.Image:
    items = order.get("items", [])
    notes = _safe_text(order.get("notes"))

    width = 1450
    top_pad = 50
    header_block = 250
    table_header_h = 40
    row_h = 38
    notes_h = 70 if notes else 20
    bottom_pad = 40

    height = top_pad + header_block + table_header_h + max(1, len(items)) * row_h + notes_h + bottom_pad
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    f_brand = _load_font(46, bold=True)
    f_title = _load_font(26, bold=True)
    f_meta = _load_font(22)
    f_table_head = _load_font(20, bold=True)
    f_table = _load_font(19)
    f_notes = _load_font(20)

    draw.rectangle([(36, top_pad - 10), (width - 36, top_pad + 88)], fill=COLOR_RED)
    draw.text((56, top_pad), BUSINESS_NAME, font=f_brand, fill="white")
    draw.text((56, top_pad + 100), BUSINESS_TITLE.upper(), font=f_title, fill=COLOR_MAROON)

    meta_top = top_pad + 145
    draw.text((56, meta_top), f"Fecha del pedido: {_safe_text(order.get('created_at_local') or order.get('created_at'))}", font=f_meta, fill=COLOR_TEXT)
    draw.text((760, meta_top), f"Proveedor: {_safe_text(order.get('supplier_name'))}", font=f_meta, fill=COLOR_TEXT)
    draw.text((56, meta_top + 36), f"Dirección: {BUSINESS_ADDRESS}", font=f_meta, fill=COLOR_TEXT)
    draw.text((56, meta_top + 72), f"Teléfono: {BUSINESS_PHONE}", font=f_meta, fill=COLOR_TEXT)

    left = 36
    right = width - 36
    table_top = top_pad + header_block
    draw.rectangle([(left, table_top), (right, table_top + table_header_h)], fill=COLOR_MAROON)

    col_qty = left + 150
    col_product = left + 970

    draw.text((left + 14, table_top + 9), "Cantidad", font=f_table_head, fill="white")
    draw.text((col_qty + 14, table_top + 9), "Producto (Descripción Exacta del Proveedor)", font=f_table_head, fill="white")
    draw.text((col_product + 14, table_top + 9), "Notas", font=f_table_head, fill="white")

    y = table_top + table_header_h
    rows_to_draw = items if items else [{"quantity": "", "product_name": "Sin productos", "note": ""}]

    for idx, item in enumerate(rows_to_draw):
        fill = COLOR_CREAM if idx % 2 == 0 else "#fffdf9"
        draw.rectangle([(left, y), (right, y + row_h)], fill=fill)
        draw.line([(left, y), (right, y)], fill="#e8d8c8", width=1)

        qty_text = _format_qty(float(item.get("quantity", 0))) if item.get("quantity") not in ("", None) else ""
        product_text = _safe_text(item.get("product_name"))
        note_text = _safe_text(item.get("note"))

        draw.text((left + 14, y + 8), qty_text, font=f_table, fill=COLOR_TEXT)
        draw.text((col_qty + 14, y + 8), textwrap.shorten(product_text, width=72, placeholder="..."), font=f_table, fill=COLOR_TEXT)
        draw.text((col_product + 14, y + 8), textwrap.shorten(note_text, width=34, placeholder="..."), font=f_table, fill=COLOR_TEXT)

        y += row_h

    draw.line([(left, y), (right, y)], fill="#d5c0ac", width=2)
    draw.line([(col_qty, table_top), (col_qty, y)], fill="#d9c8b8", width=1)
    draw.line([(col_product, table_top), (col_product, y)], fill="#d9c8b8", width=1)
    draw.rectangle([(left, table_top), (right, y)], outline="#c9b39d", width=1)

    if notes:
        draw.text((56, y + 20), f"Notas generales: {notes}", font=f_notes, fill=COLOR_MAROON)

    return image


def build_order_jpg_bytes(order: dict[str, Any]) -> bytes:
    image = build_order_image(order)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=92)
    return output.getvalue()


def build_order_pdf_bytes(order: dict[str, Any]) -> bytes:
    image = build_order_image(order).convert("RGB")
    output = io.BytesIO()
    image.save(output, format="PDF", resolution=150.0)
    return output.getvalue()
