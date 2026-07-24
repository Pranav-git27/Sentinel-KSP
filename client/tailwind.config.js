const { fontFamily } = require('tailwindcss/defaultTheme');

module.exports = {
  content: ['./src/**/*.{js,jsx}', './public/index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...fontFamily.sans],
        mono: ['JetBrains Mono', ...fontFamily.mono],
      },
      colors: {
        surface: {
          DEFAULT: '#0f172a',
          light: '#f8fafc',
        },
        card: {
          DEFAULT: '#1e293b',
          light: '#ffffff',
        },
        border: {
          DEFAULT: '#334155',
          light: '#e2e8f0',
        },
        accent: {
          DEFAULT: '#38bdf8',
          hover: '#7dd3fc',
          muted: '#0c4a6e',
        },
        cyber: {
          green: '#22c55e',
          amber: '#f59e0b',
          red: '#ef4444',
          purple: '#a855f7',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glass-light': '0 8px 32px 0 rgba(0, 0, 0, 0.08)',
      },
    },
  },
  plugins: [],
};
