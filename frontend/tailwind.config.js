/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './viewer/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'cad-dark': '#0a0e17',
        'cad-panel': '#111827',
        'cad-border': '#1e293b',
        'cad-accent': '#00d4ff',
        'cad-accent2': '#ff6b35',
        'cad-text': '#e2e8f0',
        'cad-muted': '#64748b',
      },
    },
  },
  plugins: [],
};
