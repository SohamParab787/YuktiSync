import React from 'react';

export const RiskAlertBanner = ({ alerts = [] }) => {
  if (!alerts || alerts.length === 0) return null;

  const getSeverityStyle = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return {
          wrapper: 'bg-red-50 border-red-300 text-red-900',
          badge: 'bg-red-600 text-white',
          icon: '⚠️ CRITICAL RISK',
        };
      case 'WARNING':
        return {
          wrapper: 'bg-amber-50 border-amber-300 text-amber-900',
          badge: 'bg-amber-600 text-white',
          icon: '⚡ WARNING',
        };
      case 'INFO':
      default:
        return {
          wrapper: 'bg-blue-50 border-blue-300 text-blue-900',
          badge: 'bg-blue-600 text-white',
          icon: 'ℹ️ NOTICE',
        };
    }
  };

  return (
    <div className="space-y-3" role="region" aria-label="Risk and Safety Alerts">
      {alerts.map((alert, idx) => {
        const style = getSeverityStyle(alert.severity);
        return (
          <div
            key={alert.id || idx}
            className={`rounded-xl border p-4 shadow-sm flex flex-col gap-2 ${style.wrapper}`}
          >
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-0.5 rounded text-xs font-black uppercase ${style.badge}`}>
                  {style.icon}
                </span>
                <h4 className="font-bold text-sm sm:text-base">{alert.title}</h4>
              </div>
              {alert.type && (
                <span className="text-xs font-mono uppercase tracking-wider text-slate-500">
                  [{alert.type.replace('_', ' ')}]
                </span>
              )}
            </div>

            <p className="text-sm font-medium leading-relaxed">
              {alert.explanation}
            </p>

            {alert.medications && alert.medications.length > 0 && (
              <div className="flex items-center gap-1.5 flex-wrap text-xs pt-1">
                <span className="font-semibold text-slate-600">Involved Medications:</span>
                {alert.medications.map((m, i) => (
                  <span key={i} className="px-2 py-0.5 bg-white/80 rounded border font-semibold">
                    {m}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
