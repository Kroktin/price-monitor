"""HTML тестовых магазинов. У каждого своя разметка, как у реальных сайтов."""
from __future__ import annotations

import html
import json
from datetime import date

from .catalog import SHOPS, fmt_rub, shop_price

STYLE = """
<style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f5f5f7;color:#1d1d1f}
  header{padding:18px 28px;color:#fff}
  main{max-width:1100px;margin:0 auto;padding:24px}
  .note{background:#fff8e1;border:1px solid #ffe08a;padding:10px 14px;border-radius:10px;font-size:13px;margin-bottom:18px}
</style>
"""


def _note(day: date) -> str:
    return (f'<div class="note">Тестовый магазин для демо парсера цен. Цены меняются каждый день, '
            f'сегодня {day.strftime("%d.%m.%Y")}. Это не настоящий магазин.</div>')


def render_megatech(day: date) -> str:
    cards = []
    for sku, (name, art) in SHOPS["megatech"]["items"].items():
        price = shop_price("megatech", sku, day)
        price_html = (f'<span class="price" data-price="{price}">{fmt_rub(price)} ₽</span>'
                      if price else '<span class="price price--na">Нет в наличии</span>')
        cards.append(f"""
      <div class="product-card" data-article="{art}">
        <div class="product-card__img"></div>
        <h3 class="product-card__title"><a href="#{art}">{html.escape(name)}</a></h3>
        <div class="product-card__meta">Арт. {art}</div>
        {price_html}
        <button>В корзину</button>
      </div>""")
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>МегаТех: каталог</title>{STYLE}
<style>
  header{{background:#e30613}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}}
  .product-card{{background:#fff;border-radius:14px;padding:16px}} .product-card__img{{height:120px;background:#eee;border-radius:10px}}
  .product-card__title{{font-size:15px}} .product-card__title a{{color:inherit;text-decoration:none}}
  .product-card__meta{{font-size:12px;color:#888}} .price{{display:block;font-size:22px;font-weight:700;margin:10px 0}}
  .price--na{{font-size:14px;color:#999}} button{{background:#e30613;color:#fff;border:0;border-radius:8px;padding:8px 14px}}
</style></head>
<body><header><b>МегаТех</b> · электроника</header><main>{_note(day)}<div class="grid">{''.join(cards)}</div></main></body></html>"""


def render_cifra(day: date) -> str:
    rows = []
    for sku, (name, art) in SHOPS["cifra"]["items"].items():
        price = shop_price("cifra", sku, day)
        cost = f'<td class="cost" content="{price}">{fmt_rub(price)} руб.</td>' if price else '<td class="cost">—</td>'
        stock = "В наличии" if price else "Под заказ"
        rows.append(f'<tr data-code="{art}"><td class="code">{art}</td><td class="name">{html.escape(name)}</td>{cost}'
                    f'<td class="stock">{stock}</td></tr>')
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Цифра+ · прайс-лист</title>{STYLE}
<style>
  header{{background:#0057b8}} table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden}}
  th,td{{padding:10px 14px;border-bottom:1px solid #eee;text-align:left;font-size:14px}} th{{background:#f0f4fa}}
</style></head>
<body><header><b>Цифра+</b> · оптовый прайс</header><main>{_note(day)}
<table id="price-list"><thead><tr><th>Код</th><th>Наименование</th><th>Цена</th><th>Наличие</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></main></body></html>"""


def render_elmir(day: date) -> str:
    items, ld = [], []
    for sku, (name, art) in SHOPS["elmir"]["items"].items():
        price = shop_price("elmir", sku, day)
        ld.append({
            "@type": "Product", "name": name, "sku": art,
            "offers": {
                "@type": "Offer", "priceCurrency": "RUB", "price": price or 0,
                "availability": "https://schema.org/" + ("InStock" if price else "OutOfStock"),
            },
        })
        # Видимая цена рисуется скриптом, поэтому в HTML ее нет: парсер берет данные из JSON-LD.
        items.append(f'<li class="tile"><div class="tile__name">{html.escape(name)}</div>'
                     f'<div class="tile__price" data-sku="{art}">…</div></li>')
    data = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": ld}
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>ЭлектроМир</title>{STYLE}
<style>header{{background:#111}} ul{{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}}
.tile{{background:#fff;border-radius:14px;padding:16px}} .tile__price{{font-size:20px;font-weight:700;margin-top:8px}}</style>
<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script></head>
<body><header><b>ЭлектроМир</b></header><main>{_note(day)}<ul>{''.join(items)}</ul></main>
<script>
  const d = JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent);
  for (const p of d.itemListElement) {{
    const el = document.querySelector('[data-sku="' + p.sku + '"]');
    el.textContent = p.offers.price ? p.offers.price.toLocaleString('ru-RU') + ' ₽' : 'Нет в наличии';
  }}
</script></body></html>"""


RENDER = {"megatech": render_megatech, "cifra": render_cifra, "elmir": render_elmir}
