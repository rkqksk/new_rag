"use client"

import { Input } from "@/components/ui/input"
import { NotificationCenter } from "@/components/dashboard/NotificationCenter"

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
        <div className="w-64">
          <Input
            placeholder="검색..."
          />
        </div>

        {/* Notifications */}
        <NotificationCenter />
      </div>
    </div>
  )
}
