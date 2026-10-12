"""
Парсер цен. Три магазина с разной разметкой и один реальный внешний сайт.

- МегаТех: карточки, CSS-селекторы
- Цифра+: таблица прайса, цена в атрибуте content
- ЭлектроМир: цена рисуется JS, поэтому берем структурированные данные JSON-LD
- books.toscrape.com: реальный сайт-песочница для парсинга
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field

import httpx
from selectolax.parser import HTMLParser

from .catalog import SHOPS

BOOKS_URL = "https://books.toscrape.com/catalogue/page-1.html"
HEADERS = {"User-Agent": "PriceMonitorDemo/1.0 (+portfolio demo)"}


@dataclass
class SourceResult:
    source: str
    url: str
    ok: bool = False
    ms: int = 0
    found: int = 0
    error: str = ""
    prices: dict = field(default_factory=dict)  # sku -> цена или None (нет в наличии)
    books: list = field(default_factory=list)


def digits(text: str) -> int | None:
    d = re.sub(r"[^\d]", "", text or "")
    return int(d) if d else None


def art_map(shop: str) -> dict[str, str]:
    return {art: sku for sku, (_, art) in SHOPS[shop]["items"].items()}


def parse_megatech(html: str) -> dict:
    tree, arts, out = HTMLParser(html), art_map("megatech"), {}
    for card in tree.css("div.product-card"):
        sku = arts.get(card.attributes.get("data-article", ""))
        if not sku:
            continue
        price = card.css_first(".price")
        out[sku] = None if price is None or "price--na" in (price.attributes.get("class") or "") else digits(price.text())
    return out


def parse_cifra(html: str) -> dict:
    tree, arts, out = HTMLParser(html), art_map("cifra"), {}
    for row in tree.css("#price-list tbody tr"):
        sku = arts.get(row.attributes.get("data-code", ""))
        if not sku:
            continue
        cost = row.css_first("td.cost")
        out[sku] = digits(cost.attributes.get("content", "")) if cost is not None and cost.attributes.get("content") else None
    return out


def parse_elmir(html: str) -> dict:
    tree, arts, out = HTMLParser(html), art_map("elmir"), {}
    for node in tree.css('script[type="application/ld+json"]'):
        data = json.loads(node.text())
        for item in data.get("itemListElement", []):
            sku = arts.get(item.get("sku", ""))
            if not sku:
                continue
            offer = item.get("offers", {})
            in_stock = offer.get("availability", "").endswith("InStock")
            out[sku] = int(float(offer.get("price") or 0)) if in_stock else None
    return out


def parse_books(html: str) -> list[dict]:
    books = []
    for pod in HTMLParser(html).css("article.product_pod"):
        a = pod.css_first("h3 a")
        price = pod.css_first("p.price_color")
        stock = pod.css_first("p.instock.availability")
        rating = pod.css_first("p.star-rating")
        books.append({
            "title": a.attributes.get("title", "") if a else "",
            "price": (price.text() if price else "").replace("Â", "").strip(),
            "in_stock": bool(stock and "In stock" in stock.text()),
            "rating": next((c for c in (rating.attributes.get("class") or "").split() if c != "star-rating"), "") if rating else "",
        })
    return books


PARSERS = {"megatech": parse_megatech, "cifra": parse_cifra, "elmir": parse_elmir}


async def fetch(client: httpx.AsyncClient, source: str, url: str) -> SourceResult:
    res = SourceResult(source=source, url=url)
    started = time.perf_counter()
    try:
        r = await client.get(url)
        r.raise_for_status()
        if source == "books":
            res.books = parse_books(r.text)
            res.found = len(res.books)
        else:
            res.prices = PARSERS[source](r.text)
            res.found = len(res.prices)
        res.ok = res.found > 0
        if not res.ok:
            res.error = "товары не найдены: возможно, поменялась верстка"
    except Exception as exc:  # один упавший источник не должен ронять весь прогон
        res.error = f"{type(exc).__name__}: {exc}"[:200]
    res.ms = int((time.perf_counter() - started) * 1000)
    return res


async def scrape(shop_base_url: str) -> list[SourceResult]:
    urls = {shop: f"{shop_base_url.rstrip('/')}/{shop}" for shop in SHOPS}
    urls["books"] = BOOKS_URL
    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        return await asyncio.gather(*(fetch(client, s, u) for s, u in urls.items()))
