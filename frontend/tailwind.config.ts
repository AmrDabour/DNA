import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
          950: "#1e1b4b",
        },
        accent: {
          50: "#fdf4ff",
          100: "#fae8ff",
          200: "#f5d0fe",
          300: "#f0abfc",
          400: "#e879f9",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
          800: "#5b21b6",
          900: "#4c1d95",
        },
        tertiary: {
          500: "#06b6d4",
          600: "#0891b2",
          700: "#0e7490",
        },
        emerald: {
          500: "#10b981",
          600: "#059669",
        },
        rose: {
          500: "#f43f5e",
          600: "#e11d48",
        },
        amber: {
          500: "#f59e0b",
          600: "#d97706",
        },
        violet: {
          500: "#a78bfa",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
        full: "9999px",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(0, 0, 0, 0.05)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        glow: "0 0 40px rgba(99, 102, 241, 0.3)",
        card: "0 4px 24px rgba(0, 0, 0, 0.08)",
      },
      animation: {
        "fade-in": "fadeIn 0.6s ease forwards",
        "fade-in-up": "fadeInUp 0.6s ease forwards",
        "fade-in-left": "fadeInLeft 0.6s ease forwards",
        "fade-in-right": "fadeInRight 0.6s ease forwards",
        "scale-in": "scaleIn 0.5s ease forwards",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
        "spin-slow": "spin 3s linear infinite",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "pulse-gentle": "pulseGentle 2s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
        "float-rotate": "floatRotate 6s ease-in-out infinite",
        "float-particle": "floatParticle 15s infinite ease-in-out",
        "glow": "glow 2s ease-in-out infinite alternate",
        "dna-rotate": "dnaRotate 3s linear infinite",
        "btn-glow": "btnGlow 2s ease-in-out infinite",
        "upload-bounce": "uploadBounce 2s ease-in-out infinite",
        "loading-pulse": "loadingPulse 1.5s ease-in-out infinite",
        "spin-dna": "spinDNA 1.5s linear infinite",
        "hero-glow": "heroGlow 10s ease-in-out infinite",
        "bg-float": "bgFloat 20s ease-in-out infinite",
        "heart-pulse": "heartPulse 1s ease-in-out infinite",
        "strand-pulse": "strandPulse 2s ease-in-out infinite",
        "footer-glow-pulse": "footerGlowPulse 4s ease-in-out infinite",
        "footer-particle-float": "footerParticleFloat 5s infinite ease-in-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(30px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInLeft: {
          "0%": { opacity: "0", transform: "translateX(-30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        fadeInRight: {
          "0%": { opacity: "0", transform: "translateX(30px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.9)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideDown: {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        floatRotate: {
          "0%, 100%": { transform: "translateY(0) rotate(0deg)" },
          "50%": { transform: "translateY(-20px) rotate(10deg)" },
        },
        floatParticle: {
          "0%, 100%": { transform: "translateY(100vh) rotate(0deg)", opacity: "0" },
          "10%": { opacity: "0.5" },
          "90%": { opacity: "0.5" },
          "100%": { transform: "translateY(-100px) rotate(720deg)", opacity: "0" },
        },
        glow: {
          "0%": { boxShadow: "0 0 20px rgba(99, 102, 241, 0.3)" },
          "100%": { boxShadow: "0 0 40px rgba(99, 102, 241, 0.6)" },
        },
        dnaRotate: {
          "0%": { transform: "rotate(0deg) scale(1)" },
          "50%": { transform: "rotate(180deg) scale(1.1)" },
          "100%": { transform: "rotate(360deg) scale(1)" },
        },
        btnGlow: {
          "0%, 100%": { boxShadow: "0 4px 15px rgba(99, 102, 241, 0.4)" },
          "50%": { boxShadow: "0 4px 30px rgba(99, 102, 241, 0.6)" },
        },
        uploadBounce: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        loadingPulse: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
        spinDNA: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        heroGlow: {
          "0%, 100%": { transform: "translate(0, 0)" },
          "50%": { transform: "translate(-10%, 10%)" },
        },
        bgFloat: {
          "0%, 100%": { transform: "translate(0, 0) rotate(0deg)" },
          "25%": { transform: "translate(2%, 2%) rotate(1deg)" },
          "50%": { transform: "translate(0, 4%) rotate(0deg)" },
          "75%": { transform: "translate(-2%, 2%) rotate(-1deg)" },
        },
        pulseGentle: {
          "0%, 100%": { transform: "scale(1)", opacity: "0.3" },
          "50%": { transform: "scale(1.05)", opacity: "0.5" },
        },
        heartPulse: {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.2)" },
        },
        strandPulse: {
          "0%, 100%": { transform: "scale(1)", opacity: "0.4" },
          "50%": { transform: "scale(1.5)", opacity: "1" },
        },
        footerGlowPulse: {
          "0%, 100%": { opacity: "0.5", transform: "translateX(-50%) scale(1)" },
          "50%": { opacity: "0.8", transform: "translateX(-50%) scale(1.1)" },
        },
        footerParticleFloat: {
          "0%": { transform: "translateY(0) rotate(0deg)", opacity: "0" },
          "10%": { opacity: "0.4" },
          "90%": { opacity: "0.4" },
          "100%": { transform: "translateY(-300px) rotate(360deg)", opacity: "0" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "gradient-primary": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)",
        "gradient-hero": "linear-gradient(135deg, #1e1b4b 0%, #312e81 25%, #3730a3 50%, #4f46e5 100%)",
        "gradient-card": "linear-gradient(145deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)",
        "gradient-glow": "radial-gradient(ellipse at center, rgba(99,102,241,0.15) 0%, transparent 70%)",
        "dna-pattern": "url('/patterns/dna-helix.svg')",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

export default config;
