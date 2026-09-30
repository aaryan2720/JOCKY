import React from 'react'
import { ThreatAlertList } from '../features/threats/ThreatAlertList'
import { NavTab } from '../components/layout/Sidebar'

interface ThreatsPageProps {
  initialJobId?: string
  initialAgentId?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

export const ThreatsPage: React.FC<ThreatsPageProps> = ({
  initialJobId,
  initialAgentId,
  onNavigate,
}) => {
  return (
    <ThreatAlertList
      initialJobId={initialJobId}
      initialAgentId={initialAgentId}
      onNavigate={onNavigate}
    />
  )
}
