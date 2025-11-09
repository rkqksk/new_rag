import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'RAG Enterprise - AI Product Search',
  description: 'Intelligent product search powered by NexaAI & Qdrant',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
