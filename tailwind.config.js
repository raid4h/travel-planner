/*
 * =====================================================================
 * File: tailwind.config.js
 * Purpose: Tailwind CSS settings for the whole project.
 * Contains:
 *   - content: which files Tailwind scans for class names
 *   - theme.extend.fontFamily: Inter as the default font
 *   - theme.extend.colors.brand: the main (blue) colour of the app
 *   - theme.extend.boxShadow.card: the soft shadow used on cards
 * =====================================================================
 */

const colors = require("tailwindcss/colors");
const defaultTheme = require("tailwindcss/defaultTheme");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
    "./*/forms.py",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans],
      },
      colors: {
        brand: colors.blue,
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(16 24 40 / 0.05)",
      },
    },
  },
  plugins: [],
};