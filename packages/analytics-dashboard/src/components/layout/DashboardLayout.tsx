import { type ReactNode } from 'react'
import Header from './Header'
import type { ConnectionStatus } from '../../types'

interface DashboardLayoutProps {
  theme: 'light' | 'dark'
  onThemeToggle: () => void
  connectionStatus: ConnectionStatus
  children?: ReactNode
}

export default function DashboardLayout({
  theme,
  onThemeToggle,
  connectionStatus,
  children,
}: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-dark-50 dark:bg-dark-950">
      <Header
        theme={theme}
        onThemeToggle={onThemeToggle}
        connectionStatus={connectionStatus}
      />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {children || (
          <div className="flex min-h-[calc(100vh-12rem)] items-center justify-center">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30">
                <svg
                  className="h-8 w-8 text-primary-600 dark:text-primary-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <h2 className="mb-2 text-2xl font-semibold text-dark-900 dark:text-dark-50">
                Welcome to Analytics Dashboard
              </h2>
              <p className="mb-6 text-dark-600 dark:text-dark-400">
                Real-time analytics for your Claude Code plugins
              </p>
              <div className="space-y-2 text-sm text-dark-500 dark:text-dark-500">
                {connectionStatus === 'disconnected' && (
                  <p className="flex items-center justify-center gap-2 text-yellow-600 dark:text-yellow-400">
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Waiting for WebSocket connection...
                  </p>
                )}
                {connectionStatus === 'connecting' && (
                  <p className="flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400">
                    <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Connecting to analytics daemon...
                  </p>
                )}
                {connectionStatus === 'connected' && (
                  <p className="flex items-center justify-center gap-2 text-green-600 dark:text-green-400">
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    Connected and ready
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-200 bg-white dark:border-dark-800 dark:bg-dark-900">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between text-sm text-dark-500 dark:text-dark-400">
            <p>Analytics Dashboard v0.1.0</p>
            <p>Built with React + TypeScript + Vite</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
