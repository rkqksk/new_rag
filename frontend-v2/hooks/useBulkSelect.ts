import { useState, useCallback } from "react"

export function useBulkSelect<T>(items: T[], getId: (item: T) => string) {
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const toggle = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const selectAll = useCallback(() => {
    setSelected(new Set(items.map(getId)))
  }, [items, getId])

  const deselectAll = useCallback(() => {
    setSelected(new Set())
  }, [])

  const toggleAll = useCallback(() => {
    if (selected.size === items.length) {
      deselectAll()
    } else {
      selectAll()
    }
  }, [selected.size, items.length, selectAll, deselectAll])

  const isSelected = useCallback(
    (id: string) => selected.has(id),
    [selected]
  )

  const isAllSelected = selected.size === items.length && items.length > 0

  const isSomeSelected = selected.size > 0 && selected.size < items.length

  const selectedItems = items.filter((item) => selected.has(getId(item)))

  return {
    selected,
    selectedItems,
    selectedCount: selected.size,
    toggle,
    selectAll,
    deselectAll,
    toggleAll,
    isSelected,
    isAllSelected,
    isSomeSelected,
  }
}
