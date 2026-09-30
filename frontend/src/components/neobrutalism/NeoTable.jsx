import React from 'react';

export const NeoTable = ({
  headers, // array of strings or { label, align, width }
  children,
  className = '',
  headerBg = '#ffd731'
}) => {
  return (
    <div
      className={`border-3 border-black overflow-x-auto shadow-[4px_4px_0px_0px_#000] bg-white ${className}`}
      style={{ borderRadius: '14px', borderWidth: '3px' }}
    >
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr style={{ backgroundColor: headerBg, borderBottom: '3px solid #000' }}>
            {headers.map((h, i) => {
              const label = typeof h === 'object' ? h.label : h;
              const align = typeof h === 'object' && h.align ? h.align : 'left';
              return (
                <th
                  key={i}
                  className={`p-4 font-extrabold uppercase tracking-wider text-black border-r-2 border-black last:border-r-0 text-${align}`}
                  style={{ fontFamily: 'var(--font-mono)' }}
                >
                  {label}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y-2 divide-black font-medium text-neutral-800">
          {children}
        </tbody>
      </table>
    </div>
  );
};
