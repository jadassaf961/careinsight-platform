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
  sm: 'text-sm py-1.5',
  md: 'text-sm py-2',
  lg: 'text-lg py-2.5',
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
          className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 flex gap-0.5"
        >
          {label}
          {required && <span className="text-risk-high">*</span>}
        </label>
      )}

      <div className="relative">
        {icon && (
          <span className="absolute left-0 top-1/2 -translate-y-1/2 text-ink/40 pointer-events-none flex items-center">
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
            'w-full font-sans bg-transparent text-ink placeholder:text-ink/30',
            'border-0 border-b rounded-none px-0',
            'transition-colors duration-150 outline-none',
            'focus:border-ink',
            'disabled:text-ink/40 disabled:cursor-not-allowed',
            error ? 'border-risk-high' : 'border-hairline',
            icon ? 'pl-7' : '',
            sizeClasses[size],
          ].join(' ')}
        />
      </div>

      {(error || helper) && (
        <p className={`text-xs m-0 ${error ? 'text-risk-high' : 'text-ink/50'}`}>
          {error || helper}
        </p>
      )}
    </div>
  );
}
