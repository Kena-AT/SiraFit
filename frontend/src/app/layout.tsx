import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SiraFit | Job Search Automation',
  description: 'High-density automation for job search',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-background-primary flex flex-col text-text-primary`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
