"""
Каталог демо: наш магазин и три тестовых магазина-конкурента.

Цены конкурентов детерминированно зависят от даты: каждый день немного меняются, иногда бывают акции
и товар пропадает из наличия. Так у парсера всегда есть реальные изменения, которые можно отследить.
"""
from __future__ import annotations

import hashlib
import math
from datetime import date, datetime, timedelta, timezone

MSK = timezone(timedelta(hours=3))

# sku: (наше название, наша цена)
PRODUCTS: dict[str, tuple[str, int]] = {
    "iph15": ("Apple iPhone 15 128 ГБ", 74990),
    "s24": ("Samsung Galaxy S24 256 ГБ", 79990),
    "app2": ("Apple AirPods Pro 2", 22990),
    "ps5": ("Sony PlayStation 5 Slim", 54990),
    "dyv15": ("Dyson V15 Detect Absolute", 64990),
    "x20": ("Xiaomi Robot Vacuum X20+", 39990),
    "ysm": ("Яндекс Станция Макс", 29990),
    "mba": ("Apple MacBook Air 13 M3 8/256", 119990),
    "aw9": ("Apple Watch Series 9 45 мм", 39990),
    "pad6": ("Xiaomi Pad 6 8/256 ГБ", 31990),
}

# Конкуренты: свое название товара и свой артикул, как в жизни. Матчинг идет по таблице соответствий.
SHOPS: dict[str, dict] = {
    "megatech": {
        "title": "МегаТех",
        "markup": "карточки товаров (CSS-селекторы)",
        "bias": 0.985,
        "items": {
            "iph15": ("Смартфон Apple iPhone 15 128GB черный", "MT-10231"),
            "s24": ("Смартфон Samsung Galaxy S24 8/256GB", "MT-10877"),
            "app2": ("Наушники Apple AirPods Pro (2nd gen) USB-C", "MT-20114"),
            "ps5": ("Игровая консоль PlayStation 5 Slim Disc", "MT-30551"),
            "dyv15": ("Пылесос Dyson V15 Detect Absolute", "MT-41002"),
            "x20": ("Робот-пылесос Xiaomi X20+", "MT-41290"),
            "mba": ("Ноутбук Apple MacBook Air 13 (M3, 8/256)", "MT-50014"),
            "aw9": ("Смарт-часы Apple Watch S9 45mm", "MT-60020"),
        },
    },
    "cifra": {
        "title": "Цифра+",
        "markup": "таблица прайса",
        "bias": 1.01,
        "items": {
            "iph15": ("iPhone 15 128 Гб", "C-iph15-128"),
            "s24": ("Galaxy S24 256 Гб", "C-s24-256"),
            "app2": ("AirPods Pro 2 USB-C", "C-app2"),
            "ps5": ("PS5 Slim с дисководом", "C-ps5s"),
            "ysm": ("Станция Макс с Алисой", "C-ysm"),
            "mba": ("MacBook Air 13 M3 8GB/256GB", "C-mba13m3"),
            "pad6": ("Планшет Xiaomi Pad 6 8+256", "C-pad6"),
        },
    },
    "elmir": {
        "title": "ЭлектроМир",
        "markup": "JSON-LD (schema.org)",
        "bias": 0.995,
        "items": {
            "iph15": ("Apple iPhone 15, 128 ГБ", "EM-778001"),
            "s24": ("Samsung Galaxy S24, 256 ГБ", "EM-778540"),
            "dyv15": ("Беспроводной пылесос Dyson V15 Detect Absolute", "EM-901220"),
            "x20": ("Xiaomi Robot Vacuum X20+ (белый)", "EM-901377"),
            "ysm": ("Умная колонка Яндекс Станция Макс (Zigbee)", "EM-660101"),
            "aw9": ("Apple Watch Series 9, 45 мм, алюминий", "EM-610045"),
            "pad6": ("Xiaomi Pad 6, 8/256 ГБ", "EM-640256"),
        },
    },
}

HISTORY_DAYS = 30


def today() -> date:
    return datetime.now(MSK).date()


def _rand(*parts) -> float:
    """Детерминированное «случайное» число 0..1."""
    h = hashlib.sha256(":".join(map(str, parts)).encode()).digest()
    return int.from_bytes(h[:4], "big") / 0xFFFFFFFF


def shop_price(shop: str, sku: str, day: date) -> int | None:
    """Цена товара у конкурента на дату. None — нет в наличии."""
    base = PRODUCTS[sku][1] * SHOPS[shop]["bias"] * (0.97 + 0.06 * _rand("base", shop, sku))
    n = day.toordinal()
    phase = _rand("phase", shop, sku) * 50
    wave = 0.035 * math.sin((n + phase) / (4 + 3 * _rand("speed", shop, sku)))
    step = 0.012 * (_rand("step", shop, sku, n // 3) - 0.5)
    price = base * (1 + wave + step)
    if _rand("promo", shop, sku, n // 2) < 0.1:
        price *= 0.88 - 0.06 * _rand("depth", shop, sku, n // 2)
    if _rand("stock", shop, sku, n) < 0.05:
        return None
    return int(round(price / 10) * 10 - 10)  # «...990»


def fmt_rub(value: int) -> str:
    return f"{value:,}".replace(",", " ")
