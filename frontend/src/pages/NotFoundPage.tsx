import React from 'react'
import { AlertCircle } from 'lucide-react'
import { Button } from '../components/common/Button'

interface NotFoundPageProps {
  onGoHome: () => void
}

export const NotFoundPage: React.FC<NotFoundPageProps> = ({ onGoHome }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h2 className="text-2xl font-bold text-slate-100">Page Not Found</h2>
      <p className="text-sm text-slate-400 max-w-sm">
        The requested view does not exist in the JOCKY dashboard console.
      </p>
      <Button variant="primary" onClick={onGoHome}>
        Return to Fleet Overview
      </Button>
    </div>
  )
}
