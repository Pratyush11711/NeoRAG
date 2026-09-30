import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export const NeoAccordion = ({
  title,
  subtitle,
  children,
  badge,
  badgeVariant = 'yellow',
  defaultOpen = false,
  className = '',
  headerColor = '#FFFFFF'
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div
      className={`border-2 border-black bg-white shadow-[3px_3px_0px_0px_#000] overflow-hidden ${className}`}
      style={{ borderRadius: '6px' }}
    >
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between gap-3 text-left transition-colors cursor-pointer select-none"
        style={{ backgroundColor: headerColor }}
      >
        <div className="flex items-center gap-2.5">
          {badge && (
            <span className="font-mono text-[10px] uppercase font-bold px-1.5 py-0.5 border border-black bg-white shadow-[1px_1px_0px_0px_#000]" style={{ borderRadius: '3px' }}>
              {badge}
            </span>
          )}
          <div>
            <h4 className="font-bold text-sm leading-tight text-black">{title}</h4>
            {subtitle && <p className="text-xs text-neutral-600 font-medium">{subtitle}</p>}
          </div>
        </div>
        <div
          className={`
            w-6 h-6 border-2 border-black flex items-center justify-center bg-white shadow-[1px_1px_0px_0px_#000] transition-transform duration-200
            ${isOpen ? 'rotate-180 bg-[#ffd731]' : ''}
          `}
          style={{ borderRadius: '4px' }}
        >
          <ChevronDown className="w-4 h-4 text-black" />
        </div>
      </button>

      {isOpen && (
        <div className="p-4 border-t-2 border-black bg-white animate-in fade-in duration-150">
          {children}
        </div>
      )}
    </div>
  );
};
