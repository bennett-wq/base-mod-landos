/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    borderRadius: {
      none: '0',
      DEFAULT: '0.25rem',
      lg: '0.5rem',
      xl: '0.75rem',
      full: '9999px',
    },
    extend: {
      colors: {
        'primary': '#7f5313',
        'primary-container': '#9b6b2a',
        'on-primary': '#ffffff',
        'on-primary-container': '#fffbff',
        'primary-fixed': '#ffddb8',
        'primary-fixed-dim': '#f7bb73',
        'surface': '#fbf9f6',
        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#f5f3f0',
        'surface-container': '#efeeeb',
        'surface-container-high': '#eae8e5',
        'surface-container-highest': '#e4e2df',
        'on-surface': '#1b1c1a',
        'on-surface-variant': '#504539',
        'outline': '#827567',
        'outline-variant': '#d4c4b4',
        'secondary': '#555f6d',
        'tertiary': '#006948',
        'tertiary-container': '#00855d',
        'error': '#ba1a1a',
        'error-container': '#ffdad6',
        'inverse-surface': '#30312f',
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
      },
      boxShadow: {
        ambient: '0 12px 32px rgba(27, 28, 26, 0.04)',
        'ambient-lg': '0 20px 48px rgba(27, 28, 26, 0.06)',
      },
    },
  },
  plugins: [],
}
