from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, create_all_tables
from app.routers import auth, core, inventory, sales, tax, ecommerce, hr, alerts, logistics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialise DB and create tables (dev mode)
    init_db(settings.DATABASE_URL)
    if settings.DEBUG:
        await create_all_tables()
    yield
    # Shutdown: nothing special needed


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(core.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(tax.router)
app.include_router(ecommerce.router)
app.include_router(hr.router)
app.include_router(alerts.router)
app.include_router(logistics.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
