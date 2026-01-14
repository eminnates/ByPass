import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}", // components klasörünü kapsar
        "./app/**/*.{js,ts,jsx,tsx,mdx}",        // app klasörünü kapsar
    ],
    theme: {
        extend: {},
    },
    plugins: [],
};
export default config;