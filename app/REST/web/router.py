from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.REST.data.database import get_db
from app.REST.model.products.product_schema import (
	Product,
	ProductCreate,
	ProductHistoryEntry,
	ProductUpdate,
)
from app.REST.service.products import product_service
from app.REST.service.products.product_validators import (
	ConflictError,
	ERROR_CODES,
	ResourceNotFoundError,
	ValidationError,
)

product_router = APIRouter(tags=["Products"])


@product_router.get("/")
def root() -> dict:
	return {"hello": "world"}


@product_router.get("/products", response_model=list[Product])
def get_products(db: Session = Depends(get_db)):
	return product_service.fetch_products_service(db)


@product_router.get("/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
	product = product_service.fetch_products_for_id_service(product_id, db)
	if product is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
	return product


@product_router.get(
	"/products/{product_id}/history", response_model=list[ProductHistoryEntry]
)
def get_product_history(product_id: int, db: Session = Depends(get_db)):
	history = product_service.list_product_history(db, product_id)
	if not history:
		raise HTTPException(status_code=404, detail="Product history not found")
	return history


def _raise_domain_http_error(exc: Exception):
	raise HTTPException(status_code=ERROR_CODES[type(exc)], detail=str(exc)) from exc


@product_router.post("/products", response_model=Product, status_code=201)
def post_product(payload: ProductCreate, db: Session = Depends(get_db)):
	try:
		return product_service.create_product(payload, db)
	except (ValidationError, ConflictError, ResourceNotFoundError) as exc:
		_raise_domain_http_error(exc)


@product_router.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
	try:
		product = product_service.replace_product(product_id, payload, db)
	except (ValidationError, ConflictError, ResourceNotFoundError) as exc:
		_raise_domain_http_error(exc)
	if product is None:
		raise HTTPException(status_code=404, detail="Product not found")
	return product


@product_router.patch("/products/{product_id}", response_model=Product)
def patch_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
	try:
		product = product_service.patch_product(product_id, payload, db)
	except (ValidationError, ConflictError, ResourceNotFoundError) as exc:
		_raise_domain_http_error(exc)
	if product is None:
		raise HTTPException(status_code=404, detail="Product not found")
	return product


@product_router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
	if not product_service.delete_product(product_id, db):
		raise HTTPException(status_code=404, detail="Product not found")
	return Response(status_code=204)
