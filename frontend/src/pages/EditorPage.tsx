import React from 'react'
import { ScriptEditor } from '../features/editor/ScriptEditor'
import { NavTab } from '../components/layout/Sidebar'

interface EditorPageProps {
  initialAgentId?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

export const EditorPage: React.FC<EditorPageProps> = ({ initialAgentId, onNavigate }) => {
  return <ScriptEditor initialAgentId={initialAgentId} onNavigate={onNavigate} />
}
