import React, { useState } from 'react'
import { AppLayout } from './components/layout/AppLayout'
import { NavTab } from './components/layout/Sidebar'
import { DashboardPage } from './pages/DashboardPage'
import { FleetPage } from './pages/FleetPage'
import { EditorPage } from './pages/EditorPage'
import { DeploymentsPage } from './pages/DeploymentsPage'
import { ResultsPage } from './pages/ResultsPage'
import { ThreatsPage } from './pages/ThreatsPage'
import { NotFoundPage } from './pages/NotFoundPage'

interface NavContext {
  jobId?: string
  agentId?: string
  type?: string
}

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard')
  const [navContext, setNavContext] = useState<NavContext>({})

  const handleNavigate = (tab: NavTab, context: NavContext = {}) => {
    setNavContext(context)
    setCurrentTab(tab)
  }

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardPage onNavigate={handleNavigate} />
      case 'fleet':
        return <FleetPage onNavigate={handleNavigate} />
      case 'editor':
        return (
          <EditorPage
            initialAgentId={navContext.agentId}
            onNavigate={handleNavigate}
          />
        )
      case 'deployments':
        return (
          <DeploymentsPage
            initialJobId={navContext.jobId}
            onNavigate={handleNavigate}
          />
        )
      case 'results':
        return (
          <ResultsPage
            initialJobId={navContext.jobId}
            initialAgentId={navContext.agentId}
            initialType={navContext.type}
            onNavigate={handleNavigate}
          />
        )
      case 'threats':
        return (
          <ThreatsPage
            initialJobId={navContext.jobId}
            initialAgentId={navContext.agentId}
            onNavigate={handleNavigate}
          />
        )
      default:
        return <NotFoundPage onGoHome={() => handleNavigate('dashboard')} />
    }
  }

  return (
    <AppLayout
      activeTab={currentTab}
      onSelectTab={(tab) => {
        setNavContext({})
        setCurrentTab(tab)
      }}
    >
      {renderContent()}
    </AppLayout>
  )
}

export default App
