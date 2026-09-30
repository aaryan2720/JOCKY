import React from 'react'
import { cn } from '../../lib/utils'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline'
  className?: string
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  className,
}) => {
  const variantStyles = {
    default: 'bg-slate-800/90 text-slate-300 border-slate-700/80',
    success: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60 shadow-sm shadow-emerald-950/30',
    warning: 'bg-amber-950/80 text-amber-300 border-amber-700/60 shadow-sm shadow-amber-950/30',
    danger: 'bg-rose-950/80 text-rose-300 border-rose-700/60 shadow-sm shadow-rose-950/30',
    info: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60 shadow-sm shadow-cyan-950/30',
    outline: 'bg-transparent text-slate-400 border-slate-700 hover:border-slate-600',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border font-mono tracking-tight transition-colors',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

