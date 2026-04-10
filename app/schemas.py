from __future__ import annotations

from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: int
    supplier: str
    name: str


class OrderItemIn(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    note: str | None = None


class CreateOrderRequest(BaseModel):
    supplier_name: str
    notes: str | None = None
    items: list[OrderItemIn]


class CreateOrderResponse(BaseModel):
    order_id: int
    supplier_name: str
    total: float
    created_at: str


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    note: str | None = None


class OrderDetailOut(BaseModel):
    id: int
    employee_name: str
    supplier_name: str
    notes: str | None = None
    created_at: str
    total: float
    items: list[OrderItemOut]
