import type { Config } from "tailwindcss";

export default {
	darkMode: ["class"],
	content: [
		"./pages/**/*.{ts,tsx}",
		"./components/**/*.{ts,tsx}",
		"./app/**/*.{ts,tsx}",
		"./src/**/*.{ts,tsx}",
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			fontFamily: {
				'inter': ['Inter', 'sans-serif'],
			},
			spacing: {
				'1': 'var(--space-1)', /* 4px */
				'2': 'var(--space-2)', /* 8px */
				'3': 'var(--space-3)', /* 12px */
				'4': 'var(--space-4)', /* 16px */
				'5': 'var(--space-5)', /* 24px */
				'6': 'var(--space-6)', /* 32px */
				'8': 'var(--space-8)', /* 48px */
				'10': 'var(--space-10)', /* 64px */
			},
			colors: {
				/* Core Palette */
				primary: {
					DEFAULT: 'hsl(var(--color-primary-500))',
					500: 'hsl(var(--color-primary-500))',
				},
				secondary: {
					DEFAULT: 'hsl(var(--color-secondary-500))',
					500: 'hsl(var(--color-secondary-500))',
				},
				accent: {
					DEFAULT: 'hsl(var(--color-accent-500))',
					500: 'hsl(var(--color-accent-500))',
				},
				
				/* Neutral Palette */
				gray: {
					900: 'hsl(var(--color-gray-900))',
					700: 'hsl(var(--color-gray-700))',
					500: 'hsl(var(--color-gray-500))',
					300: 'hsl(var(--color-gray-300))',
					200: 'hsl(var(--color-gray-200))',
					100: 'hsl(var(--color-gray-100))',
				},
				white: 'hsl(var(--color-white))',

				/* Semantic Colors */
				success: {
					DEFAULT: 'hsl(var(--color-success-500))',
					500: 'hsl(var(--color-success-500))',
				},
				error: {
					DEFAULT: 'hsl(var(--color-error-500))',
					500: 'hsl(var(--color-error-500))',
				},
				warning: {
					DEFAULT: 'hsl(var(--color-warning-500))',
					500: 'hsl(var(--color-warning-500))',
				},
				info: {
					DEFAULT: 'hsl(var(--color-info-500))',
					500: 'hsl(var(--color-info-500))',
				},

				/* Legacy shadcn compatibility */
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out'
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
} satisfies Config;
