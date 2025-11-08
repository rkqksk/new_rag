"use client"

import React, { useState } from "react"
import { ChevronDown, ChevronRight, Copy, Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

interface JsonViewerProps {
  data: any
  defaultExpanded?: boolean
  maxHeight?: string
}

export function JsonViewer({ data, defaultExpanded = false, maxHeight = "400px" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative rounded-lg border border-stone-800 bg-stone-950">
      <div className="flex items-center justify-between border-b border-stone-800 px-4 py-2">
        <span className="text-sm font-medium text-stone-400">JSON Data</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-8 px-2 text-stone-400 hover:text-stone-100"
        >
          {copied ? (
            <>
              <Check className="mr-1 h-4 w-4" />
              Copied
            </>
          ) : (
            <>
              <Copy className="mr-1 h-4 w-4" />
              Copy
            </>
          )}
        </Button>
      </div>
      <div
        className="overflow-auto p-4 font-mono text-sm"
        style={{ maxHeight }}
      >
        <JsonNode data={data} level={0} defaultExpanded={defaultExpanded} />
      </div>
    </div>
  )
}

interface JsonNodeProps {
  data: any
  level: number
  defaultExpanded?: boolean
  name?: string
}

function JsonNode({ data, level, defaultExpanded = false, name }: JsonNodeProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  const indent = level * 20

  if (data === null) {
    return (
      <div style={{ marginLeft: indent }}>
        {name && <span className="text-stone-500">{name}: </span>}
        <span className="text-red-400">null</span>
      </div>
    )
  }

  if (data === undefined) {
    return (
      <div style={{ marginLeft: indent }}>
        {name && <span className="text-stone-500">{name}: </span>}
        <span className="text-stone-600">undefined</span>
      </div>
    )
  }

  if (typeof data === "boolean") {
    return (
      <div style={{ marginLeft: indent }}>
        {name && <span className="text-stone-500">{name}: </span>}
        <span className="text-yellow-400">{data.toString()}</span>
      </div>
    )
  }

  if (typeof data === "number") {
    return (
      <div style={{ marginLeft: indent }}>
        {name && <span className="text-stone-500">{name}: </span>}
        <span className="text-green-400">{data}</span>
      </div>
    )
  }

  if (typeof data === "string") {
    const truncated = data.length > 100 ? data.substring(0, 100) + "..." : data
    return (
      <div style={{ marginLeft: indent }}>
        {name && <span className="text-stone-500">{name}: </span>}
        <span className="text-blue-400">"{truncated}"</span>
      </div>
    )
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return (
        <div style={{ marginLeft: indent }}>
          {name && <span className="text-stone-500">{name}: </span>}
          <span className="text-stone-400">[]</span>
        </div>
      )
    }

    return (
      <div style={{ marginLeft: indent }}>
        <div
          className="flex cursor-pointer items-center gap-1 text-stone-400 hover:text-stone-100"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          {name && <span className="text-stone-500">{name}: </span>}
          <span>[{data.length}]</span>
        </div>
        {expanded && (
          <div className="mt-1">
            {data.map((item, index) => (
              <JsonNode
                key={index}
                data={item}
                level={level + 1}
                defaultExpanded={defaultExpanded}
                name={`[${index}]`}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  if (typeof data === "object") {
    const keys = Object.keys(data)
    if (keys.length === 0) {
      return (
        <div style={{ marginLeft: indent }}>
          {name && <span className="text-stone-500">{name}: </span>}
          <span className="text-stone-400">{"{}"}</span>
        </div>
      )
    }

    return (
      <div style={{ marginLeft: indent }}>
        <div
          className="flex cursor-pointer items-center gap-1 text-stone-400 hover:text-stone-100"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          {name && <span className="text-stone-500">{name}: </span>}
          <span>{"{"}{keys.length}{"}"}</span>
        </div>
        {expanded && (
          <div className="mt-1">
            {keys.map((key) => (
              <JsonNode
                key={key}
                data={data[key]}
                level={level + 1}
                defaultExpanded={defaultExpanded}
                name={key}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  return null
}
