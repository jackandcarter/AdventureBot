import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        night: {
          900: "#0b0f1a",
          850: "#101526",
          800: "#131a2f",
          700: "#1a2440"
        },
        aurora: {
          cyan: "#4bd6ff",
          violet: "#9b7bff",
          magenta: "#f064ff",
          lime: "#89ff8b",
          amber: "#ffd166"
        }
      },
      boxShadow: {
        glow: "0 0 25px rgba(75, 214, 255, 0.25)",
        glass: "0 20px 60px rgba(5, 10, 24, 0.45)"
      },
      backdropBlur: {
        xs: "2px"
      },
      fontFamily: {
        display: ["Space Grotesk", "ui-sans-serif", "system-ui"],
        body: ["Inter", "ui-sans-serif", "system-ui"]
      }
    }
  },
  plugins: []
} satisfies Config;
