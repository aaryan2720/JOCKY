import React, { useState } from 'react'
import { AppLayout } from './components/layout/AppLayout'
import { NavTab } from './components/layout/Sidebar'
import { FleetPage } from './pages/FleetPage'
import { EditorPage } from './pages/EditorPage'
import { DeploymentsPage } from './pages/DeploymentsPage'
import { ResultsPage } from './pages/ResultsPage'
import { ThreatsPage } from './pages/ThreatsPage'
import { NotFoundPage } from './pages/NotFoundPage'

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('fleet')

  const renderContent = () => {
    switch (currentTab) {
      case 'fleet':
        return <FleetPage />
      case 'editor':
        return <EditorPage />
      case 'deployments':
        return <DeploymentsPage />
      case 'results':
        return <ResultsPage />
      case 'threats':
        return <ThreatsPage />
      default:
        return <NotFoundPage onGoHome={() => setCurrentTab('fleet')} />
    }
  }

  return (
    <AppLayout activeTab={currentTab} onSelectTab={setCurrentTab}>
      {renderContent()}
    </AppLayout>
  )
}

export default App
