import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  weight: ['300', '400', '500'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'ARIA - The AI you wear',
  description:
    'A wearable AI personal assistant that knows you, remembers your life, and takes real actions. Private, local-first, £30 in hardware.',
  openGraph: {
    title: 'ARIA - The AI you wear',
    description:
      'It knows you. It remembers everything. It takes real actions.',
    type: 'website',
    url: 'https://aria-wheat.vercel.app',
    siteName: 'ARIA',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ARIA - The AI you wear',
    description:
      'It knows you. It remembers everything. It takes real actions.',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-[#080808] text-[#f0f0f0] antialiased min-h-screen font-sans">
        {children}
      </body>
    </html>
  )
}
