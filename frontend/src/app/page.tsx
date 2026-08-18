'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { Document, OcrResult, SafetyStatus } from '@/lib/types'
import { fetchDocuments, fetchDocumentMeta, fetchSafetyStatus } from '@/lib/api'
import StatusBar from '@/components/StatusBar'
import Sidebar from '@/components/Sidebar'
import DocumentViewer from '@/components/DocumentViewer'
import OcrInspector from '@/components/OcrInspector'
import ChatPanel from '@/components/ChatPanel'

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [activeDoc, setActiveDoc] = useState<Document | null>(null)
  const [activePage, setActivePage] = useState(1)
  const [ocrResult, setOcrResult] = useState<OcrResult | null>(null)
  const [isOcrLoading, setIsOcrLoading] = useState(false)
  const [safety, setSafety] = useState<SafetyStatus | null>(null)

  const safetyRef = useRef<NodeJS.Timeout | null>(null)

  const loadDocuments = useCallback(async () => {
    try {
      const docs = await fetchDocuments()
      setDocuments(docs)
    } catch (_) {}
  }, [])

  const loadSafety = useCallback(async () => {
    try {
      const s = await fetchSafetyStatus()
      setSafety(s)
    } catch (_) {}
  }, [])

  useEffect(() => {
    loadDocuments()
    loadSafety()
    safetyRef.current = setInterval(loadSafety, 5000)
    return () => {
      if (safetyRef.current) clearInterval(safetyRef.current)
    }
  }, [loadDocuments, loadSafety])

  async function handleSelectDoc(filename: string) {
    try {
      const meta = await fetchDocumentMeta(filename)
      setActiveDoc(meta)
      setActivePage(1)
      setOcrResult(null)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-white overflow-hidden font-sans">
      <StatusBar
        status={safety}
        activePdf={activeDoc?.filename ?? null}
        activePageCount={activeDoc?.total_pages ?? 0}
      />

      <div className="flex flex-1 min-h-0">
        {/* Left sidebar */}
        <Sidebar
          documents={documents}
          activeDoc={activeDoc?.filename ?? null}
          onSelectDoc={handleSelectDoc}
          onRefresh={loadDocuments}
        />

        {/* Center: viewer + inspector stacked */}
        <div className="flex flex-col flex-1 min-w-0">
          {activeDoc ? (
            <>
              {/* Document viewer (top portion) */}
              <div className="flex-1 min-h-0 border-b border-gray-100">
                <DocumentViewer
                  filename={activeDoc.filename}
                  totalPages={activeDoc.total_pages}
                  onOcrResult={(r) => { setOcrResult(r); setIsOcrLoading(false) }}
                  onOcrStart={() => setIsOcrLoading(true)}
                  onOcrError={(msg) => { alert('OCR Error: ' + msg); setIsOcrLoading(false) }}
                  isOcrLoading={isOcrLoading}
                />
              </div>

              {/* OCR inspector (bottom panel) */}
              <div className="h-72 shrink-0 overflow-hidden border-t border-gray-100">
                <OcrInspector result={ocrResult} isLoading={isOcrLoading} />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <p className="text-base font-bold text-gray-700 mb-1">No document selected</p>
                <p className="text-sm text-gray-400">Upload a PDF or image from the left panel to begin</p>
              </div>
            </div>
          )}
        </div>

        {/* Right chat panel */}
        <div className="w-[360px] shrink-0 h-full">
          <ChatPanel activeDoc={activeDoc?.filename ?? null} activePage={activePage} />
        </div>
      </div>
    </div>
  )
}
