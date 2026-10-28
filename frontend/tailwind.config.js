/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        panel: '#0f172a',
        accent: '#38bdf8',
        good: '#22c55e',
        warn: '#f59e0b',
        danger: '#f87171',
      },
    },
  },
  plugins: [],
};
