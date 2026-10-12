import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base: '#0f1419',
        card: '#161d24',
        line: 'rgba(255,255,255,0.08)',
        mint: { 300: '#7ee2b8', 400: '#3ccf91', 500: '#1fb57a' },
      },
      fontFamily: { sans: ['var(--font-sans)', 'system-ui', 'sans-serif'], mono: ['var(--font-mono)', 'monospace'] },
      keyframes: { fade: { '0%': { opacity: '0', transform: 'translateY(4px)' }, '100%': { opacity: '1', transform: 'none' } } },
      animation: { fade: 'fade .3s ease-out both' },
    },
  },
  plugins: [],
}
export default config
