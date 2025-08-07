/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      // ATOMIC DESIGN TOKENS
      colors: {
        background: {
          primary: '#0D0D0D', // Deep Black
          secondary: '#1C1C1C', // Jet Black
        },
        text: {
          primary: '#FEFEFE',
          secondary: '#E8E8E8',
          placeholder: '#B0B0B0',
          accent: '#CE9A54',
          disabled: '#B0B0B0',
        },
        accent: {
          DEFAULT: '#CE9A54', // Warm Ochre
          focus: '#C9A063',   // Pale Copper
        },
        border: {
          subtle: '#3C3C3C',
          secondary: '#CBAE88', // Almond Buff
        },
        status: {
          warning: '#A97142', // Caramel Café
          success: '#E8B467', // Muted Saffron
        },
        disabled: {
          bg: '#3C3C3C',
          text: '#B0B0B0',
        }
      },

      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Georgia', 'serif'],
      },

      // Major Third Type Scale (1.250x)
      fontSize: {
        'sm': '0.8rem',     // Small text, helpers
        'base': '1rem',     // Body
        'lg': '1.25rem',    // H3
        'xl': '1.563rem',   // H2
        '2xl': '1.953rem',  // H1
        '3xl': '2.441rem',  // Display
      },
      
      lineHeight: {
        'tight': '1.2',
        'normal': '1.6',
        'relaxed': '1.7',
      },

      // 4px Grid Spacing
      spacing: {
        '1': '4px', '2': '8px', '3': '12px', '4': '16px', '5': '20px',
        '6': '24px', '7': '28px', '8': '32px', '9': '36px', '10': '40px',
        '11': '44px', '12': '48px', '14': '56px', '16': '64px',
      },

      borderRadius: {
        'DEFAULT': '6px', // Subtle rounding
      },

      boxShadow: {
        'soft': '0 1px 6px rgba(0,0,0,0.10)',
        'focus': '0 0 0 2px #C9A063',
      },
      
      borderWidth: {
        '1': '1px',
        '2': '2px',
      },

      animation: {
        'fade-in': 'fadeIn 150ms ease-out',
        'slide-up': 'slideUp 200ms ease-out',
        'slow-spin': 'spin 2s linear infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(2px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
