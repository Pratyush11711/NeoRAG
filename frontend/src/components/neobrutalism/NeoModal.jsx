import React, { useEffect } from 'react';

export const NeoModal = ({
  isOpen,
  onClose,
  title,
  children,
  headerColor = '#ffd731',
  maxWidth = 'max-w-2xl'
}) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div
        className={`w-full ${maxWidth} bg-white border-4 border-black shadow-[8px_8px_0px_0px_#000] overflow-hidden`}
        style={{ borderRadius: '8px' }}
      >
        {/* Header */}
        <div
          className="px-5 py-3 border-b-4 border-black flex items-center justify-between"
          style={{ backgroundColor: headerColor }}
        >
          <h3 className="font-extrabold text-base uppercase tracking-wider text-black">
            {title}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="w-7 h-7 border-2 border-black bg-white shadow-[2px_2px_0px_0px_#000] active:translate-x-[1px] active:translate-y-[1px] font-bold text-xs flex items-center justify-center hover:bg-neutral-200 cursor-pointer"
            style={{ borderRadius: '4px' }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[80vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};
