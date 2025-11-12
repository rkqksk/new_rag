"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, Filter, Star, ShoppingCart, Heart } from "lucide-react"

interface Product {
  id: string
  name: string
  code: string
  price: string
  material: string
  capacity: string
  stock: number
  rating: number
  reviews: number
  category: string
  image?: string
}

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [priceRange, setPriceRange] = useState<string>("all")
  const [materialFilter, setMaterialFilter] = useState<string>("all")

  const products: Product[] = [
    {
      id: "1",
      name: "50ml PET 화장품 병",
      code: "PET-50-001",
      price: "₩1,200",
      material: "PET",
      capacity: "50ml",
      stock: 1500,
      rating: 4.8,
      reviews: 124,
      category: "화장품 용기",
    },
    {
      id: "2",
      name: "100ml 펌프 용기",
      code: "PUMP-100-002",
      price: "₩2,500",
      material: "PP",
      capacity: "100ml",
      stock: 800,
      rating: 4.6,
      reviews: 89,
      category: "펌프 용기",
    },
    {
      id: "3",
      name: "30ml 스포이드 병",
      code: "DROP-30-003",
      price: "₩1,800",
      material: "유리",
      capacity: "30ml",
      stock: 600,
      rating: 4.9,
      reviews: 156,
      category: "스포이드 용기",
    },
    {
      id: "4",
      name: "250ml 샴푸 용기",
      code: "SHP-250-004",
      price: "₩3,200",
      material: "HDPE",
      capacity: "250ml",
      stock: 450,
      rating: 4.7,
      reviews: 92,
      category: "대용량 용기",
    },
    {
      id: "5",
      name: "15ml 에센스 병",
      code: "ESS-15-005",
      price: "₩1,500",
      material: "유리",
      capacity: "15ml",
      stock: 1200,
      rating: 4.8,
      reviews: 167,
      category: "화장품 용기",
    },
    {
      id: "6",
      name: "500ml 샤워젤 용기",
      code: "GEL-500-006",
      price: "₩4,500",
      material: "PET",
      capacity: "500ml",
      stock: 350,
      rating: 4.5,
      reviews: 73,
      category: "대용량 용기",
    },
  ]

  const categories = ["all", "화장품 용기", "펌프 용기", "스포이드 용기", "대용량 용기"]
  const materials = ["all", "PET", "PP", "HDPE", "유리"]
  const priceRanges = [
    { label: "전체", value: "all" },
    { label: "₩0 - ₩2,000", value: "0-2000" },
    { label: "₩2,000 - ₩4,000", value: "2000-4000" },
    { label: "₩4,000+", value: "4000+" },
  ]

  const filteredProducts = products.filter((product) => {
    const matchesSearch =
      searchQuery === "" ||
      product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      product.code.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === "all" || product.category === selectedCategory
    const matchesMaterial = materialFilter === "all" || product.material === materialFilter
    return matchesSearch && matchesCategory && matchesMaterial
  })

  return (
    <div>
      <Navbar title="제품 검색" subtitle="원하는 제품을 찾아보세요" />

      <div className="p-6 space-y-6">
        {/* Search Bar */}
        <Card>
          <CardContent className="p-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-3 h-4 w-4 text-stone-500" />
                <Input
                  placeholder="제품명, 코드, 재질로 검색..."
                  className="pl-9"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Button variant="outline">
                <Filter className="mr-2 h-4 w-4" />
                필터
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Filters */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">카테고리</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <Badge
                    key={category}
                    variant={selectedCategory === category ? "default" : "outline"}
                    className={`cursor-pointer ${
                      selectedCategory === category
                        ? "bg-stone-700 text-stone-100"
                        : "hover:bg-stone-800"
                    }`}
                    onClick={() => setSelectedCategory(category)}
                  >
                    {category === "all" ? "전체" : category}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">재질</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {materials.map((material) => (
                  <Badge
                    key={material}
                    variant={materialFilter === material ? "default" : "outline"}
                    className={`cursor-pointer ${
                      materialFilter === material
                        ? "bg-stone-700 text-stone-100"
                        : "hover:bg-stone-800"
                    }`}
                    onClick={() => setMaterialFilter(material)}
                  >
                    {material === "all" ? "전체" : material}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">가격대</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {priceRanges.map((range) => (
                  <Badge
                    key={range.value}
                    variant={priceRange === range.value ? "default" : "outline"}
                    className={`cursor-pointer ${
                      priceRange === range.value
                        ? "bg-stone-700 text-stone-100"
                        : "hover:bg-stone-800"
                    }`}
                    onClick={() => setPriceRange(range.value)}
                  >
                    {range.label}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Results Count */}
        <div className="flex items-center justify-between">
          <p className="text-sm text-stone-400">
            <span className="font-semibold text-stone-100">{filteredProducts.length}</span>개 제품 발견
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              최신순
            </Button>
            <Button variant="outline" size="sm">
              가격순
            </Button>
            <Button variant="outline" size="sm">
              인기순
            </Button>
          </div>
        </div>

        {/* Products Grid */}
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
          {filteredProducts.map((product) => (
            <Card
              key={product.id}
              className="group cursor-pointer transition-all hover:border-stone-600"
            >
              <CardContent className="p-4">
                {/* Image Placeholder */}
                <div className="mb-3 flex h-40 items-center justify-center rounded-lg bg-stone-950 relative overflow-hidden group-hover:bg-stone-900 transition-colors">
                  <div className="text-center text-stone-400">
                    <p className="text-sm font-medium">{product.material}</p>
                    <p className="text-xs">{product.capacity}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Heart className="h-4 w-4" />
                  </Button>
                </div>

                {/* Product Info */}
                <div className="space-y-2">
                  <div>
                    <h3 className="font-medium text-stone-100 group-hover:text-stone-300 line-clamp-2">
                      {product.name}
                    </h3>
                    <p className="text-xs text-stone-500">{product.code}</p>
                  </div>

                  <Badge variant="outline" className="bg-stone-900 text-stone-300 text-xs">
                    {product.category}
                  </Badge>

                  {/* Rating */}
                  <div className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-stone-600 text-stone-600" />
                    <span className="text-xs font-medium text-stone-300">{product.rating}</span>
                    <span className="text-xs text-stone-500">({product.reviews})</span>
                  </div>

                  {/* Stock */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-stone-400">재고</span>
                    <Badge
                      variant="outline"
                      className={
                        product.stock > 500
                          ? "bg-stone-800 text-stone-300"
                          : "bg-stone-900 text-stone-400"
                      }
                    >
                      {product.stock}개
                    </Badge>
                  </div>

                  {/* Price */}
                  <div className="flex items-center justify-between pt-2 border-t border-stone-800">
                    <span className="text-lg font-bold text-stone-100">{product.price}</span>
                    <Button size="sm" variant="outline">
                      <ShoppingCart className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Load More */}
        {filteredProducts.length > 0 && (
          <div className="flex justify-center">
            <Button variant="outline">더 보기</Button>
          </div>
        )}

        {/* Popular Tags */}
        <Card>
          <CardHeader>
            <CardTitle>인기 검색어</CardTitle>
            <CardDescription>자주 검색되는 제품</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {[
                "50ml PET 병",
                "화장품 용기",
                "펌프 용기",
                "스포이드 병",
                "샴푸 용기",
                "에센스 병",
                "대용량 용기",
                "투명 용기",
              ].map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="cursor-pointer hover:bg-stone-800"
                  onClick={() => setSearchQuery(tag)}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
