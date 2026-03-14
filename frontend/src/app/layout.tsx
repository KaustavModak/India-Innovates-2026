import type { Metadata } from 'next'
import './globals.css'
import { Navbar } from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'Election Integrity Audit | Cryptographic Verification Dashboard',
  description: 'Post-Count Cryptographic Audit Layer — verify that official election result files have never been altered using SHA-256 hashing and blockchain technology.',
  keywords: 'election, integrity, audit, blockchain, verification, SHA-256, cryptographic',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen">
        <Navbar />
        <main className="pt-20">
          {children}
        </main>

        {/* Footer */}
        <footer className="mt-20 border-t border-gray-800/50">
          <div className="max-w-7xl mx-auto px-6 py-10">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                  <span className="text-white text-sm font-bold">EA</span>
                </div>
                <span className="text-gray-400 text-sm">
                  Election Audit — Post-Count Cryptographic Verification
                </span>
              </div>
              <p className="text-gray-500 text-sm">
                Powered by SHA-256 & Hyperledger Fabric • Open Source
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
