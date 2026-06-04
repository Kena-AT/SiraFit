import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#3525cd",
          light: "#d0e1fb",
        },
        background: {
          primary: "#fcf8ff",
          secondary: "#ffffff",
          muted: "#f0ecf9",
        },
        border: {
          DEFAULT: "#c7c4d8",
          light: "#e4e1ee",
        },
        text: {
          primary: "#1b1b24",
          secondary: "#464555",
          muted: "#777587"
        }
      },
    },
  },
  plugins: [],
};
export default config;
