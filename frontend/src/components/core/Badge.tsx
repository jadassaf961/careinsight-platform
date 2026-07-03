import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'danger' | 'warning' | 'navy' | 'outline';
  size?: 'xs' | 'sm' | 'md';
}

const variantStyles: Record<string, React.CSSProperties> = {
  default: { background: '#f5f5f3', color: '#565656', borderColor: '#e5e5e5' },
  primary: { background: 'transparent', color: '#0f0f0f', borderColor: '#0f0f0f' },
  success: { background: '#ECFDF3', color: '#067647', borderColor: '#ABEFC6' },
  danger:  { background: '#FEF3F2', color: '#B42318', borderColor: '#FECDCA' },
  warning: { background: '#FFFAEB', color: '#B54708', borderColor: '#FEDF89' },
  navy:    { background: '#0f0f0f', color: '#ffffff', borderColor: 'transparent' },
  outline: { background: 'transparent', color: '#565656', borderColor: '#e5e5e5' },
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
