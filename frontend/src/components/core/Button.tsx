import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  icon?: React.ReactNode;
  className?: string;
}

const variantClasses: Record<string, string> = {
  primary:   'bg-brand-600 text-white border-transparent hover:bg-brand-700 active:bg-brand-800',
  secondary: 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50',
  ghost:     'bg-transparent text-brand-600 border-transparent hover:bg-slate-100',
  danger:    'bg-risk-high text-white border-transparent hover:opacity-90',
};

const sizeClasses: Record<string, string> = {
  sm: 'text-[0.7rem] px-2.5 py-1',
  md: 'text-[0.72rem] px-4 py-2',
  lg: 'text-sm px-5 py-2.5',
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  onClick,
  type = 'button',
  icon,
  className = '',
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={disabled || loading ? undefined : onClick}
      className={[
        'inline-flex items-center justify-center gap-1.5',
        'font-sans font-medium leading-none whitespace-nowrap',
        'rounded-md border',
        'uppercase tracking-btn',
        'transition-all duration-150',
        'focus:outline-none focus:shadow-focus',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        fullWidth ? 'w-full' : '',
        className,
      ].join(' ')}
    >
      {loading ? (
        <span className="opacity-70">…</span>
      ) : (
        <>
          {icon && <span className="leading-none flex-shrink-0">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
}
