import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'OCH-Subagent — Document Intelligence',
  description: 'Multi-Agent OCR and Document Intelligence Platform with interactive AI chat assistant.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id" className={inter.variable}>
      <body className="antialiased font-sans bg-white">{children}</body>
    </html>
  )
}
