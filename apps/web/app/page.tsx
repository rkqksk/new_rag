import Link from "next/link"

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-black">
      <div className="flex flex-col items-center">
        <h1 className="mb-12 text-6xl font-bold text-stone-100">
          PETER
        </h1>
        <Link
          href="/login"
          className="rounded-lg bg-stone-700 px-8 py-3 text-lg font-medium text-stone-100 hover:bg-stone-600"
        >
          LOGIN
        </Link>
      </div>
    </div>
  )
}
