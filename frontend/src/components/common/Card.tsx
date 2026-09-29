import React from 'react'
import { cn } from '../../lib/utils'

interface CardProps {
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
}) => {
  return (
    <div
      className={cn(
        'bg-[#111726]/80 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 shadow-xl transition-all duration-200 hover:border-slate-700/80',
        className
      )}
    >
      {(title || action) && (
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800/60">
          <div>
            {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}
