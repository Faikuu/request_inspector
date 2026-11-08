const animate = require('tailwindcss-animate')

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Schibsted Grotesk Variable"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Airmail palette (semantic). Use these names in components.
        paper: 'rgb(var(--paper) / <alpha-value>)', // page background
        sheet: 'rgb(var(--sheet) / <alpha-value>)', // raised surfaces (panels, inputs)
        ink: 'rgb(var(--ink) / <alpha-value>)', // primary text
        'ink-soft': 'rgb(var(--ink-soft) / <alpha-value>)', // secondary text
        rule: 'rgb(var(--rule) / <alpha-value>)', // borders / dividers
        airmail: {
          red: 'rgb(var(--airmail-red) / <alpha-value>)',
          blue: 'rgb(var(--airmail-blue) / <alpha-value>)',
        },
        live: 'rgb(var(--live) / <alpha-value>)',
        code: 'rgb(var(--code-bg) / <alpha-value>)', // code block background
        'code-ink': 'rgb(var(--code-ink) / <alpha-value>)',
        method: {
          get: 'rgb(var(--method-get) / <alpha-value>)',
          post: 'rgb(var(--method-post) / <alpha-value>)',
          put: 'rgb(var(--method-put) / <alpha-value>)',
          patch: 'rgb(var(--method-patch) / <alpha-value>)',
          delete: 'rgb(var(--method-delete) / <alpha-value>)',
          other: 'rgb(var(--method-other) / <alpha-value>)',
        },
        // shadcn-compatible aliases used by components/ui/*
        border: 'rgb(var(--rule) / <alpha-value>)',
        input: 'rgb(var(--rule) / <alpha-value>)',
        ring: 'rgb(var(--airmail-blue) / <alpha-value>)',
        background: 'rgb(var(--paper) / <alpha-value>)',
        foreground: 'rgb(var(--ink) / <alpha-value>)',
        primary: { DEFAULT: 'rgb(var(--ink) / <alpha-value>)', foreground: 'rgb(var(--paper) / <alpha-value>)' },
        secondary: { DEFAULT: 'rgb(var(--sheet) / <alpha-value>)', foreground: 'rgb(var(--ink) / <alpha-value>)' },
        destructive: { DEFAULT: 'rgb(var(--airmail-red) / <alpha-value>)', foreground: '#ffffff' },
        muted: { DEFAULT: 'rgb(var(--sheet) / <alpha-value>)', foreground: 'rgb(var(--ink-soft) / <alpha-value>)' },
        accent: { DEFAULT: 'rgb(var(--sheet) / <alpha-value>)', foreground: 'rgb(var(--ink) / <alpha-value>)' },
        popover: { DEFAULT: 'rgb(var(--sheet) / <alpha-value>)', foreground: 'rgb(var(--ink) / <alpha-value>)' },
        card: { DEFAULT: 'rgb(var(--sheet) / <alpha-value>)', foreground: 'rgb(var(--ink) / <alpha-value>)' },
      },
      borderRadius: {
        lg: '10px',
        md: '6px',
        sm: '4px',
      },
      backgroundImage: {
        // The one bold element: an airmail envelope chevron band.
        airmail:
          'repeating-linear-gradient(135deg, rgb(var(--airmail-red)) 0 14px, transparent 14px 22px, rgb(var(--airmail-blue)) 22px 36px, transparent 36px 44px)',
      },
    },
  },
  plugins: [animate],
}
