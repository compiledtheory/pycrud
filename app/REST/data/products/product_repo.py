from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.REST.model.products.product_orm import ProductORM


def get_all_product(db: Session):
    query = select(ProductORM).options(joinedload(ProductORM.category))
    return db.execute(query).scalars().all()


def get_product_by_id(product_id: int, db: Session):
    query = (
        select(ProductORM)
        .options(joinedload(ProductORM.category))
        .where(ProductORM.id == product_id)
    )
    return db.execute(query).scalars().first()


def add_product(product: ProductORM, db: Session):
    db.add(product)
    db.flush()
    db.refresh(product)
    return product


def save_product(product: ProductORM, db: Session):
    db.add(product)
    db.flush()
    db.refresh(product)
    return product


def delete_product(product: ProductORM, db: Session):
    db.delete(product)
    db.flush()
