'use client'

import { useState, useRef, useEffect } from 'react'
import { ChatMessage } from '@/lib/types'
import { sendChat } from '@/lib/api'
import { Bot, Send, ChevronDown, Loader2, Sparkles, CheckCheck, ReceiptText, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

const MODELS = [
  { id: 'qwen-35b', label: 'Qwen 35B (Reasoning)' },
  { id: 'nemotron-35', label: 'Nemotron 35' },
  { id: 'qwen-35b-vision', label: 'Qwen 35B Vision' },
]

const QUICK_PROMPTS = [
  { label: 'Summarize', icon: Sparkles, prompt: 'Buat ringkasan singkat dokumen ini.' },
  { label: 'Check Total', icon: CheckCheck, prompt: 'Verifikasi apakah total pembayaran sudah benar. Hitung subtotal + pajak - diskon.' },
  { label: 'Extract Entities', icon: ReceiptText, prompt: 'Ekstrak semua nama, tanggal, dan nominal uang dari dokumen ini.' },
  { label: 'Anomaly Check', icon: AlertTriangle, prompt: 'Apakah ada anomali atau ketidaksesuaian pada dokumen ini?' },
]

interface ChatPanelProps {
  activeDoc: string | null
  activePage: number
}

export default function ChatPanel({ activeDoc, activePage }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [model, setModel] = useState(MODELS[0].id)
  const [isLoading, setIsLoading] = useState(false)
  const [showModelMenu, setShowModelMenu] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Reset on doc change
  useEffect(() => {
    setMessages([])
  }, [activeDoc])

  async function submit(text?: string) {
    const userText = text ?? input.trim()
    if (!userText || !activeDoc || isLoading) return
    setInput('')

    const userMsg: ChatMessage = { role: 'user', content: userText, timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    try {
      const res = await sendChat(activeDoc, activePage, [...messages, userMsg], model)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply,
          model: res.model_used,
          timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Terjadi kendala: ${(e as Error).message}`, timestamp: '' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const selectedModel = MODELS.find((m) => m.id === model) ?? MODELS[0]

  return (
    <div className="flex flex-col h-full bg-white border-l border-gray-100">
      {/* Panel header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2 shrink-0">
        <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center">
          <Bot className="w-4 h-4 text-blue-600" />
        </div>
        <div className="flex-1">
          <p className="text-xs font-bold text-gray-900">Subagent Chat</p>
        </div>

        {/* Model selector */}
        <div className="relative">
          <button
            onClick={() => setShowModelMenu(!showModelMenu)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-700 hover:border-gray-300 transition"
          >
            {selectedModel.label}
            <ChevronDown className="w-3 h-3 text-gray-400" />
          </button>
          {showModelMenu && (
            <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-20 min-w-[180px] py-1">
              {MODELS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => { setModel(m.id); setShowModelMenu(false) }}
                  className={cn(
                    'w-full px-3 py-2 text-left text-xs transition hover:bg-gray-50',
                    model === m.id ? 'text-blue-700 font-semibold' : 'text-gray-700',
                  )}
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-[10px] text-emerald-600 font-medium">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="py-4">
            <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
              <p className="text-sm font-bold text-gray-800 mb-1">Selamat datang!</p>
              <p className="text-xs text-gray-600 mb-3">
                Saya asisten subagent dokumen Anda. Tanyakan apa saja mengenai isi dokumen yang sedang dibuka.
              </p>
              <p className="text-[10px] text-gray-400 font-medium mb-1">Anda bisa bertanya tentang:</p>
              <ul className="text-[10px] text-gray-500 space-y-0.5 list-disc pl-3">
                <li>Totals & calculations</li>
                <li>Line items & entities</li>
                <li>Dates, cashier, merchant</li>
                <li>Anomalies or inconsistencies</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            {msg.role === 'assistant' && (
              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center mr-2 mt-0.5 shrink-0">
                <Bot className="w-3.5 h-3.5 text-blue-600" />
              </div>
            )}
            <div className={cn('max-w-[80%] space-y-1')}>
              <div
                className={cn(
                  'rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : 'bg-gray-100 text-gray-800 rounded-bl-sm',
                )}
              >
                {msg.content}
              </div>
              <div className={cn('flex items-center gap-1 text-[10px] text-gray-400', msg.role === 'user' && 'justify-end')}>
                {msg.model && <span className="font-medium">{msg.model}</span>}
                {msg.model && msg.timestamp && <span>·</span>}
                {msg.timestamp && <span>{msg.timestamp}</span>}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
              <Bot className="w-3.5 h-3.5 text-blue-600" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-2.5">
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      {messages.length === 0 && activeDoc && (
        <div className="px-4 pb-2 flex flex-wrap gap-1.5 shrink-0">
          {QUICK_PROMPTS.map(({ label, icon: Icon, prompt }) => (
            <button
              key={label}
              onClick={() => submit(prompt)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-gray-200 text-[10px] font-medium text-gray-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition"
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div className="px-3 pb-3 pt-2 border-t border-gray-100 shrink-0">
        {!activeDoc ? (
          <p className="text-xs text-gray-400 text-center py-2">Select a document to start chatting</p>
        ) : (
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  submit()
                }
              }}
              placeholder="Ask anything about this document…"
              rows={1}
              className="flex-1 resize-none text-xs border border-gray-200 rounded-xl px-3 py-2.5 outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100 transition placeholder:text-gray-400"
              style={{ minHeight: '40px', maxHeight: '100px' }}
            />
            <button
              onClick={() => submit()}
              disabled={!input.trim() || isLoading}
              className="w-9 h-9 shrink-0 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 rounded-xl flex items-center justify-center transition shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 text-white animate-spin" />
              ) : (
                <Send className="w-4 h-4 text-white" />
              )}
            </button>
          </div>
        )}
        <p className="text-[10px] text-gray-300 text-center mt-1.5">⌘ K · Press Enter to send</p>
      </div>
    </div>
  )
}
