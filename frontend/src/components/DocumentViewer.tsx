'use client'

import { useState } from 'react'
import Image from 'next/image'
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Maximize2, Loader2, ScanLine } from 'lucide-react'
import { getPageImageUrl, runOcr } from '@/lib/api'
import { OcrResult } from '@/lib/types'

interface DocumentViewerProps {
  filename: string
  totalPages: number
  onOcrResult: (result: OcrResult) => void
  onOcrStart: () => void
  onOcrError: (msg: string) => void
  isOcrLoading: boolean
}

export default function DocumentViewer({
  filename,
  totalPages,
  onOcrResult,
  onOcrStart,
  onOcrError,
  isOcrLoading,
}: DocumentViewerProps) {
  const [page, setPage] = useState(1)
  const [scale, setScale] = useState(1.5)

  const imgUrl = getPageImageUrl(filename, page, scale)

  async function handleExtractOcr() {
    onOcrStart()
    try {
      const result = await runOcr(filename, page, true)
      onOcrResult(result)
    } catch (e) {
      onOcrError((e as Error).message)
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Toolbar */}
      <div className="h-11 border-b border-gray-200 bg-white flex items-center px-3 gap-2 shrink-0">
        {/* Page nav */}
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 transition"
        >
          <ChevronLeft className="w-4 h-4 text-gray-600" />
        </button>
        <span className="text-xs text-gray-600 font-medium">
          Page <span className="text-gray-900 font-bold">{page}</span> / {totalPages}
        </span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
          className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 transition"
        >
          <ChevronRight className="w-4 h-4 text-gray-600" />
        </button>

        <div className="w-px h-4 bg-gray-200 mx-1" />

        {/* Zoom */}
        <button onClick={() => setScale((s) => Math.max(0.5, s - 0.25))} className="p-1.5 rounded hover:bg-gray-100 transition">
          <ZoomOut className="w-4 h-4 text-gray-600" />
        </button>
        <span className="text-xs font-medium text-gray-600 w-12 text-center">{Math.round(scale * 100 / 1.5)}%</span>
        <button onClick={() => setScale((s) => Math.min(3, s + 0.25))} className="p-1.5 rounded hover:bg-gray-100 transition">
          <ZoomIn className="w-4 h-4 text-gray-600" />
        </button>
        <button onClick={() => setScale(1.5)} className="p-1.5 rounded hover:bg-gray-100 transition">
          <Maximize2 className="w-4 h-4 text-gray-600" />
        </button>

        <div className="flex-1" />

        {/* Extract OCR Button */}
        <button
          onClick={handleExtractOcr}
          disabled={isOcrLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-xs font-semibold rounded-lg transition shadow-sm"
        >
          {isOcrLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <ScanLine className="w-3.5 h-3.5" />
          )}
          {isOcrLoading ? 'Extracting…' : 'Extract OCR'}
        </button>
      </div>

      {/* Image canvas */}
      <div className="flex-1 overflow-auto flex items-start justify-center p-6">
        <div className="shadow-xl rounded-lg overflow-hidden bg-white border border-gray-200">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imgUrl}
            alt={`${filename} page ${page}`}
            className="block max-w-none"
            style={{ maxWidth: '100%' }}
          />
        </div>
      </div>
    </div>
  )
}
