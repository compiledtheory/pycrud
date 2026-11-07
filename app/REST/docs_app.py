from fastapi import FastAPI
from app.REST.web.router import product_router

product_docs_app = FastAPI(
    title="Products API",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)
product_docs_app.include_router(product_router)