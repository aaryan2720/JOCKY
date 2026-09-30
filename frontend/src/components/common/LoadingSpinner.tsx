import React from 'react'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface LoadingSpinnerProps {
  label?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading forensic telemetry...',
  size = 'md',
  className,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn('flex flex-col items-center justify-center py-12 gap-3', className)}
    >
      <Loader2 className={cn('animate-spin text-cyan-400', sizeClasses[size])} />
      {label && <p className="text-xs text-slate-400 font-mono tracking-tight">{label}</p>}
      <span className="sr-only">Loading...</span>
    </div>
  )
}

