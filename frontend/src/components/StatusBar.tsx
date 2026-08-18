'use client'

import { SafetyStatus } from '@/lib/types'
import { Shield, Activity, Clock, Zap, CheckCircle, AlertCircle } from 'lucide-react'

interface StatusBarProps {
  status: SafetyStatus | null
  activePdf: string | null
  activePageCount: number
}

export default function StatusBar({ status, activePdf, activePageCount }: StatusBarProps) {
  const isReady = status?.ready ?? false
  const cooldown = status?.cooldown_remaining ?? 0
  const active = status?.concurrent_active ?? 0
  const dailyUsed = status?.daily_calls_used ?? 0
  const dailyLimit = status?.daily_calls_limit ?? 25

  return (
    <header className="h-14 border-b border-gray-100 bg-white flex items-center px-4 gap-4 shrink-0 z-10 shadow-sm">
      {/* Brand */}
      <div className="flex items-center gap-2.5 min-w-[200px]">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-bold text-gray-900 tracking-tight">OCH-Subagent</p>
          <p className="text-[10px] text-gray-400 font-medium">Document Intelligence</p>
        </div>
      </div>

      {/* Active Document Pill */}
      {activePdf && (
        <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-full px-3 py-1">
          <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
          <span className="text-xs font-medium text-gray-700 max-w-[180px] truncate">{activePdf}</span>
          <span className="text-[10px] text-gray-400">{activePageCount} page{activePageCount !== 1 ? 's' : ''}</span>
        </div>
      )}

      <div className="flex-1" />

      {/* Status indicators */}
      <div className="flex items-center gap-3">
        {/* OCR Ready */}
        <div className="flex items-center gap-1.5">
          {isReady && cooldown === 0 ? (
            <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
          ) : (
            <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
          )}
          <span className={`text-xs font-medium ${isReady && cooldown === 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
            {cooldown > 0 ? `${Math.ceil(cooldown)}s cooldown` : 'OCR Ready'}
          </span>
        </div>

        <div className="w-px h-4 bg-gray-200" />

        {/* Concurrent Active */}
        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs text-gray-500">{active}/1 Active</span>
        </div>

        <div className="w-px h-4 bg-gray-200" />

        {/* Daily Calls */}
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs text-gray-500">{dailyUsed}/{dailyLimit} Calls</span>
        </div>

        <div className="w-px h-4 bg-gray-200" />

        {/* Shield */}
        <div className="flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-blue-500" />
          <span className="text-xs text-blue-600 font-medium">Shield ON</span>
        </div>
      </div>
    </header>
  )
}
