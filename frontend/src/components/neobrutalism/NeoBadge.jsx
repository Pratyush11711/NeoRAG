import React from 'react';

export const NeoBadge = ({
  children,
  variant = 'yellow', // yellow, lime, cyan, pink, purple, danger, dark, neutral, outline
  size = 'md',        // sm, md
  className = '',
  icon: Icon
}) => {
  const variantStyles = {
    yellow: 'bg-[#ffd731] text-black border-black',          // Sunburst
    sunburst: 'bg-[#ffd731] text-black border-black',
    lime: 'bg-[#55db9c] text-black border-black',            // Mint Pop
    mint: 'bg-[#55db9c] text-black border-black',
    cyan: 'bg-[#4da2ff] text-black border-black',            // Electric Blue
    electric: 'bg-[#4da2ff] text-black border-black',
    pink: 'bg-[#e9ccff] text-black border-black',            // Lavender
    lavender: 'bg-[#e9ccff] text-black border-black',
    purple: 'bg-[#5c4ade] text-white border-black',          // Voltage Violet
    violet: 'bg-[#5c4ade] text-white border-black',
    danger: 'bg-[#fb4903] text-white border-black',          // Ember
    ember: 'bg-[#fb4903] text-white border-black',
    dark: 'bg-black text-white border-black',                // Carbon
    carbon: 'bg-black text-white border-black',
    neutral: 'bg-white text-black border-black',             // Paper White
    paper: 'bg-white text-black border-black',
    mist: 'bg-[#e9e9e9] text-black border-black',            // Soft Mist
    sky: 'bg-[#dceeff] text-black border-black',             // Sky Wash
    outline: 'bg-transparent text-black border-black'
  };

  const sizeStyles = {
    sm: 'text-[10px] px-1.5 py-0.5 font-bold',
    md: 'text-xs px-2.5 py-1 font-bold'
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 uppercase tracking-wider border-2 shadow-[2px_2px_0px_0px_#000]
        ${variantStyles[variant] || variantStyles.yellow}
        ${sizeStyles[size] || sizeStyles.md}
        ${className}
      `}
      style={{
        borderRadius: '4px',
        fontFamily: 'var(--font-mono)'
      }}
    >
      {Icon && <Icon className="w-3 h-3" />}
      {children}
    </span>
  );
};
