import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.REST.model.products.product_orm import BannedNameORM, CategoryORM, ProductORM


class ValidationError(Exception):
    pass


class ConflictError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


ERROR_CODES = {
    ValidationError: 422,
    ConflictError: 409,
    ResourceNotFoundError: 400,
}


def validate_product_name(product_name: str):
    if not isinstance(product_name, str) or not re.fullmatch(r"[A-Za-z0-9]{3,20}", product_name):
        raise ValidationError(
            "Product name must be between 3 and 20 characters long and contain only letters and digits."
        )


def validate_available_quantity(available_quantity: int):
    if available_quantity < 0:
        raise ValidationError("Available quantity cannot be negative.")


def validate_price_for_category(price: float, category: CategoryORM):
    if not float(category.min_price) <= float(price) <= float(category.max_price):
        raise ValidationError(
            f"Price for '{category.name}' must be between "
            f"{category.min_price} and {category.max_price}."
        )


def validate_category_exists(db: Session, category_id: int):
    category = db.execute(
        select(CategoryORM).where(CategoryORM.id == category_id)
    ).scalar_one_or_none()
    if category is None:
        raise ResourceNotFoundError(f"Category with id {category_id} does not exist.")
    return category


def validate_product_name_unique(
    db: Session, product_name: str, excluded_product_id: int | None = None
):
    query = select(ProductORM).where(func.lower(ProductORM.name) == product_name.lower())
    if excluded_product_id is not None:
        query = query.where(ProductORM.id != excluded_product_id)
    if db.execute(query).scalar_one_or_none() is not None:
        raise ConflictError(f"Product with name '{product_name}' already exists.")


def validate_banned_name(db: Session, product_name: str):
    banned_name = db.execute(
        select(BannedNameORM.name).where(func.lower(BannedNameORM.name) == product_name.lower())
    ).scalar_one_or_none()
    if banned_name is not None:
        raise ValidationError(f"Product name '{product_name}' is forbidden.")
