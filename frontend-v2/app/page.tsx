import Link from "next/link"

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-black">
      <div className="max-w-4xl px-8 text-center">
        <h1 className="mb-6 text-6xl font-bold text-stone-100">
          RAG Enterprise
        </h1>
        <p className="mb-12 text-xl text-stone-400">
          AI-powered Enterprise Platform
          <br />
          Multi-tier Authentication • Black + Natural Theme
        </p>

        <div className="flex flex-wrap justify-center gap-4">
          <Link
            href="/login"
            className="rounded-lg bg-stone-700 px-8 py-3 text-lg font-medium text-stone-100 transition-colors hover:bg-stone-600"
          >
            로그인
          </Link>
          <Link
            href="/register"
            className="rounded-lg border-2 border-stone-700 px-8 py-3 text-lg font-medium text-stone-100 transition-colors hover:bg-stone-900"
          >
            회원가입
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-lg border border-stone-800 bg-stone-950 p-6">
            <div className="mb-2 text-3xl">⚡</div>
            <h3 className="mb-2 text-lg font-semibold text-stone-100">
              Super-user Dashboard
            </h3>
            <p className="text-sm text-stone-400">
              시스템 관리, 사용자 관리, 전체 권한
            </p>
          </div>

          <div className="rounded-lg border border-stone-800 bg-stone-950 p-6">
            <div className="mb-2 text-3xl">💼</div>
            <h3 className="mb-2 text-lg font-semibold text-stone-100">
              Staff Portal
            </h3>
            <p className="text-sm text-stone-400">
              제조 관리, 품질 관리, 재고 관리
            </p>
          </div>

          <div className="rounded-lg border border-stone-800 bg-stone-950 p-6">
            <div className="mb-2 text-3xl">🔍</div>
            <h3 className="mb-2 text-lg font-semibold text-stone-100">
              Customer Area
            </h3>
            <p className="text-sm text-stone-400">
              제품 검색, 주문 관리, 고객 지원
            </p>
          </div>
        </div>

        <div className="mt-12 text-sm text-stone-600">
          <p>Powered by Next.js 14 + shadcn/ui + Tailwind CSS</p>
          <p className="mt-1">v2.0.0 • Black Background + Natural Theme</p>
        </div>
      </div>
    </div>
  )
}
