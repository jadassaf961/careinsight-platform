import React from 'react';

interface InputProps {
  label?: string;
  id?: string;
  type?: 'text' | 'email' | 'password' | 'search' | 'number' | 'tel';
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  error?: string;
  helper?: string;
  icon?: React.ReactNode;
  required?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  autoComplete?: string;
}

const sizeClasses: Record<string, string> = {
  sm: 'text-sm py-1.5 px-2.5',
  md: 'text-sm py-2 px-3',
  lg: 'text-base py-2.5 px-4',
};

export function Input({
  label,
  id,
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  error,
  helper,
  icon,
  required = false,
  size = 'md',
  className = '',
  autoComplete,
}: InputProps) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-slate-700 flex gap-0.5"
        >
          {label}
          {required && <span className="text-risk-high">*</span>}
        </label>
      )}

      <div className="relative">
        {icon && (
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none flex items-center">
            {icon}
          </span>
        )}
        <input
          id={inputId}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          autoComplete={autoComplete}
          className={[
            'w-full font-sans rounded-md border bg-white text-slate-800',
            'transition-all duration-150 outline-none',
            'focus:shadow-focus focus:border-brand-600',
            'disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed',
            error ? 'border-risk-high focus:shadow-focus-danger' : 'border-slate-300',
            icon ? 'pl-9' : '',
            sizeClasses[size],
          ].join(' ')}
        />
      </div>

      {(error || helper) && (
        <p className={`text-xs m-0 ${error ? 'text-risk-high' : 'text-slate-500'}`}>
          {error || helper}
        </p>
      )}
    </div>
  );
}
