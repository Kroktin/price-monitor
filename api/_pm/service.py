"""Прогон парсера, история цен и данные для дашборда."""
from __future__ import annotations

from datetime import datetime, timedelta

from .catalog import HISTORY_DAYS, MSK, PRODUCTS, SHOPS, shop_price, today
from .parser import scrape

HISTORY_KEY = "pm:history"
RUNS_KEY = "pm:runs"
BOOKS_KEY = "pm:books"
LOCK_KEY = "pm:lock"
LOCK_SECONDS = 60


class Service:
    def __init__(self, store):
        self.store = store

    async def history(self) -> dict:
        hist = await self.store.get_json(HISTORY_KEY)
        if hist:
            return hist
        # Первый запуск демо: заполняем прошлые дни той же моделью цен, дальше точки добавляет парсер.
        hist = {}
        for i in range(HISTORY_DAYS - 1, 0, -1):
            day = today() - timedelta(days=i)
            hist[day.isoformat()] = {
                sku: {shop: shop_price(shop, sku, day) for shop in SHOPS if sku in SHOPS[shop]["items"]}
                for sku in PRODUCTS
            }
        await self.store.set_json(HISTORY_KEY, hist)
        await self.store.set_json("pm:backfill_until", (today() - timedelta(days=1)).isoformat())
        return hist

    async def run(self, shop_base_url: str, trigger: str) -> dict:
        if trigger == "button" and await self.store.incr(LOCK_KEY, ex=LOCK_SECONDS) > 1:
            runs = await self.store.get_json(RUNS_KEY) or []
            return {"locked": True, "run": runs[0] if runs else None}

        results = await scrape(shop_base_url)
        hist = await self.history()
        day = today().isoformat()
        snapshot = hist.get(day, {sku: {} for sku in PRODUCTS})
        for r in results:
            if r.source in SHOPS and r.ok:
                for sku, price in r.prices.items():
                    snapshot.setdefault(sku, {})[r.source] = price
            if r.source == "books" and r.ok:
                await self.store.set_json(BOOKS_KEY, {"at": datetime.now(MSK).isoformat(), "items": r.books})
        hist[day] = snapshot
        border = (today() - timedelta(days=HISTORY_DAYS + 5)).isoformat()
        hist = {d: v for d, v in hist.items() if d >= border}
        await self.store.set_json(HISTORY_KEY, hist)

        run = {
            "at": datetime.now(MSK).isoformat(),
            "trigger": trigger,
            "sources": [{"source": r.source, "url": r.url, "ok": r.ok, "ms": r.ms, "found": r.found, "error": r.error}
                        for r in results],
            "changes": len(self.changes(hist)),
        }
        runs = (await self.store.get_json(RUNS_KEY) or [])[:19]
        await self.store.set_json(RUNS_KEY, [run, *runs])
        return {"locked": False, "run": run}

    @staticmethod
    def changes(hist: dict) -> list[dict]:
        days = sorted(hist)
        if len(days) < 2:
            return []
        prev, last = hist[days[-2]], hist[days[-1]]
        out = []
        for sku, shops in last.items():
            for shop, new in shops.items():
                old = prev.get(sku, {}).get(shop)
                if old == new or (old is None and new is None):
                    continue
                kind = "out" if new is None else "back" if old is None else "down" if new < old else "up"
                pct = round((new - old) / old * 100, 1) if old and new else None
                out.append({"sku": sku, "shop": shop, "old": old, "new": new, "kind": kind, "pct": pct})
        return sorted(out, key=lambda c: abs(c["pct"] or 100), reverse=True)

    async def dashboard(self) -> dict:
        hist = await self.history()
        days = sorted(hist)[-HISTORY_DAYS:]
        last = hist[days[-1]]
        products = []
        for sku, (name, our) in PRODUCTS.items():
            comp = {shop: last.get(sku, {}).get(shop) for shop in SHOPS if sku in SHOPS[shop]["items"]}
            available = {s: p for s, p in comp.items() if p}
            min_shop = min(available, key=available.get) if available else None
            min_price = available.get(min_shop) if min_shop else None
            products.append({
                "sku": sku, "name": name, "our": our, "competitors": comp,
                "min": min_price, "min_shop": min_shop,
                "diff_pct": round((our - min_price) / min_price * 100, 1) if min_price else None,
                "history": {shop: [hist[d].get(sku, {}).get(shop) for d in days] for shop in comp},
            })
        changes = self.changes({d: hist[d] for d in days})
        cheaper = [p for p in products if p["diff_pct"] is not None and p["diff_pct"] > 0]
        return {
            "updated": days[-1],
            "days": days,
            "backfill_until": await self.store.get_json("pm:backfill_until"),
            "shops": {k: {"title": v["title"], "markup": v["markup"]} for k, v in SHOPS.items()},
            "products": products,
            "changes": changes,
            "runs": (await self.store.get_json(RUNS_KEY) or [])[:5],
            "books": await self.store.get_json(BOOKS_KEY),
            "kpi": {
                "products": len(products),
                "sources": len(SHOPS) + 1,
                "changes": len(changes),
                "we_are_pricier": len(cheaper),
            },
        }
