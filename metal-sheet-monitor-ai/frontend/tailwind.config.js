/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#003473',
          light: '#004c99', // A bit lighter
          dark: '#00224d',  // A bit darker
        },
        dark: {
          bg: '#1a1f2c',
          surface: '#242a38',
          text: '#e2e8f0'
        }
      },
    },
  },
  plugins: [],
}
