from sqlalchemy.orm import Session

from app.REST.data.products import product_repo
from app.REST.data.products.product_history_repo import (
    add_product_history,
    get_product_history_by_product_id,
)
from app.REST.model.products.product_history_orm import ProductHistoryORM
from app.REST.model.products.product_orm import CategoryORM, ProductORM
from app.REST.model.products.product_schema import ProductCreate, ProductUpdate
from app.REST.service.products.product_validators import (
    validate_available_quantity,
    validate_banned_name,
    validate_category_exists,
    validate_price_for_category,
    validate_product_name,
    validate_product_name_unique,
)


def fetch_products_service(db: Session):
    return product_repo.get_all_product(db)


def fetch_products_for_id_service(product_id: int, db: Session):
    return product_repo.get_product_by_id(product_id, db)


def _build_product_snapshot(product: ProductORM | None):
    if product is None:
        return None
    category = product.category
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "available_quantity": product.available_quantity,
        "category": {"id": category.id, "name": category.name},
    }


def _save_product_history(
    db: Session,
    product_id: int,
    action: str,
    previous_state: dict | None,
    current_state: dict | None,
):
    history_entry = ProductHistoryORM(
        product_id=product_id,
        action=action,
        previous_state=previous_state,
        current_state=current_state,
    )
    return add_product_history(db, history_entry)


def _commit_history(
    db: Session,
    product_id: int,
    action: str,
    previous_state: dict | None,
    current_state: dict | None,
):
    try:
        _save_product_history(db, product_id, action, previous_state, current_state)
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_product_history(db: Session, product_id: int):
    return get_product_history_by_product_id(db, product_id)


def _validate_name(db: Session, name: str, product_id: int | None = None):
    validate_product_name(name)
    validate_banned_name(db, name)
    validate_product_name_unique(db, name, product_id)


def _validate_price_and_quantity(
    db: Session,
    price: float,
    quantity: int,
    category_id: int,
) -> CategoryORM:
    category = validate_category_exists(db, category_id)
    validate_price_for_category(price, category)
    validate_available_quantity(quantity)
    return category


def create_product(payload: ProductCreate, db: Session):
    _validate_name(db, payload.name)
    category = _validate_price_and_quantity(
        db, payload.price, payload.available_quantity, payload.category_id
    )
    product = ProductORM(
        name=payload.name,
        price=payload.price,
        available_quantity=payload.available_quantity,
        category=category,
    )
    try:
        created_product = product_repo.add_product(product, db)
        snapshot = _build_product_snapshot(created_product)
        _save_product_history(db, created_product.id, "CREATE", None, snapshot)
        db.commit()
        db.refresh(created_product)
        return created_product
    except Exception:
        db.rollback()
        raise


def replace_product(product_id: int, payload: ProductCreate, db: Session):
    product = product_repo.get_product_by_id(product_id, db)
    if product is None:
        return None

    previous_state = _build_product_snapshot(product)
    _validate_name(db, payload.name, product_id)
    category = _validate_price_and_quantity(
        db, payload.price, payload.available_quantity, payload.category_id
    )

    product.name = payload.name
    product.price = payload.price
    product.available_quantity = payload.available_quantity
    product.category = category
    try:
        updated_product = product_repo.save_product(product, db)
        current_state = _build_product_snapshot(updated_product)
        _save_product_history(db, product_id, "REPLACE", previous_state, current_state)
        db.commit()
        db.refresh(updated_product)
        return updated_product
    except Exception:
        db.rollback()
        raise


def patch_product(product_id: int, payload: ProductUpdate, db: Session):
    product = product_repo.get_product_by_id(product_id, db)
    if product is None:
        return None

    previous_state = _build_product_snapshot(product)
    if payload.name is not None:
        _validate_name(db, payload.name, product_id)
        product.name = payload.name

    category = product.category
    if payload.category_id is not None:
        category = validate_category_exists(db, payload.category_id)
        product.category = category

    effective_price = payload.price if payload.price is not None else product.price
    effective_quantity = (
        payload.available_quantity
        if payload.available_quantity is not None
        else product.available_quantity
    )
    validate_price_for_category(effective_price, category)
    validate_available_quantity(effective_quantity)

    if payload.price is not None:
        product.price = payload.price
    if payload.available_quantity is not None:
        product.available_quantity = payload.available_quantity

    try:
        updated_product = product_repo.save_product(product, db)
        current_state = _build_product_snapshot(updated_product)
        _save_product_history(db, product_id, "UPDATE", previous_state, current_state)
        db.commit()
        db.refresh(updated_product)
        return updated_product
    except Exception:
        db.rollback()
        raise


def delete_product(product_id: int, db: Session):
    product = product_repo.get_product_by_id(product_id, db)
    if product is None:
        return False

    previous_state = _build_product_snapshot(product)
    try:
        product_repo.delete_product(product, db)
        _save_product_history(db, product_id, "DELETE", previous_state, None)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
