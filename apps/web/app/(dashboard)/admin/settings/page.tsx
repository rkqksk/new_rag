"use client"

import { useState } from "react"
import { Navbar } from "@/components/dashboard/Navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { useFeatures } from "@/contexts/FeatureContext"
import { Feature } from "@/lib/features"
export default function SettingsPage() {
  const { features, toggle, enableAll, disableAll, resetToDefaults, getFeaturesByCategory } = useFeatures()
  const [searchQuery, setSearchQuery] = useState("")

  const filteredFeatures = features.filter(
    (f) =>
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const categories: Feature['category'][] = ['ui', 'functionality', 'accessibility', 'developer', 'data']

  const categoryLabels: Record<Feature['category'], string> = {
    core: '핵심',
    saas: 'SaaS',
    enterprise: '엔터프라이즈',
    experimental: '실험적',
    ui: 'UI/UX',
    functionality: '기능',
    accessibility: '접근성',
    developer: '개발자 도구',
    data: '데이터 관리',
  }

  const impactColors: Record<Feature['impact'], string> = {
    low: 'bg-stone-800 text-stone-100',
    medium: 'bg-stone-850 text-stone-100',
    high: 'bg-stone-900 text-stone-100',
  }

  const getStats = () => {
    const total = features.length
    const enabled = features.filter(f => f.enabled).length
    const disabled = total - enabled
    return { total, enabled, disabled }
  }

  const stats = getStats()

  return (
    <div className="space-y-6 p-6">
      <Navbar title="기능 설정" subtitle="Feature Flags & Settings" />

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-stone-400">전체 기능</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-stone-100">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-stone-400">활성화됨</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-stone-300">{stats.enabled}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-stone-400">비활성화됨</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-stone-400">{stats.disabled}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-stone-400">활성화율</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-stone-100">
              {Math.round((stats.enabled / stats.total) * 100)}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          
          <Input
            placeholder="기능 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button variant="outline" onClick={enableAll} className="gap-2">
          On
          전체 활성화
        </Button>
        <Button variant="outline" onClick={disableAll} className="gap-2">
          Off
          전체 비활성화
        </Button>
        <Button variant="outline" onClick={resetToDefaults} className="gap-2">
          Reset
          기본값 복원
        </Button>
      </div>

      {/* Feature List */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList className="bg-stone-950">
          <TabsTrigger value="all">전체 ({features.length})</TabsTrigger>
          {categories.map((cat) => (
            <TabsTrigger key={cat} value={cat}>
              {categoryLabels[cat]} ({getFeaturesByCategory(cat).length})
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="all" className="space-y-3">
          {filteredFeatures.map((feature) => (
            <FeatureCard key={feature.id} feature={feature} onToggle={() => toggle(feature.id)} />
          ))}
        </TabsContent>

        {categories.map((cat) => (
          <TabsContent key={cat} value={cat} className="space-y-3">
            {getFeaturesByCategory(cat)
              .filter(
                (f) =>
                  f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  f.description.toLowerCase().includes(searchQuery.toLowerCase())
              )
              .map((feature) => (
                <FeatureCard key={feature.id} feature={feature} onToggle={() => toggle(feature.id)} />
              ))}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}

function FeatureCard({ feature, onToggle }: { feature: Feature; onToggle: () => void }) {
  const impactColors: Record<Feature['impact'], string> = {
    low: 'bg-stone-800 text-stone-100',
    medium: 'bg-stone-850 text-stone-100',
    high: 'bg-stone-900 text-stone-100',
  }

  return (
    <Card className={feature.enabled ? 'border-stone-700' : 'border-stone-900 opacity-75'}>
      <CardContent className="flex items-center justify-between p-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-medium text-stone-100">{feature.name}</h3>
            <Badge variant="outline" className={impactColors[feature.impact]}>
              {feature.impact === 'low' && '낮음'}
              {feature.impact === 'medium' && '중간'}
              {feature.impact === 'high' && '높음'}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {feature.implementationTime}
            </Badge>
          </div>
          <p className="text-sm text-stone-400">{feature.description}</p>
          <div className="mt-2">
            <Badge variant="outline">{feature.category}</Badge>
          </div>
        </div>
        <div className="ml-4">
          <Switch checked={feature.enabled} onCheckedChange={onToggle} />
        </div>
      </CardContent>
    </Card>
  )
}
