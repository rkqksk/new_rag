import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Pure Black Theme (ABSOLUTE - NO COMPROMISE)
        background: "#000000",  // Pure black, always
        foreground: "#FFFFFF",  // Pure white text
        
        // Natural accents
        primary: {
          DEFAULT: "#FFFFFF",
          foreground: "#000000",
        },
        secondary: {
          DEFAULT: "#1A1A1A",
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "#0A0A0A",
          foreground: "#999999",
        },
        border: "#1A1A1A",
        input: "#1A1A1A",
        ring: "#FFFFFF",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}

export default config
