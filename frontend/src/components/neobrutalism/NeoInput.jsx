import React from 'react';

export const NeoInput = ({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  icon: Icon,
  error,
  helperText,
  className = '',
  containerClassName = '',
  required = false,
  ...props
}) => {
  return (
    <div className={`flex flex-col gap-1.5 ${containerClassName}`}>
      {label && (
        <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-1">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-3 text-black pointer-events-none flex items-center justify-center">
            <Icon size={18} className="w-[18px] h-[18px] shrink-0" />
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`
            w-full h-[44px] bg-white text-black font-medium text-sm
            border-2 border-black shadow-[3px_3px_0px_0px_#000]
            focus:outline-none focus:bg-[#FFFEE6] focus:shadow-[4px_4px_0px_0px_#000]
            transition-all
            ${Icon ? 'pl-10 pr-3.5' : 'px-3.5'}
            ${error ? 'border-red-500' : ''}
            ${className}
          `}
          style={{
            borderRadius: '8px',
            fontFamily: 'var(--font-heading)'
          }}
          {...props}
        />
      </div>
      {error ? (
        <span className="text-xs font-bold text-red-600">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-neutral-600 font-medium">{helperText}</span>
      ) : null}
    </div>
  );
};

export const NeoTextarea = ({
  label,
  value,
  onChange,
  placeholder,
  rows = 3,
  error,
  helperText,
  className = '',
  containerClassName = '',
  required = false,
  ...props
}) => {
  return (
    <div className={`flex flex-col gap-1.5 ${containerClassName}`}>
      {label && (
        <label className="text-xs font-bold uppercase tracking-wider text-black flex items-center gap-1">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <textarea
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={rows}
        className={`
          w-full bg-white text-black font-medium text-sm
          border-2 border-black shadow-[3px_3px_0px_0px_#000]
          focus:outline-none focus:bg-[#FFFEE6] focus:shadow-[4px_4px_0px_0px_#000]
          transition-all p-3
          ${error ? 'border-red-500' : ''}
          ${className}
        `}
        style={{
          borderRadius: '6px',
          fontFamily: 'var(--font-heading)'
        }}
        {...props}
      />
      {error ? (
        <span className="text-xs font-bold text-red-600">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-neutral-600 font-medium">{helperText}</span>
      ) : null}
    </div>
  );
};
