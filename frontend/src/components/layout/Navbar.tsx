import React, { useEffect, useState } from 'react'
import { Shield, Activity, Terminal } from 'lucide-react'
import { fetchHealth } from '../../api/health'
import { Badge } from '../common/Badge'

export const Navbar: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    fetchHealth()
      .then(() => {
        setIsConnected(true)
      })
      .catch(() => {
        setIsConnected(false)
      })
  }, [])

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#090d16]/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-600 to-blue-700 flex items-center justify-center shadow-md shadow-cyan-950/50 border border-cyan-500/30">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-wider text-slate-100 font-mono">JOCKY</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/70 text-cyan-300 border border-cyan-800/60 font-semibold tracking-wide">
              DFIR PLATFORM
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 font-mono">
          <Terminal className="w-3.5 h-3.5 text-slate-500" />
          <span>v0.1.0 (MVP)</span>
        </div>

        <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
          <Badge variant={isConnected ? 'success' : 'danger'}>
            <Activity className={`w-3 h-3 ${isConnected ? 'animate-pulse text-emerald-400' : 'text-rose-400'}`} />
            <span>{isConnected ? 'Backend Connected' : 'Backend Offline'}</span>
          </Badge>
        </div>
      </div>
    </header>
  )
}

