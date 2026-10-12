'use client'

import { useMemo, useState } from 'react'
import { Price, rub, SHOP_COLORS, shortDay } from '@/lib/api'

const W = 640
const H = 220
const PAD = { l: 64, r: 14, t: 14, b: 26 }

export default function Chart({
  days, series, our, titles,
}: { days: string[]; series: Record<string, Price[]>; our: number; titles: Record<string, string> }) {
  const [hover, setHover] = useState<number | null>(null)

  const { min, max } = useMemo(() => {
    const vals = Object.values(series).flat().filter((v): v is number => v != null).concat(our)
    const lo = Math.min(...vals), hi = Math.max(...vals)
    const pad = (hi - lo) * 0.12 || hi * 0.05
    return { min: lo - pad, max: hi + pad }
  }, [series, our])

  const x = (i: number) => PAD.l + (i / Math.max(1, days.length - 1)) * (W - PAD.l - PAD.r)
  const y = (v: number) => PAD.t + (1 - (v - min) / (max - min)) * (H - PAD.t - PAD.b)

  const path = (vals: Price[]) => {
    let d = ''
    let pen = false
    vals.forEach((v, i) => {
      if (v == null) { pen = false; return }
      d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)} `
      pen = true
    })
    return d
  }

  const ticks = [0, 0.5, 1].map(t => min + (max - min) * t)

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        onMouseLeave={() => setHover(null)}
        onMouseMove={e => {
          const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect()
          const px = ((e.clientX - rect.left) / rect.width) * W
          const i = Math.round(((px - PAD.l) / (W - PAD.l - PAD.r)) * (days.length - 1))
          setHover(Math.min(days.length - 1, Math.max(0, i)))
        }}
      >
        {ticks.map(t => (
          <g key={t}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke="rgba(255,255,255,.06)" />
            <text x={PAD.l - 8} y={y(t) + 4} textAnchor="end" className="fill-slate-500 text-[10px]">{Math.round(t).toLocaleString('ru-RU')}</text>
          </g>
        ))}
        {[0, Math.floor(days.length / 2), days.length - 1].map(i => (
          <text key={i} x={x(i)} y={H - 6} textAnchor="middle" className="fill-slate-500 text-[10px]">{shortDay(days[i])}</text>
        ))}
        <line x1={PAD.l} x2={W - PAD.r} y1={y(our)} y2={y(our)} stroke={SHOP_COLORS.our} strokeDasharray="5 4" strokeWidth={1.5} />
        {Object.entries(series).map(([shop, vals]) => (
          <path key={shop} d={path(vals)} fill="none" stroke={SHOP_COLORS[shop]} strokeWidth={2} strokeLinejoin="round" />
        ))}
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={PAD.t} y2={H - PAD.b} stroke="rgba(255,255,255,.25)" />}
        {hover != null && Object.entries(series).map(([shop, vals]) =>
          vals[hover] != null ? <circle key={shop} cx={x(hover)} cy={y(vals[hover]!)} r={3.5} fill={SHOP_COLORS[shop]} /> : null)}
      </svg>
      {hover != null && (
        <div className="pointer-events-none absolute right-2 top-2 rounded-xl border border-line bg-base/95 px-3 py-2 text-xs shadow-lg">
          <div className="mb-1 font-semibold text-white">{shortDay(days[hover])}</div>
          {Object.entries(series).map(([shop, vals]) => (
            <div key={shop} className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-1.5 text-slate-400"><i className="h-2 w-2 rounded-full" style={{ background: SHOP_COLORS[shop] }} />{titles[shop]}</span>
              <span className="font-mono text-slate-200">{vals[hover] == null ? 'нет' : rub(vals[hover])}</span>
            </div>
          ))}
        </div>
      )}
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
        <span className="flex items-center gap-1.5"><i className="h-0.5 w-4 border-t-2 border-dashed" style={{ borderColor: SHOP_COLORS.our }} />Наша цена</span>
        {Object.keys(series).map(shop => (
          <span key={shop} className="flex items-center gap-1.5"><i className="h-2 w-2 rounded-full" style={{ background: SHOP_COLORS[shop] }} />{titles[shop]}</span>
        ))}
      </div>
    </div>
  )
}
