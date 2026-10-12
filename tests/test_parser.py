import asyncio
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

import _pm.service as service_mod  # noqa: E402
from _pm.catalog import PRODUCTS, SHOPS, shop_price, today  # noqa: E402
from _pm.parser import SourceResult, parse_books, parse_cifra, parse_elmir, parse_megatech  # noqa: E402
from _pm.service import Service  # noqa: E402
from _pm.shops import RENDER  # noqa: E402
from _pm.storage import MemoryStore  # noqa: E402

PARSE = {"megatech": parse_megatech, "cifra": parse_cifra, "elmir": parse_elmir}


def test_parsers_match_model_for_many_days():
    for offset in range(40):
        day = date(2026, 1, 1) + timedelta(days=offset)
        for shop, parse in PARSE.items():
            got = parse(RENDER[shop](day))
            assert set(got) == set(SHOPS[shop]["items"])
            for sku, price in got.items():
                assert price == shop_price(shop, sku, day), (shop, sku, day)


def test_model_has_changes_promos_and_out_of_stock():
    values = [shop_price("megatech", "iph15", date(2026, 1, 1) + timedelta(days=i)) for i in range(60)]
    assert len(set(values)) > 20
    allp = [shop_price(s, k, date(2026, 1, 1) + timedelta(days=i)) for i in range(60) for s in SHOPS for k in SHOPS[s]["items"]]
    assert any(p is None for p in allp)
    assert all(p is None or str(p).endswith("990") or p % 10 == 0 for p in allp)


def test_books_parser():
    html = """<article class="product_pod"><h3><a title="A Light in the Attic" href="#">A Light...</a></h3>
    <div class="product_price"><p class="price_color">Â£51.77</p><p class="instock availability">In stock</p></div>
    <p class="star-rating Three"></p></article>"""
    books = parse_books(html)
    assert books == [{"title": "A Light in the Attic", "price": "£51.77", "in_stock": True, "rating": "Three"}]


def test_service_run_and_dashboard(monkeypatch):
    async def fake_scrape(base):
        out = []
        for shop, parse in PARSE.items():
            prices = parse(RENDER[shop](today()))
            out.append(SourceResult(source=shop, url=f"{base}/{shop}", ok=True, found=len(prices), prices=prices))
        out.append(SourceResult(source="books", url="x", ok=False, error="offline"))
        return out

    monkeypatch.setattr(service_mod, "scrape", fake_scrape)

    async def go():
        s = Service(MemoryStore())
        d0 = await s.dashboard()
        assert len(d0["days"]) == 29 and d0["updated"] < today().isoformat()
        res = await s.run("http://x", trigger="button")
        assert not res["locked"] and res["run"]["sources"][3]["ok"] is False
        assert (await s.run("http://x", trigger="button"))["locked"]
        d = await s.dashboard()
        assert d["updated"] == today().isoformat() and len(d["days"]) == 30
        assert len(d["products"]) == len(PRODUCTS)
        p = d["products"][0]
        assert p["min"] == min(v for v in p["competitors"].values() if v)
        assert all(len(h) == 30 for h in p["history"].values())
        assert d["kpi"]["changes"] == len(d["changes"])
    asyncio.run(go())
