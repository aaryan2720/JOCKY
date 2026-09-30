import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './Button'

interface ErrorBannerProps {
  title?: string
  message: string
  onRetry?: () => void
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  title = 'Service Communication Error',
  message,
  onRetry,
}) => {
  return (
    <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-md">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-rose-300">{title}</h4>
          <p className="text-xs text-rose-300/80 mt-0.5 leading-relaxed">{message}</p>
        </div>
      </div>
      {onRetry && (
        <Button variant="danger" size="sm" onClick={onRetry} className="shrink-0">
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </Button>
      )}
    </div>
  )
}
