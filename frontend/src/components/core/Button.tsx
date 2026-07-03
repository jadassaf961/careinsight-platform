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
  primary:   'bg-ink text-paper border-transparent hover:bg-ink/85',
  secondary: 'bg-paper text-ink border-hairline hover:bg-tint',
  ghost:     'bg-transparent text-ink/70 border-transparent hover:text-ink hover:bg-tint',
  danger:    'bg-risk-high text-white border-transparent hover:opacity-90',
};

const sizeClasses: Record<string, string> = {
  sm: 'text-xs px-3.5 py-1.5',
  md: 'text-sm px-5 py-2',
  lg: 'text-sm px-6 py-2.5',
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
        'font-semibold leading-none whitespace-nowrap',
        'rounded-full border',
        'lowercase font-display',
        'transition-all duration-150',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-ink/15',
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
