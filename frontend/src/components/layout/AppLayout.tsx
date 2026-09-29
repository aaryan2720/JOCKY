import React from 'react'
import { Navbar } from './Navbar'
import { Sidebar, NavTab } from './Sidebar'

interface AppLayoutProps {
  children: React.ReactNode
  activeTab: NavTab
  onSelectTab: (tab: NavTab) => void
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  activeTab,
  onSelectTab,
}) => {
  return (
    <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar activeTab={activeTab} onSelectTab={onSelectTab} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 max-w-7xl">
          {children}
        </main>
      </div>
    </div>
  )
}
