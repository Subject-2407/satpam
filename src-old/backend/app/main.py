from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_driver, init_driver
from app.routers import (
    admin,
    alerts,
    analysis,
    auth,
    blacklist,
    dashboard,
    entities,
    export,
    health,
    import_data,
    intel,
    reports,
    verification,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_driver()
    yield
    await close_driver()


app = FastAPI(
    title="SATPAM API",
    description=(
        "Search-based AI Threat Prevention and Mapping — "
        "Prototype backend untuk sistem graph intelligence deteksi risiko judol/pinjol ilegal. "
        "Semua data bersifat dummy/simulasi."
    ),
    version="0.1.0-week1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(import_data.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(entities.router)
app.include_router(alerts.router)
app.include_router(verification.router)
app.include_router(blacklist.router)
app.include_router(intel.router)
app.include_router(export.router)
app.include_router(admin.router)
