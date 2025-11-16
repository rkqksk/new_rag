"use client"

import { useState } from "react"

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])

  const handleSearch = async () => {
    // TODO: Connect to apps/api
    console.log("Searching:", query)
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header - Pure Black, NO icons */}
      <header className="border-b border-gray-800 py-6">
        <div className="container mx-auto px-6">
          <h1 className="text-2xl font-semibold">
            RAG Enterprise
          </h1>
        </div>
      </header>

      {/* Search - Pure Black design */}
      <main className="container mx-auto px-6 py-12">
        <div className="max-w-2xl mx-auto">
          <div className="space-y-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search products..."
              className="
                w-full bg-black border border-gray-800 text-white text-lg
                px-6 py-4 rounded-md
                focus:outline-none focus:ring-2 focus:ring-white
                placeholder:text-gray-600
              "
            />

            <button
              onClick={handleSearch}
              className="
                w-full bg-white text-black py-4 rounded-md
                font-medium hover:bg-gray-200 transition-colors
              "
            >
              Search
            </button>
          </div>

          {/* Results - NO icons, text only */}
          {results.length > 0 && (
            <div className="mt-12 space-y-6">
              <h2 className="text-xl font-medium">
                Results
              </h2>

              {results.map((result, idx) => (
                <div
                  key={idx}
                  className="
                    bg-black border border-gray-800 rounded-lg p-6
                    hover:border-gray-700 transition-colors
                  "
                >
                  <h3 className="text-lg font-medium mb-2">
                    {result.title}
                  </h3>
                  <p className="text-gray-400">
                    {result.description}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-6 mt-12">
        <div className="container mx-auto px-6 text-center text-gray-600">
          <p>RAG Enterprise v10.0.0 - Pure Black Design</p>
        </div>
      </footer>
    </div>
  )
}
