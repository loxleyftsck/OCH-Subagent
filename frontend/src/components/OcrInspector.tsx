'use client'

import { useState } from 'react'
import { OcrResult } from '@/lib/types'
import { CheckCircle, Clock, Cpu, FileJson, AlignLeft, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface OcrInspectorProps {
  result: OcrResult | null
  isLoading: boolean
}

type Tab = 'structured' | 'raw' | 'meta'

export default function OcrInspector({ result, isLoading }: OcrInspectorProps) {
  const [tab, setTab] = useState<Tab>('structured')

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white p-6">
        <div className="text-center">
          <div className="w-10 h-10 rounded-full border-2 border-blue-600 border-t-transparent animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-700">Running OCR extraction…</p>
          <p className="text-xs text-gray-400 mt-1">This may take a few seconds</p>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white p-6">
        <div className="text-center">
          <FileJson className="w-10 h-10 text-gray-200 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-500">No OCR result yet</p>
          <p className="text-xs text-gray-400 mt-1">Click "Extract OCR" to analyze the document</p>
        </div>
      </div>
    )
  }

  const struct = result.structured_data ?? {}
  const items: Array<{ name: string; qty: number; unit_price: number; total_price: number }> =
    (struct.items as typeof items) ?? []

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Tab bar */}
      <div className="flex items-center gap-0 border-b border-gray-100 px-3 pt-2 shrink-0">
        {(
          [
            { id: 'structured', label: 'Structured', icon: FileJson },
            { id: 'raw', label: 'Raw OCR Text', icon: AlignLeft },
            { id: 'meta', label: 'Metadata & Tokens', icon: Info },
          ] as { id: Tab; label: string; icon: React.ElementType }[]
        ).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-all mr-1',
              tab === id
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            )}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}

        <div className="flex-1" />
        {result.cached ? (
          <div className="flex items-center gap-1 text-[10px] text-emerald-600 font-medium">
            <CheckCircle className="w-3 h-3" />
            Cached
          </div>
        ) : (
          <div className="flex items-center gap-1 text-[10px] text-blue-600 font-medium">
            <Cpu className="w-3 h-3" />
            Completed {result.processing_time ? `in ${result.processing_time.toFixed(2)}s` : ''}
          </div>
        )}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-auto p-4">
        {tab === 'structured' && (
          <div className="space-y-4">
            {/* Document info grid */}
            <div className="grid grid-cols-3 gap-3">
              {/* Document fields */}
              <div className="col-span-1 bg-gray-50 rounded-xl p-3 border border-gray-100">
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Document</p>
                {Object.entries(struct)
                  .filter(([k]) => !['items', 'summary', 'structured_fields'].includes(k))
                  .slice(0, 8)
                  .map(([key, val]) => (
                    <div key={key} className="flex items-start justify-between py-1 border-b border-gray-100 last:border-0 gap-2">
                      <span className="text-[10px] text-gray-500 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="text-[10px] font-semibold text-gray-800 text-right max-w-[100px] truncate">
                        {String(val ?? '—')}
                      </span>
                    </div>
                  ))}
              </div>

              {/* Line Items */}
              {items.length > 0 && (
                <div className="col-span-2 bg-gray-50 rounded-xl p-3 border border-gray-100">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">
                    Line Items ({items.length})
                  </p>
                  <table className="w-full text-[10px]">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-200">
                        <th className="text-left pb-1 font-semibold">Item</th>
                        <th className="text-right pb-1 font-semibold">Qty</th>
                        <th className="text-right pb-1 font-semibold">Unit</th>
                        <th className="text-right pb-1 font-semibold">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item, i) => (
                        <tr key={i} className="border-b border-gray-100 last:border-0">
                          <td className="py-1 text-gray-700 font-medium">{item.name}</td>
                          <td className="py-1 text-right text-gray-500">{item.qty}</td>
                          <td className="py-1 text-right text-gray-500">
                            {item.unit_price?.toLocaleString()}
                          </td>
                          <td className="py-1 text-right font-semibold text-gray-800">
                            {item.total_price?.toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Totals summary */}
            {(struct.total_amount || struct.subtotal) && (
              <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                <p className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-2">Totals</p>
                <div className="grid grid-cols-3 gap-4 text-xs">
                  {struct.subtotal && (
                    <div>
                      <p className="text-gray-500">Subtotal</p>
                      <p className="font-bold text-gray-800">{Number(struct.subtotal).toLocaleString()}</p>
                    </div>
                  )}
                  {struct.tax && (
                    <div>
                      <p className="text-gray-500">Tax</p>
                      <p className="font-bold text-gray-800">{Number(struct.tax).toLocaleString()}</p>
                    </div>
                  )}
                  {struct.total_amount && (
                    <div>
                      <p className="text-blue-600 font-semibold">TOTAL</p>
                      <p className="text-xl font-black text-blue-700">{Number(struct.total_amount).toLocaleString()}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {tab === 'raw' && (
          <pre className="text-xs text-gray-700 font-mono leading-relaxed whitespace-pre-wrap bg-gray-50 p-4 rounded-xl border border-gray-100">
            {result.raw_text || 'No text extracted.'}
          </pre>
        )}

        {tab === 'meta' && (
          <div className="space-y-2 text-xs">
            {[
              ['Model Used', result.model_used],
              ['Token Estimate', `${result.token_estimate} tokens`],
              ['Cached', result.cached ? 'Yes (0 tokens consumed)' : 'No (fresh extraction)'],
              ['Processing Time', result.processing_time ? `${result.processing_time.toFixed(2)}s` : '—'],
              ['Raw Text Length', `${result.raw_text?.length ?? 0} characters`],
              ['Structured Fields', `${Object.keys(struct).length} fields`],
            ].map(([k, v]) => (
              <div key={k} className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="text-gray-500">{k}</span>
                <span className="font-semibold text-gray-800">{v}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
