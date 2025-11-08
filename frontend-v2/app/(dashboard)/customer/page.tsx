import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function CustomerPage() {
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
              />
              <Button>검색</Button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-sm text-stone-400">인기 검색어:</span>
              {["50ml PET 병", "화장품 용기", "펌프 용기", "스포이드 병"].map((tag) => (
                <Badge key={tag} variant="outline" className="cursor-pointer hover:bg-stone-800">
                  {tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Featured Products */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-stone-100">추천 제품</h2>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
            {[
              { name: "50ml PET 병", code: "PET-50-001", price: "₩1,200", stock: "재고 있음", image: "🧴" },
              { name: "100ml PET 병", code: "PET-100-001", price: "₩1,800", stock: "재고 있음", image: "🧴" },
              { name: "펌프 용기 (200ml)", code: "PUMP-200-001", price: "₩2,500", stock: "재고 있음", image: "🧴" },
              { name: "스포이드 병 (30ml)", code: "DROP-30-001", price: "₩1,500", stock: "재고 부족", image: "🧴" },
              { name: "크림 용기 (50ml)", code: "CREAM-50-001", price: "₩2,200", stock: "재고 있음", image: "🫙" },
              { name: "분사기 용기", code: "SPRAY-100-001", price: "₩2,800", stock: "재고 있음", image: "🧴" },
              { name: "롤온 용기 (10ml)", code: "ROLL-10-001", price: "₩1,000", stock: "재고 있음", image: "💄" },
              { name: "에어리스 펌프", code: "AIR-50-001", price: "₩3,500", stock: "재고 있음", image: "🧴" },
            ].map((product) => (
              <Card key={product.code} className="group cursor-pointer transition-all hover:border-stone-600">
                <CardContent className="p-4">
                  <div className="mb-3 flex h-32 items-center justify-center rounded-lg bg-stone-950 text-6xl">
                    {product.image}
                  </div>
                  <h3 className="mb-1 font-medium text-stone-100 group-hover:text-stone-300">
                    {product.name}
                  </h3>
                  <p className="mb-2 text-xs text-stone-500">{product.code}</p>
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-lg font-bold text-stone-100">{product.price}</span>
                    <Badge variant={product.stock === "재고 있음" ? "success" : "warning"}>
                      {product.stock}
                    </Badge>
                  </div>
                  <Button className="w-full" variant="outline" size="sm">
                    견적 요청
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Orders */}
        <Card>
          <CardHeader>
            <CardTitle>최근 주문 내역</CardTitle>
            <CardDescription>나의 주문 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { id: "ORD-1234", product: "50ml PET 병 x 1000", date: "2025-11-08", status: "배송중", amount: "₩1,200,000" },
                { id: "ORD-1235", product: "펌프 용기 x 500", date: "2025-11-05", status: "완료", amount: "₩1,250,000" },
                { id: "ORD-1236", product: "크림 용기 x 800", date: "2025-11-03", status: "완료", amount: "₩1,760,000" },
              ].map((order) => (
                <div key={order.id} className="flex items-center gap-4 rounded-lg bg-stone-950 p-4 hover:bg-stone-900 transition-colors">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-stone-100">{order.product}</p>
                    <p className="text-xs text-stone-500">주문번호: {order.id} • {order.date}</p>
                  </div>
                  <span className="text-sm font-semibold text-stone-100">{order.amount}</span>
                  <Badge variant={order.status === "배송중" ? "warning" : "success"}>
                    {order.status}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    상세보기
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="cursor-pointer transition-all hover:border-stone-600">
            <CardHeader>
              <div className="text-4xl mb-2">📞</div>
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
              <div className="text-4xl mb-2">📦</div>
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
              <div className="text-4xl mb-2">⭐</div>
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
