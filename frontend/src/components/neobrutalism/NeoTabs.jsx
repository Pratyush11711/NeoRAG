import React from 'react';

export const NeoTabs = ({
  tabs, // array of { id, label, icon: Icon, badge }
  activeTab,
  onChange,
  className = '',
  activeColor = '#ffd731'
}) => {
  return (
    <div className={`flex flex-wrap gap-2 border-b-2 border-black pb-3 pt-1 px-1 ${className}`}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`
              flex items-center gap-2 px-3.5 py-1.5 font-bold text-xs uppercase tracking-wider
              border-2 border-black transition-all cursor-pointer select-none
              ${isActive ? 'shadow-[3px_3px_0px_0px_#000] translate-y-[-1px]' : 'bg-white hover:bg-neutral-100 shadow-[1px_1px_0px_0px_#000]'}
            `}
            style={{
              backgroundColor: isActive ? activeColor : '#FFFFFF',
              borderRadius: '6px'
            }}
          >
            {Icon && <Icon className="w-3.5 h-3.5" />}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span className={`
                text-[10px] px-1.5 py-0.2 border border-black font-mono
                ${isActive ? 'bg-white' : 'bg-neutral-200'}
              `} style={{ borderRadius: '3px' }}>
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
