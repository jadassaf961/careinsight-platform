import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'danger' | 'warning' | 'navy' | 'outline';
  size?: 'xs' | 'sm' | 'md';
}

const variantStyles: Record<string, React.CSSProperties> = {
  default: { background: '#f1f5f9', color: '#475569', borderColor: '#e2e8f0' },
  primary: { background: '#e0f2fe', color: '#075985', borderColor: '#bae6fd' },
  success: { background: '#dcfce7', color: '#16a34a', borderColor: '#86efac' },
  danger:  { background: '#fee2e2', color: '#dc2626', borderColor: '#fca5a5' },
  warning: { background: '#fef3c7', color: '#d97706', borderColor: '#fcd34d' },
  navy:    { background: '#1e3a5f', color: '#ffffff', borderColor: 'transparent' },
  outline: { background: 'transparent', color: '#64748b', borderColor: '#94a3b8' },
};

const sizeClasses: Record<string, string> = {
  xs: 'text-[0.65rem] px-[0.45rem] py-[0.1rem]',
  sm: 'text-xs px-2.5 py-0.5',
  md: 'text-sm px-3 py-1',
};

export function Badge({ children, variant = 'default', size = 'sm' }: BadgeProps) {
  return (
    <span
      className={[
        'inline-flex items-center',
        'font-sans font-semibold',
        'rounded-full border',
        'whitespace-nowrap tracking-[0.03em]',
        sizeClasses[size],
      ].join(' ')}
      style={variantStyles[variant]}
    >
      {children}
    </span>
  );
}
