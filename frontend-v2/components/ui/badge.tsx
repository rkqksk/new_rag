import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-stone-700 text-stone-100 hover:bg-stone-600",
        secondary:
          "border-transparent bg-stone-800 text-stone-300 hover:bg-stone-700",
        destructive:
          "border-transparent bg-red-900 text-red-100 hover:bg-red-800",
        outline: "text-stone-300 border-stone-700",
        success:
          "border-transparent bg-green-900 text-green-100 hover:bg-green-800",
        warning:
          "border-transparent bg-yellow-900 text-yellow-100 hover:bg-yellow-800",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
