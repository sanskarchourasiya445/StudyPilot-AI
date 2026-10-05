import React, { forwardRef } from 'react';

export const Input = forwardRef(function Input(
  { label, error, helperText, icon: Icon, className = '', containerClassName = '', type = 'text', ...props },
  ref
) {
  return (
    <div className={`flex flex-col gap-1.5 w-full ${containerClassName}`}>
      {label && (
        <label className="text-xs font-semibold uppercase tracking-wider text-[#9ca8ba]">
          {label}
        </label>
      )}
      <div className="relative flex items-center w-full">
        {Icon && (
          <div className="absolute left-3.5 text-[#667085] pointer-events-none">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <input
          ref={ref}
          type={type}
          className={`w-full rounded-xl border text-sm transition-all duration-150 py-2.5 px-3.5
            ${Icon ? 'pl-10' : 'pl-3.5'}
            bg-[#0a0f18] text-[#f5f7fa] placeholder-[#667085]
            ${
              error
                ? 'border-red-500/70 focus:border-red-500 focus:ring-1 focus:ring-red-500/30'
                : 'border-white/[0.08] focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 hover:border-white/[0.15]'
            }
            focus:outline-none ${className}`}
          {...props}
        />
      </div>
      {error ? (
        <span className="text-xs font-medium text-red-400">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-[#667085]">{helperText}</span>
      ) : null}
    </div>
  );
});
