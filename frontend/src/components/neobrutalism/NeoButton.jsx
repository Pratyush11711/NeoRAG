import React from 'react';

export const NeoButton = ({
  children,
  onClick,
  variant = 'main', // main, lime, cyan, pink, danger, neutral, dark, ghost
  size = 'md',     // sm, md, lg
  className = '',
  disabled = false,
  type = 'button',
  icon: Icon,
  ...props
}) => {
  const variantStyles = {
    main: 'bg-[#ffd731] text-black hover:bg-[#ebc425]',         // Sunburst
    sunburst: 'bg-[#ffd731] text-black hover:bg-[#ebc425]',     // Sunburst
    lime: 'bg-[#55db9c] text-black hover:bg-[#46c98a]',         // Mint Pop
    mint: 'bg-[#55db9c] text-black hover:bg-[#46c98a]',         // Mint Pop
    cyan: 'bg-[#4da2ff] text-black hover:bg-[#3d91eb]',         // Electric Blue
    electric: 'bg-[#4da2ff] text-black hover:bg-[#3d91eb]',     // Electric Blue
    pink: 'bg-[#e9ccff] text-black hover:bg-[#dac0f2]',         // Lavender
    lavender: 'bg-[#e9ccff] text-black hover:bg-[#dac0f2]',     // Lavender
    danger: 'bg-[#fb4903] text-white hover:bg-[#e03f00]',       // Ember
    ember: 'bg-[#fb4903] text-white hover:bg-[#e03f00]',        // Ember
    violet: 'bg-[#5c4ade] text-white hover:bg-[#4c3bcd]',       // Voltage Violet
    primary: 'bg-black text-white hover:bg-[#222]',             // Carbon
    neutral: 'bg-white text-black hover:bg-[#f3f3f3]',          // Paper White
    mist: 'bg-[#e9e9e9] text-black hover:bg-[#d9d9d9]',         // Soft Mist
    dark: 'bg-black text-white hover:bg-[#222]',                // Carbon
    ghost: 'bg-transparent text-black border-none shadow-none hover:bg-black/5'
  };

  const sizeStyles = {
    sm: 'h-[36px] px-3.5 text-xs font-bold gap-2',
    md: 'h-[44px] px-5 text-sm font-bold gap-2.5',
    lg: 'h-[50px] px-6 text-base font-extrabold gap-3'
  };

  const isGhost = variant === 'ghost';

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center justify-center cursor-pointer select-none transition-all duration-150
        ${isGhost ? '' : 'border-2 border-black shadow-[4px_4px_0px_0px_#000] hover:translate-x-[4px] hover:translate-y-[4px] hover:shadow-none active:translate-x-[4px] active:translate-y-[4px] active:shadow-none'}
        ${disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''}
        ${variantStyles[variant] || variantStyles.main}
        ${sizeStyles[size] || sizeStyles.md}
        ${className}
      `}
      style={{
        borderRadius: '8px',
        fontFamily: 'var(--font-heading)'
      }}
      {...props}
    >
      {Icon && (
        <Icon
          size={size === 'sm' ? 16 : size === 'lg' ? 20 : 18}
          className={`shrink-0 ${size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-5 h-5' : 'w-[18px] h-[18px]'}`}
        />
      )}
      {children}
    </button>
  );
};
