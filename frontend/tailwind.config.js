/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        oil: {
          navy: '#0b192c',
          dark: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          gold: '#eab308',
          goldlight: '#fde047',
          amber: '#f59e0b',
          orange: '#f97316',
          slate: '#64748b',
          light: '#f8fafc',
          steel: '#475569',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
