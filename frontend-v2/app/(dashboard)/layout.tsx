"use client"

import { Sidebar } from "@/components/dashboard/Sidebar"
import { FeatureProvider } from "@/contexts/FeatureContext"
import { Toaster } from "sonner"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // TODO: Get from auth context
  const user = {
    role: "super-user",
    name: "Admin User",
    email: "admin@example.com",
  }

  return (
    <FeatureProvider>
      <div className="flex h-screen overflow-hidden bg-black">
        <Sidebar
          userRole={user.role}
          userName={user.name}
          userEmail={user.email}
        />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      <Toaster position="top-right" richColors />
    </FeatureProvider>
  )
}
