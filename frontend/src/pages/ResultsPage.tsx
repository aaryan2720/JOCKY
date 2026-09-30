import React from 'react'
import { ArtifactViewer } from '../features/results/ArtifactViewer'
import { NavTab } from '../components/layout/Sidebar'

interface ResultsPageProps {
  initialJobId?: string
  initialAgentId?: string
  initialType?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

export const ResultsPage: React.FC<ResultsPageProps> = ({
  initialJobId,
  initialAgentId,
  initialType,
  onNavigate,
}) => {
  return (
    <ArtifactViewer
      initialJobId={initialJobId}
      initialAgentId={initialAgentId}
      initialType={initialType}
      onNavigate={onNavigate}
    />
  )
}
