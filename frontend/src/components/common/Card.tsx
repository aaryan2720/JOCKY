import React from 'react'
import { cn } from '../../lib/utils'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
  title?: string
  subtitle?: string
  action?: React.ReactNode
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  title,
  subtitle,
  action,
  ...props
}) => {
  return (
    <div
      className={cn(
        'bg-[#0d1322]/90 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-lg transition-all duration-200 hover:border-slate-700/90',
        className
      )}
      {...props}
    >
      {(title || action) && (
        <div className="flex items-center justify-between pb-3.5 mb-4 border-b border-slate-800/80">
          <div>
            {title && <h3 className="text-sm font-semibold tracking-tight text-slate-100 font-mono">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}

