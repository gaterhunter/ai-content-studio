from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .db import Base, engine
from .llm import LLMError, get_llm
from .routers import analytics, contents, ideas, personas, settings, trends


@asynccontextmanager
async def lifespan(_: FastAPI):
    # MVP: tạo bảng tự động. Khi lên PostgreSQL production nên chuyển sang Alembic.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="AI Content Studio", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(LLMError)
async def llm_error_handler(_: Request, exc: LLMError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"ok": True, "llm": get_llm().name}


for r in (personas.router, trends.router, ideas.router, contents.router, analytics.router, settings.router):
    app.include_router(r, prefix="/api")
