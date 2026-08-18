'use client'

import { Document } from '@/lib/types'
import { FileText, ImageIcon, Plus, Upload } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useRef } from 'react'
import { uploadDocument } from '@/lib/api'

interface SidebarProps {
  documents: Document[]
  activeDoc: string | null
  onSelectDoc: (filename: string) => void
  onRefresh: () => void
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function Sidebar({ documents, activeDoc, onSelectDoc, onRefresh }: SidebarProps) {
  const fileRef = useRef<HTMLInputElement>(null)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      await uploadDocument(file)
      onRefresh()
    } catch (err) {
      alert('Upload gagal: ' + (err as Error).message)
    }
    e.target.value = ''
  }

  return (
    <aside className="w-[220px] shrink-0 border-r border-gray-100 bg-white flex flex-col h-full">
      {/* Documents section */}
      <div className="px-3 pt-4 pb-2">
        <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest mb-2">Documents</p>

        <div className="space-y-1">
          {documents.length === 0 && (
            <p className="text-xs text-gray-400 px-2 py-3 text-center">No documents yet</p>
          )}
          {documents.map((doc) => (
            <button
              key={doc.filename}
              onClick={() => onSelectDoc(doc.filename)}
              className={cn(
                'w-full flex items-start gap-2.5 px-2.5 py-2 rounded-lg text-left transition-all',
                activeDoc === doc.filename
                  ? 'bg-blue-50 text-blue-700 border border-blue-100'
                  : 'hover:bg-gray-50 text-gray-700 border border-transparent',
              )}
            >
              {doc.is_pdf ? (
                <FileText className="w-4 h-4 mt-0.5 shrink-0 text-blue-500" />
              ) : (
                <ImageIcon className="w-4 h-4 mt-0.5 shrink-0 text-violet-500" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{doc.filename}</p>
                <p className="text-[10px] text-gray-400">
                  {doc.total_pages} page{doc.total_pages !== 1 ? 's' : ''} · {formatBytes(doc.size_bytes)}
                </p>
              </div>
            </button>
          ))}
        </div>

        {/* Upload button */}
        <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" className="hidden" onChange={handleUpload} />
        <button
          onClick={() => fileRef.current?.click()}
          className="mt-3 w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg border border-dashed border-gray-300 text-xs text-gray-500 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          Upload Document
        </button>
      </div>

      {/* Divider */}
      <div className="h-px bg-gray-100 mx-3 my-3" />

      {/* Navigation menu */}
      <nav className="px-3 flex-1">
        <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest mb-2">Menu</p>
        {[
          { label: 'Documents', active: true },
          { label: 'OCR History' },
          { label: 'Entities' },
          { label: 'Analytics' },
          { label: 'Settings' },
        ].map(({ label, active }) => (
          <button
            key={label}
            className={cn(
              'w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-medium transition-all mb-0.5',
              active ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700',
            )}
          >
            {label}
          </button>
        ))}
      </nav>

      {/* Footer: System status */}
      <div className="p-3 border-t border-gray-100">
        <div className="flex items-center gap-1.5 mb-1">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-[10px] font-medium text-gray-600">System Status</span>
        </div>
        <p className="text-[10px] text-gray-400">All systems operational</p>
      </div>
    </aside>
  )
}
