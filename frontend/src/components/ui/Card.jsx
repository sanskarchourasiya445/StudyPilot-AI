import React from 'react';

export function Card({ children, className = '', hoverable = false, ...props }) {
  return (
    <div
      className={`bg-[#0d1420] border border-white/[0.07] rounded-2xl p-5 shadow-xs transition-all duration-200 ${
        hoverable ? 'hover:border-blue-500/40 hover:bg-[#101827] cursor-pointer' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return <div className={`mb-4 flex items-center justify-between gap-4 ${className}`}>{children}</div>;
}

export function CardTitle({ children, className = '' }) {
  return <h3 className={`text-base font-bold text-[#f5f7fa] tracking-tight ${className}`}>{children}</h3>;
}

export function CardDescription({ children, className = '' }) {
  return <p className={`text-xs text-[#9ca8ba] mt-1 ${className}`}>{children}</p>;
}

export function CardContent({ children, className = '' }) {
  return <div className={className}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return <div className={`mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between gap-3 ${className}`}>{children}</div>;
}
