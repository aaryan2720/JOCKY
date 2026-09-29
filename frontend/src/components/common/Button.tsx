import React from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className,
  ...props
}) => {
  const variantStyles = {
    primary:
      'bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/20 active:scale-[0.98]',
    secondary:
      'bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700 active:scale-[0.98]',
    outline:
      'bg-transparent text-slate-300 border border-slate-700 hover:bg-slate-800/60 hover:text-white',
    danger:
      'bg-rose-600 text-white hover:bg-rose-500 shadow-lg shadow-rose-600/20 active:scale-[0.98]',
    ghost:
      'bg-transparent text-slate-400 hover:text-slate-100 hover:bg-slate-800/40',
  }

  const sizeStyles = {
    sm: 'px-2.5 py-1 text-xs rounded-md',
    md: 'px-3.5 py-2 text-sm rounded-lg',
    lg: 'px-5 py-2.5 text-base rounded-lg',
  }

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 disabled:opacity-50 disabled:cursor-not-allowed',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
