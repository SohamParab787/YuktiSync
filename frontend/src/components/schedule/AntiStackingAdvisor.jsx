import React from 'react';

export const AntiStackingAdvisor = ({ advice, onClose }) => {
  if (!advice) return null;

  const {
    status = 'SAFE TO TAKE',
    recommendation,
    hours_until_next_dose,
    next_scheduled_time,
    stacking_risk_detected = false,
    disclaimer = 'Medication decisions should follow prescribed instructions or professional guidance. Never automatically change your prescribed dosage.'
  } = advice;

  const getStyle = (s) => {
    switch (s) {
      case 'SAFE TO TAKE':
        return {
          bg: 'bg-emerald-50 border-emerald-300 text-emerald-950',
          badge: 'bg-emerald-600 text-white',
          icon: '🛡️'
        };
      case 'WAIT / SKIP':
        return {
          bg: 'bg-amber-50 border-amber-300 text-amber-950',
          badge: 'bg-amber-600 text-white',
          icon: '⚠️'
        };
      case 'CONSULT PROFESSIONAL':
      default:
        return {
          bg: 'bg-rose-50 border-rose-300 text-rose-950',
          badge: 'bg-rose-600 text-white',
          icon: '🚨'
        };
    }
  };

  const style = getStyle(status);

  return (
    <div className={`rounded-2xl border-2 p-5 shadow-sm space-y-3 ${style.bg}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{style.icon}</span>
          <span className={`px-2.5 py-1 rounded-full text-xs font-black tracking-wide uppercase ${style.badge}`}>
            {status}
          </span>
          <h4 className="font-bold text-sm sm:text-base">Anti-Stacking & Missed-Dose Safety</h4>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-slate-600 px-2 py-1 rounded"
          >
            ✕ Close
          </button>
        )}
      </div>

      <p className="text-sm font-medium leading-relaxed">
        {recommendation}
      </p>

      {hours_until_next_dose !== null && hours_until_next_dose !== undefined && (
        <div className="text-xs flex items-center gap-2 font-semibold text-slate-700 bg-emerald-50/80 px-3 py-1.5 rounded-lg border border-slate-200/60">
          <span>Next scheduled dose in: <strong>{hours_until_next_dose} hours</strong></span>
          {next_scheduled_time && (
            <span>({new Date(next_scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})</span>
          )}
        </div>
      )}

      <p className="text-xs italic text-slate-600 border-t border-slate-200/60 pt-2">
        ℹ️ {disclaimer}
      </p>
    </div>
  );
};

export default AntiStackingAdvisor;
