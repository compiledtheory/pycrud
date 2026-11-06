from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.REST.data.database import Base


class CategoryORM(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    min_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    max_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    products: Mapped[list["ProductORM"]] = relationship(back_populates="category")


class BannedNameORM(Base):
    __tablename__ = "banned_name"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class ProductORM(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), nullable=False)

    category: Mapped[CategoryORM] = relationship(back_populates="products")
