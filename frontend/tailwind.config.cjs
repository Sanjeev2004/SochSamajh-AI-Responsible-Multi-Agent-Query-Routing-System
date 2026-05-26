/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                display: ['Outfit', 'sans-serif'],
            },
            colors: {
                deep: '#0A0A0A',
                surface: '#111111',
                'surface-hover': '#1A1A1A',
                border: '#262626',
            },
            boxShadow: {
                'subtle': '0 4px 24px -4px rgba(0, 0, 0, 0.2)',
            }
        }
    },
    plugins: []
};
