from fastapi import FastAPI

from app.REST.web.router import product_router
from app.notifications.docs_app import notifications_docs_app
from app.notifications.web.router import router as notifications_router

from contextlib import asynccontextmanager
from threading import Thread
from app.notifications.service.notification_worker import run_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = Thread(target=run_worker, daemon=True)
    thread.start()
    yield

app = FastAPI(
    title="Product CRUD",
    lifespan=lifespan,
)

app.include_router(product_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")

app.mount("/notifications-docs", notifications_docs_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
