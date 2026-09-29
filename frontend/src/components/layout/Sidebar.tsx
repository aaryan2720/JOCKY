import React from 'react'
import {
  Server,
  Code2,
  Rocket,
  Layers,
  AlertTriangle,
  FolderGit2,
} from 'lucide-react'

export type NavTab = 'fleet' | 'editor' | 'deployments' | 'results' | 'threats'

interface SidebarProps {
  activeTab: NavTab
  onSelectTab: (tab: NavTab) => void
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: 'fleet', label: 'Fleet Overview', icon: <Server className="w-4 h-4" /> },
    { id: 'editor', label: 'JOCKY Editor', icon: <Code2 className="w-4 h-4" /> },
    { id: 'deployments', label: 'Deployments', icon: <Rocket className="w-4 h-4" /> },
    { id: 'results', label: 'Artifact Results', icon: <Layers className="w-4 h-4" /> },
    { id: 'threats', label: 'Threat Detections', icon: <AlertTriangle className="w-4 h-4" /> },
  ]

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-[#0a0d14]/60 backdrop-blur-md flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 px-3 mb-2 font-mono">
            Navigation
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

      <div className="p-3 bg-[#111726]/60 border border-slate-800/60 rounded-xl text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-2 text-slate-300 font-medium">
          <FolderGit2 className="w-4 h-4 text-cyan-400" />
          <span>Hackathon Scaffold</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          Initial monorepo baseline active. Core collectors and interpreter modules will plug in here.
        </p>
      </div>
    </aside>
  )
}
