import * as React from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "../lib/utils"

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  status: "active" | "inactive" | "pending" | "success" | "error" | "warning"
  pulse?: boolean
  children?: React.ReactNode
}

const statusConfig = {
  active: {
    color: "bg-green-900 text-green-100 border-green-800",
    pulseColor: "bg-green-500",
    label: "활성"
  },
  inactive: {
    color: "bg-stone-700 text-stone-300 border-stone-600",
    pulseColor: "bg-stone-500",
    label: "비활성"
  },
  pending: {
    color: "bg-yellow-900 text-yellow-100 border-yellow-800",
    pulseColor: "bg-yellow-500",
    label: "대기 중"
  },
  success: {
    color: "bg-green-900 text-green-100 border-green-800",
    pulseColor: "bg-green-500",
    label: "성공"
  },
  error: {
    color: "bg-red-900 text-red-100 border-red-800",
    pulseColor: "bg-red-500",
    label: "오류"
  },
  warning: {
    color: "bg-yellow-900 text-yellow-100 border-yellow-800",
    pulseColor: "bg-yellow-500",
    label: "경고"
  }
}

const StatusBadge = React.forwardRef<HTMLDivElement, StatusBadgeProps>(
  ({ className, status, pulse = false, children, ...props }, ref) => {
    const config = statusConfig[status]

    return (
      <div ref={ref} className={cn("inline-flex items-center gap-2", className)} {...props}>
        {pulse && (
          <span className="relative flex h-2 w-2">
            <span className={cn(
              "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
              config.pulseColor
            )} />
            <span className={cn(
              "relative inline-flex rounded-full h-2 w-2",
              config.pulseColor
            )} />
          </span>
        )}
        <Badge className={cn("border", config.color)}>
          {children || config.label}
        </Badge>
      </div>
    )
  }
)

StatusBadge.displayName = "StatusBadge"

export { StatusBadge }
