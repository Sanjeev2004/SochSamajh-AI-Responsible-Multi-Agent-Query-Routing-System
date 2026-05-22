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
                deep: '#0B0E14',
            },
            animation: {
                'gradient-x': 'gradient-x 15s ease infinite',
                'float': 'float 6s ease-in-out infinite',
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'typing': 'typing 2s steps(20, end), blink .75s step-end infinite',
            },
            keyframes: {
                'gradient-x': {
                    '0%, 100%': {
                        'background-size': '200% 200%',
                        'background-position': 'left center'
                    },
                    '50%': {
                        'background-size': '200% 200%',
                        'background-position': 'right center'
                    },
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                'typing': {
                    from: { width: '0' },
                    to: { width: '100%' },
                },
                'blink': {
                    'from, to': { borderColor: 'transparent' },
                    '50%': { borderColor: 'white' },
                }
            },
            boxShadow: {
                'glow-teal': '0 0 20px -5px rgba(45, 212, 191, 0.4)',
                'glow-violet': '0 0 20px -5px rgba(139, 92, 246, 0.4)',
            }
        }
    },
    plugins: []
};
