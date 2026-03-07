import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Axiom',
  description: 'Battle-tested Claude Code skills for xOS development',
  base: '/Axiom/',

  themeConfig: {
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/' },
      { text: 'Skills', link: '/skills/' }
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Guide',
          items: [
            { text: 'Getting Started', link: '/guide/' },
            { text: 'Installation', link: '/guide/installation' }
          ]
        }
      ],
      '/skills/': [
        {
          text: 'Skills',
          items: [
            { text: 'Overview', link: '/skills/' }
          ]
        },
        {
          text: 'UI & Design',
          items: [
            { text: 'Overview', link: '/skills/ui-design/' },
            { text: 'Liquid Glass', link: '/skills/ui-design/liquid-glass' },
            { text: 'SwiftUI Performance', link: '/skills/ui-design/swiftui-performance' },
            { text: 'UI Testing', link: '/skills/ui-design/ui-testing' }
          ]
        },
        {
          text: 'Debugging & Troubleshooting',
          items: [
            { text: 'Overview', link: '/skills/debugging/' },
            { text: 'Xcode Debugging', link: '/skills/debugging/xcode-debugging' },
            { text: 'Memory Debugging', link: '/skills/debugging/memory-debugging' },
            { text: 'Build Troubleshooting', link: '/skills/debugging/build-troubleshooting' }
          ]
        },
        {
          text: 'Concurrency & Async',
          items: [
            { text: 'Overview', link: '/skills/concurrency/' },
            { text: 'Swift Concurrency', link: '/skills/concurrency/swift-concurrency' }
          ]
        },
        {
          text: 'Persistence',
          items: [
            { text: 'Overview', link: '/skills/persistence/' },
            { text: 'Database Migration', link: '/skills/persistence/database-migration' },
            { text: 'SQLiteData', link: '/skills/persistence/sqlitedata' },
            { text: 'GRDB', link: '/skills/persistence/grdb' },
            { text: 'SwiftData', link: '/skills/persistence/swiftdata' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/CharlesWiltgen/Axiom' }
    ]
  }
})
