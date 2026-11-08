import { type VariantProps, cva } from 'class-variance-authority'

export { default as Button } from './Button.vue'

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-[15px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-airmail-blue focus-visible:ring-offset-2 focus-visible:ring-offset-paper disabled:pointer-events-none disabled:opacity-50 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default: 'bg-ink text-paper hover:bg-ink/90',
        destructive: 'bg-airmail-red text-paper hover:bg-airmail-red/90',
        outline: 'border border-rule bg-sheet text-ink hover:border-ink-soft',
        secondary: 'bg-rule/40 text-ink hover:bg-rule/70',
        ghost: 'text-ink hover:bg-sheet',
        link: 'text-airmail-blue underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-9 px-3 text-[13px]',
        default: 'h-10 px-4',
        lg: 'h-12 px-6',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export type ButtonVariants = VariantProps<typeof buttonVariants>
