from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    min_price: float
    max_price: float


class Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    available_quantity: int
    category: Category


class ProductCreate(BaseModel):
    name: str
    price: float
    available_quantity: int = 0
    category_id: int


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    available_quantity: int | None = None
    category_id: int | None = None


class ProductHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    action: str
    previous_state: dict | None = None
    current_state: dict | None = None
    changed_at: datetime
