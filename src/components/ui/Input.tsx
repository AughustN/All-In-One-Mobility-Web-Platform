import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({ label, icon, className, ...props }) => {
  return (
    <div className="space-y-1.5 w-full">
      <label className="text-xs font-medium text-zinc-400 tracking-wide uppercase ml-1">
        {label}
      </label>
      <div className="relative group">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-white transition-colors duration-200">
            {icon}
          </div>
        )}
        <input
          {...props}
          className={`w-full bg-zinc-900/50 border border-zinc-800 text-white text-sm rounded-lg focus:ring-1 focus:ring-white focus:border-white block p-3 ${icon ? 'pl-10' : ''} placeholder-zinc-600 transition-all duration-200 outline-none hover:bg-zinc-900 ${className}`}
        />
      </div>
    </div>
  );
};