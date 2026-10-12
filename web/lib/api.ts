export type Price = number | null
export type Product = {
  sku: string
  name: string
  our: number
  competitors: Record<string, Price>
  min: Price
  min_shop: string | null
  diff_pct: number | null
  history: Record<string, Price[]>
}
export type Change = { sku: string; shop: string; old: Price; new: Price; kind: 'up' | 'down' | 'out' | 'back'; pct: number | null }
export type SourceRun = { source: string; url: string; ok: boolean; ms: number; found: number; error: string }
export type Run = { at: string; trigger: 'button' | 'cron'; sources: SourceRun[]; changes: number }
export type Book = { title: string; price: string; in_stock: boolean; rating: string }
export type Dashboard = {
  updated: string
  days: string[]
  backfill_until: string | null
  shops: Record<string, { title: string; markup: string }>
  products: Product[]
  changes: Change[]
  runs: Run[]
  books: { at: string; items: Book[] } | null
  kpi: { products: number; sources: number; changes: number; we_are_pricier: number }
}

// Локально API на uvicorn, на проде тот же домен через прокси хостинга.
export const BASE = process.env.NEXT_PUBLIC_API_BASE ?? '/api/py'

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, { ...init, cache: 'no-store' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const api = {
  dashboard: () => call<Dashboard>('/dashboard'),
  scrape: () => call<{ locked: boolean; run: Run | null }>('/scrape', { method: 'POST' }),
}

export const rub = (v: Price) => (v == null ? '—' : v.toLocaleString('ru-RU') + ' ₽')
export const shortDay = (iso: string) => new Date(iso + 'T00:00:00').toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' })
export const SHOP_COLORS: Record<string, string> = { megatech: '#f87171', cifra: '#60a5fa', elmir: '#fbbf24', our: '#3ccf91' }
export const PORTFOLIO_URL = 'https://anatoly-dev.netlify.app'
