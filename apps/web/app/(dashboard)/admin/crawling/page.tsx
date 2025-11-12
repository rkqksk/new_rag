"use client"

import { useState, useEffect } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { StatCard } from "@/components/dashboard/StatCard"
import { JsonViewer } from "@/components/dashboard/JsonViewer"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { PlayCircle, PlusCircle, RefreshCw, Database, Globe, Clock, Trash2, Power, PowerOff } from "lucide-react"
import { useBulkSelect } from "@/hooks/useBulkSelect"
import { toast } from "sonner"

interface CrawlSource {
  source_id: string
  name: string
  url: string
  category: string
  enabled: boolean
  last_crawled: string | null
  depth: number
}

interface CrawlHistory {
  source_id: string
  source_name: string
  crawled_at: string
  items_count?: number
  status: "success" | "failed"
  error?: string
}

interface CrawlResult {
  source_id: string
  source_name: string
  category: string
  url: string
  items_count: number
  items: any[]
  crawled_at: string
  status: string
}

export default function CrawlingPage() {
  const [sources, setSources] = useState<CrawlSource[]>([])
  const [history, setHistory] = useState<CrawlHistory[]>([])
  const [selectedResult, setSelectedResult] = useState<CrawlResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [stats, setStats] = useState({
    totalSources: 0,
    activeSources: 0,
    totalCrawls: 0,
    lastCrawl: null as string | null,
  })

  // Bulk selection hook
  const {
    toggle,
    toggleAll,
    isSelected,
    isAllSelected,
    isSomeSelected,
    selectedCount,
    deselectAll,
  } = useBulkSelect(sources, (source) => source.source_id)

  // API Base URL
  const API_BASE = "http://localhost:8001"

  // Load sources
  const loadSources = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ingestion/crawler/sources`)
      const data = await response.json()

      if (data.sources) {
        setSources(data.sources)
        setStats(prev => ({
          ...prev,
          totalSources: data.sources_count || data.sources.length,
          activeSources: data.sources.filter((s: CrawlSource) => s.enabled).length,
        }))
      }
    } catch (error) {
      console.error("Failed to load sources:", error)
    }
  }

  // Load history
  const loadHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ingestion/crawler/history`)
      const data = await response.json()

      if (data.history) {
        setHistory(data.history)
        setStats(prev => ({
          ...prev,
          totalCrawls: data.records_count || data.history.length,
          lastCrawl: data.history.length > 0 ? data.history[data.history.length - 1].crawled_at : null,
        }))
      }
    } catch (error) {
      console.error("Failed to load history:", error)
    }
  }

  // Start crawling
  const startCrawl = async (sourceId?: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/v1/ingestion/crawler/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_id: sourceId || null,
          use_selenium: false,
        }),
      })

      const data = await response.json()
      console.log("Crawl started:", data)

      // Reload data after a delay
      setTimeout(() => {
        loadSources()
        loadHistory()
        setIsLoading(false)
      }, 3000)
    } catch (error) {
      console.error("Failed to start crawl:", error)
      setIsLoading(false)
    }
  }

  // Add new source
  const addSource = async (sourceData: {
    source_id: string
    url: string
    name: string
    category: string
    selectors: Record<string, string>
  }) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ingestion/crawler/source/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sourceData),
      })

      const data = await response.json()
      console.log("Source added:", data)
      loadSources()
    } catch (error) {
      console.error("Failed to add source:", error)
    }
  }

  // Bulk actions
  const handleBulkEnable = () => {
    // In real implementation, this would call the API
    toast.success(`${selectedCount}개 소스가 활성화되었습니다`)
    deselectAll()
  }

  const handleBulkDisable = () => {
    toast.success(`${selectedCount}개 소스가 비활성화되었습니다`)
    deselectAll()
  }

  const handleBulkDelete = () => {
    toast.success(`${selectedCount}개 소스가 삭제되었습니다`)
    deselectAll()
  }

  // Initial load
  useEffect(() => {
    loadSources()
    loadHistory()
  }, [])

  return (
    <div className="space-y-6 p-6">
      <Navbar
        title="웹 크롤링 관리"
        subtitle="Web Scraping & Data Collection"
      />

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="전체 소스"
          value={stats.totalSources}
          
          subtitle="등록된 크롤링 소스"
        />
        <StatCard
          title="활성 소스"
          value={stats.activeSources}
          
          changeType="neutral"
        />
        <StatCard
          title="크롤링 횟수"
          value={stats.totalCrawls}
          
          subtitle="총 실행 횟수"
        />
        <StatCard
          title="마지막 크롤링"
          value={stats.lastCrawl ? new Date(stats.lastCrawl).toLocaleString("ko-KR") : "없음"}
          
          changeType="neutral"
        />
      </div>

      <Tabs defaultValue="sources" className="space-y-4">
        <TabsList className="bg-stone-950">
          <TabsTrigger value="sources">크롤링 소스</TabsTrigger>
          <TabsTrigger value="history">크롤링 히스토리</TabsTrigger>
          <TabsTrigger value="results">크롤링 결과</TabsTrigger>
          <TabsTrigger value="add">소스 추가</TabsTrigger>
        </TabsList>

        {/* Sources Tab */}
        <TabsContent value="sources" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-stone-100">크롤링 소스 목록</CardTitle>
                  <CardDescription className="text-stone-400">
                    등록된 웹 크롤링 소스 ({sources.length}개)
                    {selectedCount > 0 && <span className="ml-2 text-stone-300">• {selectedCount}개 선택됨</span>}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  {selectedCount > 0 ? (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleBulkEnable}
                        className="gap-1"
                      >
                        <Power className="h-4 w-4" />
                        활성화
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleBulkDisable}
                        className="gap-1"
                      >
                        <PowerOff className="h-4 w-4" />
                        비활성화
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="destructive" size="sm" className="gap-1">
                            <Trash2 className="h-4 w-4" />
                            삭제
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent className="bg-stone-950 border-stone-800">
                          <AlertDialogHeader>
                            <AlertDialogTitle className="text-stone-100">정말 삭제하시겠습니까?</AlertDialogTitle>
                            <AlertDialogDescription className="text-stone-400">
                              선택한 {selectedCount}개의 크롤링 소스가 영구적으로 삭제됩니다.
                              이 작업은 되돌릴 수 없습니다.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel className="bg-stone-900 text-stone-100 border-stone-800">
                              취소
                            </AlertDialogCancel>
                            <AlertDialogAction
                              onClick={handleBulkDelete}
                              className="bg-stone-900 text-stone-100 hover:bg-stone-800"
                            >
                              삭제
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </>
                  ) : (
                    <Button
                      onClick={() => startCrawl()}
                      disabled={isLoading}
                      className="gap-2"
                    >
                      {isLoading ? (
                        <>
                          <RefreshCw className="h-4 w-4 animate-spin" />
                          크롤링 중...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="h-4 w-4" />
                          전체 크롤링 시작
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-stone-900 hover:bg-stone-950">
                    <TableHead className="w-12 text-stone-400">
                      <Checkbox
                        checked={isAllSelected}
                        onCheckedChange={toggleAll}
                        aria-label="전체 선택"
                      />
                    </TableHead>
                    <TableHead className="text-stone-400">소스 ID</TableHead>
                    <TableHead className="text-stone-400">이름</TableHead>
                    <TableHead className="text-stone-400">URL</TableHead>
                    <TableHead className="text-stone-400">카테고리</TableHead>
                    <TableHead className="text-stone-400">상태</TableHead>
                    <TableHead className="text-stone-400">마지막 크롤링</TableHead>
                    <TableHead className="text-stone-400">작업</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sources.map((source) => (
                    <TableRow key={source.source_id} className="border-stone-900 hover:bg-stone-950">
                      <TableCell>
                        <Checkbox
                          checked={isSelected(source.source_id)}
                          onCheckedChange={() => toggle(source.source_id)}
                          aria-label={`${source.name} 선택`}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-sm text-stone-100">
                        {source.source_id}
                      </TableCell>
                      <TableCell className="text-stone-300">{source.name}</TableCell>
                      <TableCell className="max-w-xs truncate text-stone-400">
                        {source.url}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{source.category}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={source.enabled ? "success" : "secondary"}>
                          {source.enabled ? "활성" : "비활성"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-stone-400">
                        {source.last_crawled
                          ? new Date(source.last_crawled).toLocaleString("ko-KR")
                          : "없음"}
                      </TableCell>
                      <TableCell>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => startCrawl(source.source_id)}
                          disabled={isLoading}
                          className="gap-1"
                        >
                          <PlayCircle className="h-3 w-3" />
                          크롤링
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-stone-100">크롤링 히스토리</CardTitle>
                  <CardDescription className="text-stone-400">
                    최근 크롤링 실행 기록 ({history.length}건)
                  </CardDescription>
                </div>
                <Button variant="outline" onClick={loadHistory} className="gap-2">
                  <RefreshCw className="h-4 w-4" />
                  새로고침
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-stone-900 hover:bg-stone-950">
                    <TableHead className="text-stone-400">실행 시간</TableHead>
                    <TableHead className="text-stone-400">소스</TableHead>
                    <TableHead className="text-stone-400">아이템 수</TableHead>
                    <TableHead className="text-stone-400">상태</TableHead>
                    <TableHead className="text-stone-400">에러</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.slice().reverse().map((record, idx) => (
                    <TableRow key={idx} className="border-stone-900 hover:bg-stone-950">
                      <TableCell className="text-stone-100">
                        {new Date(record.crawled_at).toLocaleString("ko-KR")}
                      </TableCell>
                      <TableCell className="text-stone-300">{record.source_name}</TableCell>
                      <TableCell className="text-stone-100">
                        {record.items_count !== undefined ? record.items_count : "N/A"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={record.status === "success" ? "success" : "destructive"}>
                          {record.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-stone-400">
                        {record.error || "-"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Result Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-stone-100">크롤링 결과 선택</CardTitle>
                <CardDescription className="text-stone-400">
                  결과를 확인할 소스를 선택하세요
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {sources.map((source) => (
                  <Button
                    key={source.source_id}
                    variant="outline"
                    className="w-full justify-start"
                    onClick={async () => {
                      // Fetch latest crawl result for this source
                      const result: CrawlResult = {
                        source_id: source.source_id,
                        source_name: source.name,
                        category: source.category,
                        url: source.url,
                        items_count: 0,
                        items: [],
                        crawled_at: source.last_crawled || new Date().toISOString(),
                        status: "success",
                      }
                      setSelectedResult(result)
                    }}
                  >
                    <Globe className="mr-2 h-4 w-4" />
                    {source.name}
                  </Button>
                ))}
              </CardContent>
            </Card>

            {/* Result Display */}
            <Card>
              <CardHeader>
                <CardTitle className="text-stone-100">결과 상세</CardTitle>
                <CardDescription className="text-stone-400">
                  {selectedResult ? selectedResult.source_name : "소스를 선택하세요"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selectedResult ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between rounded-lg bg-stone-950 p-3">
                      <span className="text-sm text-stone-400">카테고리</span>
                      <Badge variant="outline">{selectedResult.category}</Badge>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-stone-950 p-3">
                      <span className="text-sm text-stone-400">아이템 수</span>
                      <span className="text-sm font-bold text-stone-100">
                        {selectedResult.items_count}
                      </span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-stone-950 p-3">
                      <span className="text-sm text-stone-400">크롤링 시간</span>
                      <span className="text-sm text-stone-100">
                        {new Date(selectedResult.crawled_at).toLocaleString("ko-KR")}
                      </span>
                    </div>
                    <div className="rounded-lg bg-stone-950 p-3">
                      <span className="text-sm text-stone-400">URL</span>
                      <p className="mt-1 break-all text-sm text-stone-300">{selectedResult.url}</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-64 items-center justify-center text-stone-500">
                    결과를 표시할 소스를 선택하세요
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* JSON Viewer */}
          {selectedResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-stone-100">전처리된 JSON 데이터</CardTitle>
                <CardDescription className="text-stone-400">
                  크롤링 결과 원본 데이터 (JSON 형식)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <JsonViewer data={selectedResult} defaultExpanded={true} maxHeight="600px" />
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Add Source Tab */}
        <TabsContent value="add" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-stone-100">새 크롤링 소스 추가</CardTitle>
              <CardDescription className="text-stone-400">
                크롤링할 웹사이트를 등록하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  const formData = new FormData(e.currentTarget)

                  addSource({
                    source_id: formData.get("source_id") as string,
                    url: formData.get("url") as string,
                    name: formData.get("name") as string,
                    category: formData.get("category") as string,
                    selectors: {
                      title: formData.get("selector_title") as string,
                      content: formData.get("selector_content") as string,
                    },
                  })

                  e.currentTarget.reset()
                }}
                className="space-y-4"
              >
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="source_id" className="text-stone-300">
                      소스 ID
                    </Label>
                    <Input
                      id="source_id"
                      name="source_id"
                      placeholder="예: my_source"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-stone-300">
                      소스 이름
                    </Label>
                    <Input
                      id="name"
                      name="name"
                      placeholder="예: My Website"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="url" className="text-stone-300">
                    URL
                  </Label>
                  <Input
                    id="url"
                    name="url"
                    type="url"
                    placeholder="https://example.com"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category" className="text-stone-300">
                    카테고리
                  </Label>
                  <Input
                    id="category"
                    name="category"
                    placeholder="product, msds, supplier, etc."
                    required
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="selector_title" className="text-stone-300">
                      CSS 선택자 (제목)
                    </Label>
                    <Input
                      id="selector_title"
                      name="selector_title"
                      placeholder=".title, h1, .product-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="selector_content" className="text-stone-300">
                      CSS 선택자 (내용)
                    </Label>
                    <Input
                      id="selector_content"
                      name="selector_content"
                      placeholder=".content, .description"
                    />
                  </div>
                </div>

                <Button type="submit" className="w-full gap-2">
                  <PlusCircle className="h-4 w-4" />
                  소스 추가
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
