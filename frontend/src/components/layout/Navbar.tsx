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
    <header className="h-16 border-b border-slate-800/80 bg-[#0a0d14]/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-wider text-slate-100 font-mono">JOCKY</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-800/50">
              DFIR PLATFORM
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
          <Terminal className="w-4 h-4 text-slate-500" />
          <span>v0.1.0-alpha</span>
        </div>

        <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
          <Badge variant={isConnected ? 'success' : 'danger'}>
            <Activity className="w-3 h-3 animate-pulse" />
            <span>{isConnected ? 'Backend Online' : 'Backend Disconnected'}</span>
          </Badge>
        </div>
      </div>
    </header>
  )
}
