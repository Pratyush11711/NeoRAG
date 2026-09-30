import React from 'react';
import { ChevronDown } from 'lucide-react';

export const NeoSelect = ({
  label,
  value,
  onChange,
  options, // array of { value, label } or strings
  helperText,
  className = '',
  containerClassName = ''
}) => {
  return (
    <div className={`flex flex-col gap-1.5 ${containerClassName}`}>
      {label && (
        <label className="text-xs font-bold uppercase tracking-wider text-black">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          value={value}
          onChange={onChange}
          className={`
            w-full h-[44px] appearance-none bg-white text-black font-semibold text-sm
            border-2 border-black shadow-[3px_3px_0px_0px_#000]
            focus:outline-none focus:bg-[#FFFEE6]
            px-3.5 pr-10 cursor-pointer transition-all ${className}
          `}
          style={{
            borderRadius: '8px',
            fontFamily: 'var(--font-heading)'
          }}
        >
          {options.map((opt) => {
            const val = typeof opt === 'object' ? opt.value : opt;
            const lbl = typeof opt === 'object' ? opt.label : opt;
            return (
              <option key={val} value={val} className="font-medium">
                {lbl}
              </option>
            );
          })}
        </select>
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none flex items-center justify-center">
          <ChevronDown size={18} className="w-[18px] h-[18px] text-black shrink-0" />
        </div>
      </div>
      {helperText && (
        <span className="text-[11px] text-neutral-600 font-medium">{helperText}</span>
      )}
    </div>
  );
};

export const NeoSlider = ({
  label,
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.05,
  helperText,
  formatValue = (v) => v,
  className = ''
}) => {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <div className="flex items-center justify-between">
        {label && (
          <label className="text-xs font-bold uppercase tracking-wider text-black">
            {label}
          </label>
        )}
        <span className="text-xs font-mono font-bold px-2 py-0.5 border border-black bg-[#ffd731] shadow-[1px_1px_0px_0px_#000]" style={{ borderRadius: '3px' }}>
          {formatValue(value)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-3 bg-neutral-200 border-2 border-black rounded-lg appearance-none cursor-pointer accent-[#ffd731]"
      />
      {helperText && (
        <span className="text-[11px] text-neutral-600 font-medium">{helperText}</span>
      )}
    </div>
  );
};
