import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink:      "#0f0f0f",
        paper:    "#ffffff",
        tint:     "#f5f5f3",
        hairline: "#e5e5e5",
        navy: {
          950: "#060d16",
          900: "#0c1f33",
          800: "#142d47",
          700: "#1e3a5f",
          600: "#2d5a8e",
        },
        brand: {
          50:  "#f0f9ff",
          100: "#e0f2fe",
          400: "#38bdf8",
          500: "#0284c7",
          600: "#0369a1",  // primary button / interactive
          700: "#075985",  // sidebar background
          800: "#0c4a6e",  // sidebar gradient end
        },
        steel: {
          600: "#4a5e70",
          400: "#7a96ad",
          200: "#d0dce8",
        },
        risk: {
          high:            "#dc2626",
          medium:          "#d97706",
          low:             "#16a34a",
          "high-bg":       "#fee2e2",
          "high-border":   "#fca5a5",
          "medium-bg":     "#fef3c7",
          "medium-border": "#fcd34d",
          "low-bg":        "#dcfce7",
          "low-border":    "#86efac",
        },
      },
      fontFamily: {
        sans:    ["DM Sans", "system-ui", "sans-serif"],
        display: ["Josefin Sans", "sans-serif"],
        mono:    ["IBM Plex Mono", "Menlo", "monospace"],
        hero:    ["Archivo", "system-ui", "sans-serif"],
        serifit: ["Instrument Serif", "Georgia", "serif"],
      },
      boxShadow: {
        focus:        "0 0 0 3px rgba(2, 132, 199, 0.25)",
        "focus-danger": "0 0 0 3px rgba(220, 38, 38, 0.25)",
      },
      letterSpacing: {
        btn:    "0.06em",   // button text (UPPERCASE tracked)
        allcaps: "0.08em",  // ALL CAPS section labels
        logo:   "0.15em",   // logo wordmark
      },
    },
  },
  plugins: [],
} satisfies Config;
