from fastapi import FastAPI

from app.REST.web.router import product_router

app = FastAPI()
app.include_router(product_router)
