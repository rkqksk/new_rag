"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { copyToClipboard } from "@/lib/utils/copy"
import { exportToJSON, exportToCSV } from "@/lib/utils/export"

interface JsonViewerProps {
  data: any
  defaultExpanded?: boolean
  maxHeight?: string
  filename?: string
}

export function JsonViewer({ data, defaultExpanded = false, maxHeight = "400px", filename = "data" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await copyToClipboard(JSON.stringify(data, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleExportJSON = () => {
    exportToJSON(data, `${filename}.json`)
  }

  const handleExportCSV = () => {
    // If data is array, export directly; if object, wrap in array
    const arrayData = Array.isArray(data) ? data : [data]
    exportToCSV(arrayData, `${filename}.csv`)
  }

  return (
    <div className="relative rounded-lg border border-stone-800 bg-stone-950">
      <div className="flex items-center justify-between border-b border-stone-800 px-4 py-2">
        <span className="text-sm font-medium text-stone-400">JSON Data</span>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExportCSV}
            className="h-8 px-2 text-stone-400 hover:text-stone-100"
          >
            CSV
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExportJSON}
            className="h-8 px-2 text-stone-400 hover:text-stone-100"
          >
            JSON
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="h-8 px-2 text-stone-400 hover:text-stone-100"
          >
            {copied ? "Copied" : "Copy"}
          </Button>
        </div>
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
          <span className="w-4 text-center">{expanded ? "▼" : "▶"}</span>
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
          <span className="w-4 text-center">{expanded ? "▼" : "▶"}</span>
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
