import type { Metadata, Viewport } from 'next'
import { JetBrains_Mono, Manrope } from 'next/font/google'
import './globals.css'

const sans = Manrope({ subsets: ['latin', 'cyrillic'], variable: '--font-sans' })
const mono = JetBrains_Mono({ subsets: ['latin', 'cyrillic'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'Мониторинг цен конкурентов · демо парсера',
  description: 'Демо парсера цен: три магазина с разной версткой, реальный внешний сайт, история цен за 30 дней и выгрузка в CSV.',
  icons: { icon: '/favicon.svg' },
}

export const viewport: Viewport = { themeColor: '#0f1419' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${sans.variable} ${mono.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
