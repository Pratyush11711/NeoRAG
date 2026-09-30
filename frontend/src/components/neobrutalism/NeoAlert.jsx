import React from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

export const NeoAlert = ({
  children,
  title,
  type = 'info', // info, success, warning, error
  className = '',
  onClose
}) => {
  const configs = {
    info: {
      bg: 'bg-[#4da2ff]', // Electric Blue
      icon: Info,
      defaultTitle: 'Information'
    },
    success: {
      bg: 'bg-[#55db9c]', // Mint Pop
      icon: CheckCircle,
      defaultTitle: 'Success'
    },
    warning: {
      bg: 'bg-[#ffd731]', // Sunburst
      icon: AlertTriangle,
      defaultTitle: 'Notice'
    },
    error: {
      bg: 'bg-[#fb4903] text-white', // Ember
      icon: AlertCircle,
      defaultTitle: 'Error'
    }
  };

  const cfg = configs[type] || configs.info;
  const Icon = cfg.icon;

  return (
    <div
      className={`
        border-2 border-black p-3.5 shadow-[3px_3px_0px_0px_#000] flex items-start gap-3
        ${cfg.bg} text-black ${className}
      `}
      style={{ borderRadius: '6px' }}
    >
      <div className="p-1 border border-black bg-white shadow-[1px_1px_0px_0px_#000] shrink-0" style={{ borderRadius: '4px' }}>
        <Icon className="w-4 h-4 text-black" />
      </div>
      <div className="flex-1 text-xs leading-relaxed">
        {title && <h5 className="font-extrabold text-sm mb-0.5">{title || cfg.defaultTitle}</h5>}
        <div className="font-medium">{children}</div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="text-black font-mono font-bold text-sm hover:scale-110 cursor-pointer ml-1"
        >
          [✕]
        </button>
      )}
    </div>
  );
};
