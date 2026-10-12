'use client'

import { Fragment, useCallback, useEffect, useState } from 'react'
import Chart from '@/components/Chart'
import { api, BASE, Dashboard, PORTFOLIO_URL, Run, rub, SHOP_COLORS, shortDay } from '@/lib/api'

const SOURCE_TITLES: Record<string, string> = { megatech: 'МегаТех', cifra: 'Цифра+', elmir: 'ЭлектроМир', books: 'books.toscrape.com' }

function csv(d: Dashboard) {
  const shops = Object.keys(d.shops)
  const head = ['Товар', 'Наша цена', ...shops.map(s => d.shops[s].title), 'Минимум у конкурентов', 'Разница, %']
  const rows = d.products.map(p => [
    p.name, p.our, ...shops.map(s => (s in p.competitors ? p.competitors[s] ?? 'нет в наличии' : '—')), p.min ?? '', p.diff_pct ?? '',
  ])
  const text = [head, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(';')).join('\r\n')
  const url = URL.createObjectURL(new Blob(['﻿' + text], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: `prices-${d.updated}.csv` })
  a.click()
  URL.revokeObjectURL(url)
}

export default function Page() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')
  const [open, setOpen] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [log, setLog] = useState<string[]>([])

  const load = useCallback(async () => {
    try {
      setData(await api.dashboard())
      setError('')
    } catch {
      setError('Не удалось загрузить данные, попробуйте обновить страницу')
    }
  }, [])

  useEffect(() => { load() }, [load])

  const runParser = async () => {
    setRunning(true)
    setLog(['▶ Запуск парсера…'])
    try {
      const res = await api.scrape()
      const run: Run | null = res.run
      if (res.locked) {
        setLog(l => [...l, 'Парсер запускался меньше минуты назад, показываю последний прогон:'])
      }
      for (const s of run?.sources ?? []) {
        await new Promise(r => setTimeout(r, 350))
        setLog(l => [...l, s.ok
          ? `✓ ${SOURCE_TITLES[s.source]}: ${s.found} ${s.source === 'books' ? 'книг' : 'товаров'} за ${s.ms} мс`
          : `✕ ${SOURCE_TITLES[s.source]}: ${s.error || 'ошибка'}`])
      }
      await new Promise(r => setTimeout(r, 350))
      setLog(l => [...l, `Готово. Изменений цен за сутки: ${run?.changes ?? 0}`])
      await load()
    } catch {
      setLog(l => [...l, '✕ Ошибка запуска, попробуйте еще раз'])
    } finally {
      setRunning(false)
    }
  }

  if (!data) {
    return (
      <main className="grid min-h-screen place-items-center text-slate-400">
        {error || <span className="animate-pulse">Загружаю цены…</span>}
      </main>
    )
  }

  const shops = Object.keys(data.shops)
  const lastRun = data.runs[0]

  return (
    <main className="mx-auto max-w-[1240px] px-4 pb-10 pt-6 sm:px-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-mint-400">Демо · парсер цен</div>
          <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">Мониторинг цен конкурентов</h1>
          <p className="mt-1 text-sm text-slate-400">
            Магазин «ТехноДом» против трех конкурентов. Данные на {shortDay(data.updated)}
            {lastRun && <> · последний прогон {new Date(lastRun.at).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })} ({lastRun.trigger === 'cron' ? 'по расписанию' : 'вручную'})</>}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => csv(data)} className="rounded-xl border border-line bg-white/5 px-4 py-2.5 text-sm font-semibold text-slate-200 transition hover:bg-white/10">
            Скачать CSV
          </button>
          <button onClick={runParser} disabled={running} className="rounded-xl bg-mint-500 px-4 py-2.5 text-sm font-semibold text-base transition hover:bg-mint-400 disabled:opacity-60">
            {running ? 'Парсинг…' : '▶ Запустить парсер'}
          </button>
        </div>
      </header>

      {log.length > 0 && (
        <div className="mt-4 rounded-2xl border border-line bg-black/40 p-4 font-mono text-[13px] leading-relaxed text-slate-300">
          {log.map((line, i) => <div key={i} className="animate-fade">{line}</div>)}
        </div>
      )}

      <section className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          [data.kpi.products, 'товаров на контроле'],
          [data.kpi.sources, 'источника данных'],
          [data.kpi.changes, 'изменений цен за сутки'],
          [`${data.kpi.we_are_pricier} из ${data.kpi.products}`, 'позиций дороже минимума у конкурентов'],
        ].map(([v, l]) => (
          <div key={l as string} className="rounded-2xl border border-line bg-card px-4 py-4">
            <div className="text-2xl font-bold text-white">{v}</div>
            <div className="text-xs text-slate-400">{l}</div>
          </div>
        ))}
      </section>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_340px]">
        <section className="overflow-hidden rounded-2xl border border-line bg-card">
          <div className="flex items-center justify-between border-b border-line px-4 py-3">
            <h2 className="font-semibold text-white">Цены сегодня</h2>
            <span className="text-xs text-slate-500">нажмите на товар, чтобы увидеть график за 30 дней</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500">
                  <th className="px-4 py-2 font-medium">Товар</th>
                  <th className="px-3 py-2 font-medium">Наша цена</th>
                  {shops.map(s => (
                    <th key={s} className="px-3 py-2 font-medium">
                      <span className="mr-1.5 inline-block h-2 w-2 rounded-full" style={{ background: SHOP_COLORS[s] }} />{data.shops[s].title}
                    </th>
                  ))}
                  <th className="px-3 py-2 font-medium">Позиция</th>
                </tr>
              </thead>
              <tbody>
                {data.products.map(p => (
                  <Fragment key={p.sku}>
                    <tr onClick={() => setOpen(open === p.sku ? null : p.sku)} className={`cursor-pointer border-t border-line transition hover:bg-white/[0.03] ${open === p.sku ? 'bg-white/[0.04]' : ''}`}>
                      <td className="px-4 py-3 font-medium text-slate-100">{p.name}</td>
                      <td className="px-3 py-3 font-mono text-mint-300">{rub(p.our)}</td>
                      {shops.map(s => {
                        const v = p.competitors[s]
                        const isMin = s === p.min_shop
                        return (
                          <td key={s} className={`px-3 py-3 font-mono ${!(s in p.competitors) ? 'text-slate-600' : v == null ? 'text-slate-500' : isMin ? 'font-semibold text-white' : 'text-slate-300'}`}>
                            {!(s in p.competitors) ? '—' : v == null ? 'нет' : rub(v)}
                            {isMin && <span className="ml-1 text-[10px] text-mint-400">min</span>}
                          </td>
                        )
                      })}
                      <td className="px-3 py-3">
                        {p.diff_pct == null ? '—' : (
                          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${p.diff_pct > 0 ? 'bg-red-500/15 text-red-300' : 'bg-mint-500/15 text-mint-300'}`}>
                            {p.diff_pct > 0 ? `дороже на ${p.diff_pct}%` : p.diff_pct < 0 ? `дешевле на ${Math.abs(p.diff_pct)}%` : 'как у рынка'}
                          </span>
                        )}
                      </td>
                    </tr>
                    {open === p.sku && (
                      <tr className="border-t border-line bg-black/20">
                        <td colSpan={3 + shops.length} className="px-4 py-4">
                          <Chart days={data.days} series={p.history} our={p.our} titles={Object.fromEntries(shops.map(s => [s, data.shops[s].title]))} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="space-y-5">
          <section className="rounded-2xl border border-line bg-card">
            <h2 className="border-b border-line px-4 py-3 font-semibold text-white">Изменения за сутки</h2>
            <ul className="max-h-[420px] divide-y divide-line overflow-y-auto">
              {data.changes.length === 0 && <li className="px-4 py-6 text-center text-sm text-slate-500">Изменений нет</li>}
              {data.changes.slice(0, 25).map((c, i) => {
                const name = data.products.find(p => p.sku === c.sku)?.name
                return (
                  <li key={i} className="px-4 py-2.5 text-sm">
                    <div className="truncate text-slate-200">{name}</div>
                    <div className="mt-0.5 flex items-center justify-between text-xs">
                      <span className="text-slate-500">{data.shops[c.shop].title}</span>
                      {c.kind === 'out' && <span className="text-slate-400">закончился</span>}
                      {c.kind === 'back' && <span className="text-sky-300">снова в наличии · {rub(c.new)}</span>}
                      {(c.kind === 'up' || c.kind === 'down') && (
                        <span className={c.kind === 'down' ? 'text-mint-300' : 'text-red-300'}>
                          {rub(c.old)} → {rub(c.new)} ({Math.abs(c.pct!) < 0.1 ? (c.kind === 'up' ? '+' : '−') + '<0.1' : (c.pct! > 0 ? '+' : '') + c.pct}%)
                        </span>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          </section>

          <section className="rounded-2xl border border-line bg-card p-4">
            <h2 className="font-semibold text-white">Источники</h2>
            <p className="mt-1 text-xs text-slate-500">Тестовые магазины с разной версткой: парсер умеет каждую.</p>
            <ul className="mt-3 space-y-2 text-sm">
              {shops.map(s => (
                <li key={s} className="flex items-center justify-between gap-2">
                  <a href={`${BASE}/shops/${s}`} target="_blank" rel="noopener" className="flex items-center gap-2 text-slate-200 hover:text-white">
                    <i className="h-2 w-2 rounded-full" style={{ background: SHOP_COLORS[s] }} />{data.shops[s].title} ↗
                  </a>
                  <span className="text-xs text-slate-500">{data.shops[s].markup}</span>
                </li>
              ))}
              <li className="flex items-center justify-between gap-2">
                <a href="https://books.toscrape.com" target="_blank" rel="noopener" className="flex items-center gap-2 text-slate-200 hover:text-white">
                  <i className="h-2 w-2 rounded-full bg-slate-400" />books.toscrape.com ↗
                </a>
                <span className="text-xs text-slate-500">реальный сайт</span>
              </li>
            </ul>
          </section>
        </aside>
      </div>

      {data.books && (
        <section className="mt-5 rounded-2xl border border-line bg-card">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
            <h2 className="font-semibold text-white">Реальный внешний сайт: books.toscrape.com</h2>
            <span className="text-xs text-slate-500">первая страница каталога, {data.books.items.length} позиций</span>
          </div>
          <div className="grid gap-px bg-line sm:grid-cols-2 lg:grid-cols-4">
            {data.books.items.slice(0, 8).map(b => (
              <div key={b.title} className="bg-card px-4 py-3 text-sm">
                <div className="line-clamp-1 text-slate-200">{b.title}</div>
                <div className="mt-1 flex justify-between text-xs text-slate-500">
                  <span className="font-mono text-slate-300">{b.price}</span>
                  <span>{b.in_stock ? 'в наличии' : 'нет'} · {b.rating}★</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <footer className="mt-8 flex flex-wrap items-start justify-between gap-3 text-xs text-slate-500">
        <p className="max-w-2xl">
          Парсер работает по расписанию каждый день в 09:00 МСК и по кнопке. Магазины-конкуренты тестовые, чтобы не парсить
          чужие сайты в публичной демке; их цены меняются каждый день.
          {data.backfill_until && <> История до {shortDay(data.backfill_until)} заполнена при запуске демо той же моделью цен, дальше точки добавляет парсер.</>}
        </p>
        <a href={PORTFOLIO_URL} target="_blank" rel="noopener" className="text-slate-400 hover:text-white">Портфолио разработчика →</a>
      </footer>
    </main>
  )
}
