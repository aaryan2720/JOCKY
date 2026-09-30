import React from 'react'
import {
  LayoutDashboard,
  Server,
  Code2,
  Activity,
  Layers,
  AlertTriangle,
  ShieldCheck,
} from 'lucide-react'

export type NavTab = 'dashboard' | 'fleet' | 'editor' | 'deployments' | 'results' | 'threats'

interface SidebarProps {
  activeTab: NavTab
  onSelectTab: (tab: NavTab) => void
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    { id: 'fleet', label: 'Fleet Agents', icon: <Server className="w-4 h-4" /> },
    { id: 'editor', label: 'JOCKY Editor', icon: <Code2 className="w-4 h-4" /> },
    { id: 'deployments', label: 'Jobs & Live Feed', icon: <Activity className="w-4 h-4" /> },
    { id: 'results', label: 'Forensic Artifacts', icon: <Layers className="w-4 h-4" /> },
    { id: 'threats', label: 'Threat Detections', icon: <AlertTriangle className="w-4 h-4" /> },
  ]

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-[#0a0d14]/60 backdrop-blur-md flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 px-3 mb-2 font-mono">
            Forensic Operations
          </p>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-950/80 to-blue-950/40 text-cyan-400 border border-cyan-800/50 shadow-sm shadow-cyan-950/50'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={isActive ? 'text-cyan-400' : 'text-slate-500'}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </div>
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      <div className="p-3.5 bg-[#111726]/60 border border-slate-800/60 rounded-xl text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-2 text-cyan-400 font-medium">
          <ShieldCheck className="w-4 h-4" />
          <span>Defensive DFIR Platform</span>
        </div>
        <p className="text-[11px] text-slate-400/80 leading-relaxed">
          Read-only forensic collection, deterministic rule evaluation, and live artifact streaming.
        </p>
        <div className="pt-1 flex items-center gap-1.5 text-[10px] text-emerald-400 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>6 Active Real Collectors</span>
        </div>
      </div>
    </aside>
  )
}

