"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Search,
  X,
  Filter,
  Download,
  ChevronDown,
  ChevronUp,
  Calendar,
  SlidersHorizontal
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

export interface SearchFilters {
  keyword?: string
  category?: string
  status?: string
  dateFrom?: string
  dateTo?: string
  sortBy?: string
  sortOrder?: "asc" | "desc"
}

export interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void
  onExport?: (format: "csv" | "json") => void
  categories?: { value: string; label: string }[]
  statuses?: { value: string; label: string }[]
  sortOptions?: { value: string; label: string }[]
  placeholder?: string
  showExport?: boolean
  showSort?: boolean
  className?: string
}

const defaultCategories = [
  { value: "all", label: "전체 카테고리" },
  { value: "crawling", label: "크롤링" },
  { value: "search", label: "검색" },
  { value: "user", label: "사용자" },
  { value: "system", label: "시스템" },
]

const defaultStatuses = [
  { value: "all", label: "전체 상태" },
  { value: "success", label: "성공" },
  { value: "failed", label: "실패" },
  { value: "pending", label: "대기 중" },
  { value: "active", label: "활성" },
  { value: "inactive", label: "비활성" },
]

const defaultSortOptions = [
  { value: "timestamp", label: "시간순" },
  { value: "name", label: "이름순" },
  { value: "status", label: "상태순" },
  { value: "category", label: "카테고리순" },
]

export function AdvancedSearch({
  onSearch,
  onExport,
  categories = defaultCategories,
  statuses = defaultStatuses,
  sortOptions = defaultSortOptions,
  placeholder = "키워드로 검색...",
  showExport = true,
  showSort = true,
  className
}: AdvancedSearchProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>({
    keyword: "",
    category: "all",
    status: "all",
    dateFrom: "",
    dateTo: "",
    sortBy: "timestamp",
    sortOrder: "desc"
  })

  const handleFilterChange = (key: keyof SearchFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleSearch = () => {
    // Filter out "all" values and empty strings
    const activeFilters: SearchFilters = Object.entries(filters).reduce((acc, [key, value]) => {
      if (value && value !== "all" && value !== "") {
        acc[key as keyof SearchFilters] = value
      }
      return acc
    }, {} as SearchFilters)

    onSearch(activeFilters)
    toast.success(`검색 필터 적용됨 (${Object.keys(activeFilters).length}개 조건)`)
  }

  const handleClearFilters = () => {
    const clearedFilters: SearchFilters = {
      keyword: "",
      category: "all",
      status: "all",
      dateFrom: "",
      dateTo: "",
      sortBy: "timestamp",
      sortOrder: "desc"
    }
    setFilters(clearedFilters)
    onSearch({})
    toast.success("모든 필터가 초기화되었습니다")
  }

  const handleExport = (format: "csv" | "json") => {
    if (onExport) {
      onExport(format)
      toast.success(`${format.toUpperCase()} 파일로 내보내기 시작...`)
    }
  }

  const toggleSortOrder = () => {
    setFilters(prev => ({
      ...prev,
      sortOrder: prev.sortOrder === "asc" ? "desc" : "asc"
    }))
  }

  const activeFilterCount = Object.entries(filters).filter(([key, value]) => {
    if (key === "sortBy" || key === "sortOrder") return false
    return value && value !== "all" && value !== ""
  }).length

  return (
    <div className={cn("space-y-4", className)}>
      {/* Quick Search Bar */}
      <div className="flex items-center gap-2">
        {/* Keyword Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-500" />
          <Input
            placeholder={placeholder}
            value={filters.keyword}
            onChange={(e) => handleFilterChange("keyword", e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="pl-10"
          />
        </div>

        {/* Category Filter */}
        <Select
          value={filters.category}
          onValueChange={(value) => handleFilterChange("category", value)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="카테고리" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((cat) => (
              <SelectItem key={cat.value} value={cat.value}>
                {cat.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Status Filter */}
        <Select
          value={filters.status}
          onValueChange={(value) => handleFilterChange("status", value)}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="상태" />
          </SelectTrigger>
          <SelectContent>
            {statuses.map((status) => (
              <SelectItem key={status.value} value={status.value}>
                {status.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Advanced Filters Toggle */}
        <Button
          variant="outline"
          onClick={() => setIsExpanded(!isExpanded)}
          className="gap-2"
        >
          <SlidersHorizontal className="h-4 w-4" />
          고급 필터
          {activeFilterCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-600 text-white rounded-full">
              {activeFilterCount}
            </span>
          )}
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 ml-1" />
          ) : (
            <ChevronDown className="h-4 w-4 ml-1" />
          )}
        </Button>

        {/* Search Button */}
        <Button onClick={handleSearch} className="gap-2">
          <Search className="h-4 w-4" />
          검색
        </Button>

        {/* Clear Filters */}
        {activeFilterCount > 0 && (
          <Button variant="ghost" onClick={handleClearFilters} className="gap-2">
            <X className="h-4 w-4" />
            초기화
          </Button>
        )}
      </div>

      {/* Advanced Filters Panel */}
      {isExpanded && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              고급 검색 필터
            </CardTitle>
            <CardDescription>
              상세한 조건으로 검색 결과를 필터링하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Date Range */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="dateFrom" className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  시작 날짜
                </Label>
                <Input
                  id="dateFrom"
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => handleFilterChange("dateFrom", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="dateTo" className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  종료 날짜
                </Label>
                <Input
                  id="dateTo"
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => handleFilterChange("dateTo", e.target.value)}
                />
              </div>
            </div>

            {/* Sort Options */}
            {showSort && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sortBy">정렬 기준</Label>
                  <Select
                    value={filters.sortBy}
                    onValueChange={(value) => handleFilterChange("sortBy", value)}
                  >
                    <SelectTrigger id="sortBy">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {sortOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>정렬 순서</Label>
                  <Button
                    variant="outline"
                    onClick={toggleSortOrder}
                    className="w-full justify-between"
                  >
                    {filters.sortOrder === "asc" ? "오름차순" : "내림차순"}
                    {filters.sortOrder === "asc" ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            )}

            {/* Export Options */}
            {showExport && onExport && (
              <div className="pt-4 border-t border-stone-800">
                <Label className="mb-2 block">데이터 내보내기</Label>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleExport("csv")}
                    className="flex-1 gap-2"
                  >
                    <Download className="h-4 w-4" />
                    CSV로 내보내기
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleExport("json")}
                    className="flex-1 gap-2"
                  >
                    <Download className="h-4 w-4" />
                    JSON으로 내보내기
                  </Button>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={handleClearFilters}>
                초기화
              </Button>
              <Button onClick={handleSearch} className="gap-2">
                <Search className="h-4 w-4" />
                검색 적용
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Filters Display */}
      {activeFilterCount > 0 && !isExpanded && (
        <div className="flex items-center gap-2 text-sm text-stone-400">
          <Filter className="h-4 w-4" />
          <span>활성 필터: {activeFilterCount}개</span>
          <Button
            variant="link"
            onClick={() => setIsExpanded(true)}
            className="h-auto p-0 text-blue-400 hover:text-blue-300"
          >
            보기
          </Button>
        </div>
      )}
    </div>
  )
}
