import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface StatCardProps {
  title: string
  value: string | number
  change?: string
  changeType?: "increase" | "decrease" | "neutral"
  icon?: string
  subtitle?: string
}

export function StatCard({
  title,
  value,
  change,
  changeType = "neutral",
  icon,
  subtitle,
}: StatCardProps) {
  const changeColor = {
    increase: "text-green-400",
    decrease: "text-red-400",
    neutral: "text-stone-400",
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-stone-400">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-stone-100">{value}</div>
        {change && (
          <p className={cn("text-xs", changeColor[changeType])}>
            {changeType === "increase" && "↑ "}
            {changeType === "decrease" && "↓ "}
            {change}
          </p>
        )}
        {subtitle && !change && (
          <p className="text-xs text-stone-500">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  )
}
