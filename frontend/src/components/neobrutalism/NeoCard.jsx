import React from 'react';

export const NeoCard = ({
  children,
  title,
  subtitle,
  badge,
  badgeVariant = 'yellow',
  headerColor = null, // e.g. '#ffd731' (Sunburst), '#55db9c' (Mint Pop), '#4da2ff' (Electric Blue), '#e9ccff' (Lavender)
  actions,
  className = '',
  bodyClassName = '',
  shadow = 'md', // sm, md, lg
  onClick,
  hoverLift = false
}) => {
  const shadowStyles = {
    sm: 'shadow-[2px_2px_0px_0px_#000]',
    md: 'shadow-[4px_4px_0px_0px_#000]',
    lg: 'shadow-[6px_6px_0px_0px_#000]'
  };

  return (
    <div
      onClick={onClick}
      className={`
        bg-white border-3 border-black
        ${shadowStyles[shadow] || shadowStyles.md}
        ${hoverLift ? 'transition-all hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_0px_#000]' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      style={{
        borderRadius: '16px',
        borderWidth: '3px'
      }}
    >
      {(title || badge || actions) && (
        <div
          className="px-6 py-4 border-b-3 border-black flex items-center justify-between gap-3 rounded-t-[13px]"
          style={{
            backgroundColor: headerColor || '#FFFFFF',
            borderBottom: '3px solid #000'
          }}
        >
          <div className="flex items-center gap-2.5">
            {badge && (
              <span className="font-mono text-xs font-bold px-2 py-0.5 border-2 border-black bg-white shadow-[1px_1px_0px_0px_#000]" style={{ borderRadius: '4px' }}>
                {badge}
              </span>
            )}
            <div>
              {title && <h3 className="font-extrabold text-base leading-tight">{title}</h3>}
              {subtitle && <p className="text-xs text-neutral-600 font-medium">{subtitle}</p>}
            </div>
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className={`p-6 sm:p-7 ${bodyClassName}`}>
        {children}
      </div>
    </div>
  );
};
