import React from 'react';

interface CardProps {
  children: React.ReactNode;
  heading?: string;
  subheading?: string;
  action?: React.ReactNode;
  padding?: 'sm' | 'md' | 'lg';
  elevated?: boolean;
  noPadding?: boolean;
  className?: string;
}

const paddingClasses: Record<string, string> = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export function Card({
  children,
  heading,
  subheading,
  action,
  padding = 'md',
  elevated = false,
  noPadding = false,
  className = '',
}: CardProps) {
  return (
    <div
      className={[
        'bg-white rounded-lg border border-slate-200 overflow-hidden',
        elevated ? 'shadow-md' : 'shadow-sm',
        className,
      ].join(' ')}
    >
      {(heading || action) && (
        <div className={`flex items-start justify-between gap-4 ${paddingClasses[padding]} pb-0`}>
          <div>
            <h3 className="font-sans text-base font-semibold text-slate-800 m-0 leading-snug">
              {heading}
            </h3>
            {subheading && (
              <p className="font-sans text-sm text-slate-500 mt-0.5 m-0">{subheading}</p>
            )}
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      <div className={noPadding ? '' : paddingClasses[padding]}>{children}</div>
    </div>
  );
}
