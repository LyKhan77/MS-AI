/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#003473',
        secondary: '#005bb5',
        dark: '#0f172a',
      }
    },
  },
  plugins: [],
}
