import React from 'react'
import { FleetTable } from '../features/fleet/FleetTable'
import { NavTab } from '../components/layout/Sidebar'

interface FleetPageProps {
  onNavigate?: (tab: NavTab, context?: { agentId?: string; jobId?: string }) => void
}

export const FleetPage: React.FC<FleetPageProps> = ({ onNavigate }) => {
  return <FleetTable onNavigate={onNavigate} />
}
