from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_SUPPLIERS = ("El Rodeo", "Todito", "Pricemart", "Emma Bakery")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sku TEXT NOT NULL DEFAULT '',
    unit TEXT NOT NULL,
    price REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    UNIQUE (supplier_id, name, sku)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT NOT NULL,
    supplier_name TEXT NOT NULL DEFAULT '',
    notes TEXT,
    created_at TEXT NOT NULL,
    total REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity REAL NOT NULL,
    item_note TEXT NOT NULL DEFAULT '',
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db(db_path: str, products_csv_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        _ensure_column(conn, "orders", "supplier_name", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "order_items", "item_note", "TEXT NOT NULL DEFAULT ''")
        _sync_products(conn, products_csv_path)
        _reset_orders_once(conn, db_path, "2026-04-15-clean-start")


def _reset_orders_once(conn: sqlite3.Connection, db_path: str, reset_key: str) -> None:
    marker_name = f".orders-reset-{reset_key}.marker"
    marker_path = Path(db_path).with_name(marker_name)
    if marker_path.exists():
        return

    conn.execute("DELETE FROM order_items")
    conn.execute("DELETE FROM orders")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('orders', 'order_items')")
    marker_path.write_text("reset complete\n", encoding="utf-8")


def _sync_products(conn: sqlite3.Connection, products_csv_path: str) -> None:
    for supplier_name in EXPECTED_SUPPLIERS:
        conn.execute("INSERT OR IGNORE INTO suppliers (name) VALUES (?)", (supplier_name,))

    conn.execute("UPDATE products SET is_active = 0")

    with Path(products_csv_path).open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            supplier_name = (row.get("supplier") or "").strip()
            if supplier_name not in EXPECTED_SUPPLIERS:
                continue

            product_name = (row.get("name") or "").strip()
            unit = (row.get("unit") or "unidad").strip() or "unidad"
            sku = (row.get("sku") or "").strip()

            if not product_name:
                continue

            try:
                price = float(row.get("price") or 0)
            except ValueError:
                price = 0.0

            supplier_id = conn.execute("SELECT id FROM suppliers WHERE name = ?", (supplier_name,)).fetchone()["id"]

            conn.execute(
                """
                INSERT INTO products (supplier_id, name, sku, unit, price, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(supplier_id, name, sku)
                DO UPDATE SET
                    unit = excluded.unit,
                    price = excluded.price,
                    is_active = 1
                """,
                (supplier_id, product_name, sku, unit, price),
            )


def fetch_products(db_path: str) -> list[dict[str, Any]]:
    placeholders = ", ".join("?" for _ in EXPECTED_SUPPLIERS)

    with _connect(db_path) as conn:
        rows = conn.execute(
            f"""
            SELECT
                p.id,
                s.name AS supplier,
                p.name,
                p.sku,
                p.unit,
                p.price
            FROM products p
            JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.is_active = 1
              AND s.name IN ({placeholders})
            ORDER BY s.name, p.name
            """,
            EXPECTED_SUPPLIERS,
        ).fetchall()

    return [dict(row) for row in rows]


def _validate_and_build_line_items(
    conn: sqlite3.Connection,
    supplier_name: str,
    items: list[dict[str, Any]],
) -> tuple[float, list[dict[str, Any]]]:
    valid_items = [item for item in items if float(item.get("quantity", 0)) > 0]
    if not valid_items:
        raise ValueError("Debes agregar al menos un producto con cantidad mayor a 0.")

    total = 0.0
    line_items: list[dict[str, Any]] = []

    for item in valid_items:
        product_id = int(item.get("product_id"))
        quantity = float(item.get("quantity"))
        item_note = str(item.get("note") or "").strip()
        if quantity <= 0:
            continue

        product = conn.execute(
            """
            SELECT p.id, p.price, p.name, s.name AS supplier
            FROM products p
            JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.id = ? AND p.is_active = 1
            """,
            (product_id,),
        ).fetchone()
        if not product:
            raise ValueError(f"Producto inválido: {product_id}")

        if product["supplier"] != supplier_name:
            raise ValueError("Todos los productos deben pertenecer al proveedor seleccionado.")

        unit_price = float(product["price"])
        line_total = round(unit_price * quantity, 2)
        total += line_total

        line_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "item_note": item_note,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    total = round(total, 2)
    if not line_items:
        raise ValueError("No hay productos válidos para guardar.")

    return total, line_items


def create_order(
    db_path: str,
    employee_name: str,
    supplier_name: str,
    notes: str | None,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    if not employee_name.strip():
        raise ValueError("El usuario es obligatorio.")

    supplier_name = supplier_name.strip()
    if supplier_name not in EXPECTED_SUPPLIERS:
        raise ValueError("Proveedor inválido.")

    created_at = datetime.now(timezone.utc).isoformat()

    with _connect(db_path) as conn:
        total, line_items = _validate_and_build_line_items(conn, supplier_name, items)

        cursor = conn.execute(
            """
            INSERT INTO orders (employee_name, supplier_name, notes, created_at, total)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_name.strip(), supplier_name, (notes or "").strip(), created_at, total),
        )
        order_id = int(cursor.lastrowid)

        conn.executemany(
            """
            INSERT INTO order_items (order_id, product_id, quantity, item_note, unit_price, line_total)
            VALUES (:order_id, :product_id, :quantity, :item_note, :unit_price, :line_total)
            """,
            [{**line_item, "order_id": order_id} for line_item in line_items],
        )

    return {
        "order_id": order_id,
        "supplier_name": supplier_name,
        "total": total,
        "created_at": created_at,
    }


def update_order(
    db_path: str,
    order_id: int,
    employee_name: str,
    supplier_name: str,
    notes: str | None,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    if not employee_name.strip():
        raise ValueError("El usuario es obligatorio.")

    supplier_name = supplier_name.strip()
    if supplier_name not in EXPECTED_SUPPLIERS:
        raise ValueError("Proveedor inválido.")

    with _connect(db_path) as conn:
        existing = conn.execute(
            "SELECT id, created_at FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if not existing:
            raise ValueError("Pedido no encontrado.")

        total, line_items = _validate_and_build_line_items(conn, supplier_name, items)

        conn.execute(
            """
            UPDATE orders
            SET employee_name = ?, supplier_name = ?, notes = ?, total = ?
            WHERE id = ?
            """,
            (employee_name.strip(), supplier_name, (notes or "").strip(), total, order_id),
        )

        conn.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        conn.executemany(
            """
            INSERT INTO order_items (order_id, product_id, quantity, item_note, unit_price, line_total)
            VALUES (:order_id, :product_id, :quantity, :item_note, :unit_price, :line_total)
            """,
            [{**line_item, "order_id": order_id} for line_item in line_items],
        )

    return {
        "order_id": order_id,
        "supplier_name": supplier_name,
        "total": total,
        "created_at": existing["created_at"],
    }


def delete_order(db_path: str, order_id: int) -> None:
    with _connect(db_path) as conn:
        exists = conn.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not exists:
            raise ValueError("Pedido no encontrado.")

        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))


def list_orders(db_path: str, limit: int = 30) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                o.id,
                o.employee_name,
                o.supplier_name,
                o.notes,
                o.created_at,
                o.total,
                COUNT(oi.id) AS item_count
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.id
            ORDER BY o.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_order(db_path: str, order_id: int) -> dict[str, Any]:
    with _connect(db_path) as conn:
        order = conn.execute(
            """
            SELECT id, employee_name, supplier_name, notes, created_at, total
            FROM orders
            WHERE id = ?
            """,
            (order_id,),
        ).fetchone()
        if not order:
            raise ValueError("Pedido no encontrado.")

        rows = conn.execute(
            """
            SELECT
                oi.product_id,
                p.name AS product_name,
                oi.quantity,
                oi.item_note
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.id
            """,
            (order_id,),
        ).fetchall()

    return {
        "id": int(order["id"]),
        "employee_name": order["employee_name"],
        "supplier_name": order["supplier_name"],
        "notes": order["notes"] or "",
        "created_at": order["created_at"],
        "total": float(order["total"]),
        "items": [
            {
                "product_id": int(row["product_id"]),
                "product_name": row["product_name"],
                "quantity": float(row["quantity"]),
                "note": row["item_note"] or "",
            }
            for row in rows
        ],
    }


def build_order_csv(db_path: str, order_id: int) -> str:
    order = get_order(db_path, order_id)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Pedido", order["id"]])
    writer.writerow(["Usuario", order["employee_name"]])
    writer.writerow(["Proveedor", order["supplier_name"]])
    writer.writerow(["Fecha UTC", order["created_at"]])
    writer.writerow(["Notas generales", order["notes"] or ""])
    writer.writerow([])
    writer.writerow(["Cantidad", "Producto (Descripción Exacta del Proveedor)", "Notas"])

    for row in order["items"]:
        writer.writerow([row["quantity"], row["product_name"], row["note"] or ""])

    return output.getvalue()
