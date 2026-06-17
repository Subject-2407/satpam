from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import close_driver, init_driver
from app.routers import analysis, auth, health, import_data, reports


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(import_data.router)
app.include_router(analysis.router)
