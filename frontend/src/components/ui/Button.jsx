import React from 'react';
import { Loader2 } from 'lucide-react';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  className = '',
  icon: Icon,
  type = 'button',
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#07090d] disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none cursor-pointer select-none';

  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white shadow-sm shadow-blue-600/20 focus:ring-blue-500',
    secondary: 'bg-[#101827] hover:bg-[#152033] border border-white/[0.08] text-[#f5f7fa] hover:border-white/[0.15] focus:ring-slate-500',
    outline: 'border border-white/[0.12] bg-transparent hover:bg-white/[0.05] text-[#f5f7fa] focus:ring-blue-500',
    ghost: 'bg-transparent hover:bg-white/[0.05] text-[#9ca8ba] hover:text-[#f5f7fa] focus:ring-slate-600',
    destructive: 'bg-red-600/90 hover:bg-red-600 active:bg-red-700 text-white shadow-sm focus:ring-red-500',
    study: 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-sm focus:ring-indigo-500',
  };

  const sizes = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2 gap-2',
    lg: 'text-base px-5 py-2.5 gap-2.5',
    icon: 'p-2 text-[#9ca8ba] hover:text-[#f5f7fa] hover:bg-white/[0.05]',
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      className={`${baseStyles} ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : Icon ? (
        <Icon className="w-4 h-4 shrink-0" />
      ) : null}
      {children}
    </button>
  );
}
