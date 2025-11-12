"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { Feature, FeatureManager, DEFAULT_FEATURES } from '@/lib/features'

interface FeatureContextType {
  features: Feature[]
  isEnabled: (featureId: string) => boolean
  toggle: (featureId: string) => void
  enable: (featureId: string) => void
  disable: (featureId: string) => void
  resetToDefaults: () => void
  enableAll: () => void
  disableAll: () => void
  getFeaturesByCategory: (category: Feature['category']) => Feature[]
}

const FeatureContext = createContext<FeatureContextType | undefined>(undefined)

export function FeatureProvider({ children }: { children: ReactNode }) {
  const [manager] = useState(() => new FeatureManager())
  const [features, setFeatures] = useState<Feature[]>([])

  const refresh = () => {
    setFeatures(manager.getAllFeatures())
  }

  useEffect(() => {
    refresh()
  }, [])

  const contextValue: FeatureContextType = {
    features,
    isEnabled: (featureId) => manager.isEnabled(featureId),
    toggle: (featureId) => {
      manager.toggle(featureId)
      refresh()
    },
    enable: (featureId) => {
      manager.enable(featureId)
      refresh()
    },
    disable: (featureId) => {
      manager.disable(featureId)
      refresh()
    },
    resetToDefaults: () => {
      manager.resetToDefaults()
      refresh()
    },
    enableAll: () => {
      manager.enableAll()
      refresh()
    },
    disableAll: () => {
      manager.disableAll()
      refresh()
    },
    getFeaturesByCategory: (category) => manager.getFeaturesByCategory(category),
  }

  return (
    <FeatureContext.Provider value={contextValue}>
      {children}
    </FeatureContext.Provider>
  )
}

export function useFeatures() {
  const context = useContext(FeatureContext)
  if (context === undefined) {
    throw new Error('useFeatures must be used within a FeatureProvider')
  }
  return context
}

// Convenience hook for checking single feature
export function useFeature(featureId: string): boolean {
  const { isEnabled } = useFeatures()
  return isEnabled(featureId)
}
