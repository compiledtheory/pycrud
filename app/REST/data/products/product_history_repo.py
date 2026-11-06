from sqlalchemy import select
from sqlalchemy.orm import Session

from app.REST.model.products.product_history_orm import ProductHistoryORM


def get_product_history_by_product_id(db: Session, product_id: int):
    query = (
        select(ProductHistoryORM)
        .where(ProductHistoryORM.product_id == product_id)
        .order_by(ProductHistoryORM.id.desc())
    )
    return db.execute(query).scalars().all()


def add_product_history(db: Session, history_entry: ProductHistoryORM):
    db.add(history_entry)
    db.flush()
    db.refresh(history_entry)
    return history_entry
