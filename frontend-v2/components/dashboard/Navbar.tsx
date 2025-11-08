"use client"

import { Bell, Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

interface NavbarProps {
  title: string
  subtitle?: string
}

export function Navbar({ title, subtitle }: NavbarProps) {
  return (
    <div className="sticky top-0 z-10 border-b border-stone-800 bg-black/95 backdrop-blur supports-[backdrop-filter]:bg-black/60">
      <div className="flex h-16 items-center gap-4 px-6">
        {/* Title */}
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-stone-100">{title}</h2>
          {subtitle && <p className="text-sm text-stone-500">{subtitle}</p>}
        </div>

        {/* Search */}
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-stone-500" />
          <Input
            placeholder="검색..."
            className="pl-9"
          />
        </div>

        {/* Notifications */}
        <button className="relative rounded-lg p-2 text-stone-400 transition-colors hover:bg-stone-900 hover:text-stone-100">
          <Bell className="h-5 w-5" />
          <Badge
            variant="destructive"
            className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs"
          >
            3
          </Badge>
        </button>
      </div>
    </div>
  )
}
