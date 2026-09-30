import React from 'react'
import { Inbox } from 'lucide-react'
import { Card } from './Card'
import { Button } from './Button'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <Card className="py-12 text-center border-dashed border-slate-800 bg-[#0a0f1d]/50">
      <div className="flex flex-col items-center justify-center max-w-sm mx-auto space-y-3">
        <div className="w-12 h-12 rounded-xl bg-slate-800/50 border border-slate-700/60 flex items-center justify-center text-slate-400">
          {icon || <Inbox className="w-6 h-6 text-slate-500" />}
        </div>
        <h3 className="text-sm font-semibold text-slate-200 font-mono tracking-tight">{title}</h3>
        <p className="text-xs text-slate-400 leading-relaxed">{description}</p>
        {actionLabel && onAction && (
          <Button variant="outline" size="sm" onClick={onAction} className="mt-2 text-cyan-400 border-cyan-800/60 hover:bg-cyan-950/40">
            {actionLabel}
          </Button>
        )}
      </div>
    </Card>
  )
}

