module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx,vue}'],
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
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
