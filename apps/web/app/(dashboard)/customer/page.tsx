"use client"

import { useState, useEffect } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface Product {
  id: string
  name: string
  code: string
  price: string
  stock: string
  description?: string
  material?: string
  capacity?: string
  score?: number
}

interface SearchResult {
  query: string
  total_results: number
  results: any[]
  search_strategy: string
  performance: any
}

export default function CustomerPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([])
  const [recentOrders, setRecentOrders] = useState<any[]>([])

  useEffect(() => {
    // Fetch featured products on mount
    fetchFeaturedProducts()
    fetchRecentOrders()
  }, [])

  const fetchFeaturedProducts = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/hybrid/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: 'PET 병 화장품 용기',
          top_k: 8,
          enable_reranking: true
        })
      })

      if (response.ok) {
        const data: SearchResult = await response.json()
        const products = data.results.slice(0, 8).map((result: any, idx: number) => ({
          id: result.id || `prod-${idx}`,
          name: result.metadata?.제품명 || result.text?.substring(0, 30) || '제품명 없음',
          code: result.metadata?.제품코드 || `PROD-${idx}`,
          price: result.metadata?.가격 || '₩1,200',
          stock: result.score > 0.8 ? '재고 있음' : '재고 부족',
          description: result.text?.substring(0, 100),
          material: result.metadata?.재질,
          capacity: result.metadata?.용량,
          score: result.score
        }))
        setFeaturedProducts(products)
      }
    } catch (error) {
      console.error('Failed to fetch featured products:', error)
    }
  }

  const fetchRecentOrders = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/dashboard/documents?limit=3')
      if (response.ok) {
        const data = await response.json()
        setRecentOrders(data.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch recent orders:', error)
      // Fallback mock data
      setRecentOrders([
        { id: "ORD-1234", product: "50ml PET 병 x 1000", date: "2025-11-08", status: "배송중", amount: "₩1,200,000" },
        { id: "ORD-1235", product: "펌프 용기 x 500", date: "2025-11-05", status: "완료", amount: "₩1,250,000" },
      ])
    }
  }

  const handleSearch = async (query?: string) => {
    const searchText = query || searchQuery
    if (!searchText.trim()) return

    setLoading(true)
    try {
      const response = await fetch('http://localhost:8001/api/v1/hybrid/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchText,
          top_k: 20,
          enable_reranking: true,
          dense_weight: 0.6,
          sparse_weight: 0.4
        })
      })

      if (response.ok) {
        const data: SearchResult = await response.json()
        const products = data.results.map((result: any, idx: number) => ({
          id: result.id || `search-${idx}`,
          name: result.metadata?.제품명 || result.text?.substring(0, 30) || '제품명 없음',
          code: result.metadata?.제품코드 || `PROD-${idx}`,
          price: result.metadata?.가격 || '₩1,200',
          stock: result.score > 0.8 ? '재고 있음' : '재고 부족',
          description: result.text?.substring(0, 100),
          material: result.metadata?.재질,
          capacity: result.metadata?.용량,
          score: result.score
        }))
        setSearchResults(products)
      }
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickSearch = (tag: string) => {
    setSearchQuery(tag)
    handleSearch(tag)
  }

  const displayProducts = searchResults.length > 0 ? searchResults : featuredProducts

  return (
    <div>
      <Navbar title="제품 검색" subtitle="맞춤형 제품을 찾아보세요" />

      <div className="p-6 space-y-6">
        {/* Search Section */}
        <Card>
          <CardHeader>
            <CardTitle>AI 기반 제품 검색</CardTitle>
            <CardDescription>자연어로 원하는 제품을 검색하세요</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="예: 50ml PET 용기, 화장품 병, 투명한 플라스틱..."
                className="flex-1"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button onClick={() => handleSearch()} disabled={loading}>
                {loading ? '검색 중...' : '검색'}
              </Button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-sm text-stone-400">인기 검색어:</span>
              {["50ml PET 병", "화장품 용기", "펌프 용기", "스포이드 병"].map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="cursor-pointer hover:bg-stone-800"
                  onClick={() => handleQuickSearch(tag)}
                >
                  {tag}
                </Badge>
              ))}
            </div>
            {searchResults.length > 0 && (
              <div className="mt-4 pt-4 border-t border-stone-800">
                <p className="text-sm text-stone-400">
                  검색 결과: <span className="text-stone-100 font-semibold">{searchResults.length}개</span> 제품 발견
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Products Grid */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-stone-100">
            {searchResults.length > 0 ? '검색 결과' : '추천 제품'}
          </h2>
          {displayProducts.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
              {displayProducts.map((product) => (
                <Card key={product.id} className="group cursor-pointer transition-all hover:border-stone-600">
                  <CardContent className="p-4">
                    <div className="mb-3 flex h-32 items-center justify-center rounded-lg bg-stone-950">
                      <div className="text-center text-stone-400">
                        <p className="text-sm font-medium">{product.material || 'PET'}</p>
                        <p className="text-xs">{product.capacity || '50ml'}</p>
                      </div>
                    </div>
                    <h3 className="mb-1 font-medium text-stone-100 group-hover:text-stone-300">
                      {product.name}
                    </h3>
                    <p className="mb-2 text-xs text-stone-500">{product.code}</p>
                    {product.description && (
                      <p className="mb-2 text-xs text-stone-400 line-clamp-2">{product.description}</p>
                    )}
                    <div className="mb-3 flex items-center justify-between">
                      <span className="text-lg font-bold text-stone-100">{product.price}</span>
                      <Badge variant={product.stock === "재고 있음" ? "default" : "destructive"}>
                        {product.stock}
                      </Badge>
                    </div>
                    {product.score && (
                      <div className="mb-2">
                        <div className="flex items-center justify-between text-xs text-stone-500 mb-1">
                          <span>적합도</span>
                          <span>{(product.score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="h-1 bg-stone-900 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-stone-600 transition-all"
                            style={{ width: `${product.score * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    <Button className="w-full" variant="outline" size="sm">
                      견적 요청
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-stone-400">
              {loading ? '검색 중...' : '제품을 불러오는 중...'}
            </div>
          )}
        </div>

        {/* Recent Orders */}
        <Card>
          <CardHeader>
            <CardTitle>최근 주문 내역</CardTitle>
            <CardDescription>나의 주문 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentOrders.length > 0 ? (
                recentOrders.map((order, idx) => (
                  <div key={order.id || idx} className="flex items-center gap-4 rounded-lg bg-stone-950 p-4 hover:bg-stone-900 transition-colors">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-stone-100">{order.product || order.title}</p>
                      <p className="text-xs text-stone-500">
                        주문번호: {order.id} • {order.date || new Date(order.created_at).toLocaleDateString('ko-KR')}
                      </p>
                    </div>
                    <span className="text-sm font-semibold text-stone-100">{order.amount || '₩0'}</span>
                    <Badge variant={order.status === "배송중" ? "default" : "secondary"}>
                      {order.status || '완료'}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      상세보기
                    </Button>
                  </div>
                ))
              ) : (
                <div className="text-center py-4 text-stone-500">주문 내역이 없습니다</div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="cursor-pointer transition-all hover:border-stone-600">
            <CardHeader>
              <CardTitle>고객 지원</CardTitle>
              <CardDescription>문의사항이 있으신가요?</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                문의하기
              </Button>
            </CardContent>
          </Card>

          <Card className="cursor-pointer transition-all hover:border-stone-600">
            <CardHeader>
              <CardTitle>배송 추적</CardTitle>
              <CardDescription>주문하신 제품을 확인하세요</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                추적하기
              </Button>
            </CardContent>
          </Card>

          <Card className="cursor-pointer transition-all hover:border-stone-600">
            <CardHeader>
              <CardTitle>즐겨찾기</CardTitle>
              <CardDescription>자주 주문하는 제품</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                보러가기
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
