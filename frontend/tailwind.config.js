import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: false, // Light only as per requirements
  content: ['./src/**/*.{js,jsx,ts,tsx}', './index.html'],
  theme: {
    extend: {
      colors: {
        forest: '#173F35',
        'primary-light': '#E4F1EC',
        amber: '#E9A23B',
        'recovery-green': '#2F8F6B',
        'recovery-light': '#E7F5EF',
        'risk-coral': '#D96C55',
        'risk-light': '#FBEAE6',
        'blocked-plum': '#76566E',
        background: '#F7F5F0',
        surface: '#FFFFFF',
        'text-primary': '#20302C',
        'text-secondary': '#68746F',
        border: '#DDE3DF',
      },
      transitionDuration: {
        DEFAULT: '150', // default 150ms
        fast: '150',
        med: '200',
        slow: '220',
      },
    },
  },
  plugins: [],
}

export default config
