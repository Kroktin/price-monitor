"""HTTP API демо мониторинга цен: тестовые магазины, запуск парсера, данные дашборда."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Header, HTTPException, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402

from _pm.catalog import SHOPS, today  # noqa: E402
from _pm.service import Service  # noqa: E402
from _pm.shops import RENDER  # noqa: E402
from _pm.storage import get_store  # noqa: E402

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
# CORS только для локальной разработки: на проде дашборд и API на одном домене через прокси.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])


def service() -> Service:
    return Service(get_store())


def shop_base(request: Request) -> str:
    return os.getenv("SHOP_BASE_URL") or str(request.base_url).rstrip("/") + "/api/py/shops"


@app.get("/api/py/health")
async def health():
    return {"ok": True}


@app.get("/api/py/shops/{shop}", response_class=HTMLResponse)
async def shop_page(shop: str):
    if shop not in SHOPS:
        raise HTTPException(404, "shop not found")
    return HTMLResponse(RENDER[shop](today()), headers={"Cache-Control": "no-store"})


@app.get("/api/py/dashboard")
async def dashboard():
    return await service().dashboard()


@app.post("/api/py/scrape")
async def scrape_now(request: Request):
    return await service().run(shop_base(request), trigger="button")


@app.get("/api/py/cron")
async def cron(request: Request, authorization: str | None = Header(default=None)):
    secret = os.getenv("CRON_SECRET")
    if not secret or authorization != f"Bearer {secret}":
        raise HTTPException(403, "forbidden")
    return await service().run(shop_base(request), trigger="cron")
