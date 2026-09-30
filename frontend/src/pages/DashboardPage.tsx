import React from 'react'
import { DashboardOverview } from '../features/dashboard/DashboardOverview'
import { NavTab } from '../components/layout/Sidebar'

interface DashboardPageProps {
  onNavigate: (tab: NavTab, context?: { jobId?: string; agentId?: string; type?: string }) => void
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  return <DashboardOverview onNavigate={onNavigate} />
}
