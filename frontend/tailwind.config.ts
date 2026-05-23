import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        paper:    'var(--paper)',
        'paper-2':'var(--paper-2)',
        surface:  'var(--surface)',
        'surface-sunk': 'var(--surface-sunk)',
        vellum:   'var(--vellum)',
        ink:      'var(--ink)',
        'ink-2':  'var(--ink-2)',
        graphite: 'var(--graphite)',
        slate:    'var(--slate)',
        whisper:  'var(--whisper)',
        rule:     'var(--rule)',
        'rule-strong': 'var(--rule-strong)',
        'rule-soft':   'var(--rule-soft)',
        moss:     'var(--moss)',
        'moss-tint': 'var(--moss-tint)',
        brass:    'var(--brass)',
        'brass-tint': 'var(--brass-tint)',
        rust:     'var(--rust)',
        'rust-tint': 'var(--rust-tint)',
        azure:    'var(--azure)',
        'azure-tint': 'var(--azure-tint)',
        highlight: 'var(--highlight)',
        'highlight-rule': 'var(--highlight-rule)',
      },
      fontFamily: {
        serif: ['Newsreader', 'Source Serif 4', 'Georgia', 'serif'],
        sans:  ['IBM Plex Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono:  ['IBM Plex Mono', 'ui-monospace', 'JetBrains Mono', 'monospace'],
      },
      fontSize: {
        '2xs': ['10.5px', { lineHeight: '1.4' }],
        xs:    ['11px',   { lineHeight: '1.4' }],
        sm:    ['12px',   { lineHeight: '1.5' }],
        'sm+': ['12.5px', { lineHeight: '1.5' }],
        base:  ['13.5px', { lineHeight: '1.5' }],
        'base+':['14px',  { lineHeight: '1.55' }],
        md:    ['15px',   { lineHeight: '1.5' }],
        lg:    ['16px',   { lineHeight: '1.55' }],
        xl:    ['18px',   { lineHeight: '1.45' }],
        '2xl': ['22px',   { lineHeight: '1.3' }],
        '3xl': ['28px',   { lineHeight: '1.15' }],
        '4xl': ['38px',   { lineHeight: '1.05' }],
      },
      spacing: {
        'rail':   '232px',
        'topbar': '48px',
      },
      gridTemplateColumns: {
        'shell':  '232px 1fr',
      },
      keyframes: {
        pulse: {
          '0%, 100%': { opacity: '0.4' },
          '50%':      { opacity: '1' },
        },
        thinkfade: {
          '0%, 100%': { opacity: '0.4' },
          '50%':      { opacity: '1' },
        },
      },
      animation: {
        'pulse-slow': 'pulse 1.6s ease-in-out infinite',
        thinkfade:    'thinkfade 1.5s ease-in-out infinite',
      },
      maxWidth: {
        prose: '64ch',
        'prose-wide': '70ch',
      },
    },
  },
  plugins: [],
}

export default config
