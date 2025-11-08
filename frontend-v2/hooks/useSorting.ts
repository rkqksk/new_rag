import { useState, useMemo } from "react"

export type SortOrder = "asc" | "desc" | null

export interface SortState<T> {
  field: keyof T | null
  order: SortOrder
}

export function useSorting<T>(data: T[], initialField?: keyof T, initialOrder: SortOrder = "asc") {
  const [sortState, setSortState] = useState<SortState<T>>({
    field: initialField || null,
    order: initialOrder,
  })

  const sortedData = useMemo(() => {
    if (!sortState.field || !sortState.order) return data

    return [...data].sort((a, b) => {
      const aValue = a[sortState.field!]
      const bValue = b[sortState.field!]

      if (aValue === null || aValue === undefined) return 1
      if (bValue === null || bValue === undefined) return -1

      const comparison = aValue > bValue ? 1 : aValue < bValue ? -1 : 0
      return sortState.order === "asc" ? comparison : -comparison
    })
  }, [data, sortState])

  const handleSort = (field: keyof T) => {
    setSortState((prev) => {
      if (prev.field === field) {
        // Cycle through: asc -> desc -> null
        if (prev.order === "asc") return { field, order: "desc" }
        if (prev.order === "desc") return { field: null, order: null }
      }
      return { field, order: "asc" }
    })
  }

  const getSortIcon = (field: keyof T) => {
    if (sortState.field !== field) return "↕️"
    if (sortState.order === "asc") return "↑"
    if (sortState.order === "desc") return "↓"
    return "↕️"
  }

  return {
    sortedData,
    sortState,
    handleSort,
    getSortIcon,
  }
}
