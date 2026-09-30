import React from 'react'
import { DeploymentList } from '../features/deployment/DeploymentList'
import { NavTab } from '../components/layout/Sidebar'

interface DeploymentsPageProps {
  initialJobId?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

export const DeploymentsPage: React.FC<DeploymentsPageProps> = ({ initialJobId, onNavigate }) => {
  return <DeploymentList initialJobId={initialJobId} onNavigate={onNavigate} />
}
