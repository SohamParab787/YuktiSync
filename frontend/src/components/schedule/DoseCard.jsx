import React, { useState, useEffect } from 'react';

export const DoseCard = ({
  dose,
  isNextDose = false,
  secondsRemaining = 0,
  onMarkStatus,
  onCheckSafety,
  disabled = false
}) => {
  const [countdown, setCountdown] = useState(secondsRemaining);
  const [loadingStatus, setLoadingStatus] = useState(false);

  useEffect(() => {
    setCountdown(secondsRemaining);
  }, [secondsRemaining]);

  useEffect(() => {
    if (!isNextDose || countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [isNextDose, countdown]);

  const formatCountdown = (secs) => {
    if (secs <= 0) return 'Due now';
    const hrs = Math.floor(secs / 3600);
    const mins = Math.floor((secs % 3600) / 60);
    const s = secs % 60;
    if (hrs > 0) return `${hrs}h ${mins}m remaining`;
    if (mins > 0) return `${mins}m ${s}s remaining`;
    return `${s}s remaining`;
  };

  const handleAction = async (status) => {
    if (disabled || loadingStatus) return;
    setLoadingStatus(true);
    try {
      await onMarkStatus(dose.id, status);
    } finally {
      setLoadingStatus(false);
    }
  };

  const currentStatus = (dose?.status || 'pending').toLowerCase();

  const getStatusBadge = (statusStr) => {
    switch (statusStr) {
      case 'taken':
        return (
          <span
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200"
            role="status"
            aria-label="Status: Taken"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
            ✓ Taken
          </span>
        );
      case 'missed':
        return (
          <span
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200"
            role="status"
            aria-label="Status: Missed"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
            ✕ Missed
          </span>
        );
      case 'skipped':
        return (
          <span
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200"
            role="status"
            aria-label="Status: Skipped"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
            ⊘ Skipped
          </span>
        );
      case 'delayed':
        return (
          <span
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200"
            role="status"
            aria-label="Status: Delayed"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
            ⏰ Delayed
          </span>
        );
      case 'upcoming':
      case 'pending':
      default:
        return (
          <span
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"
            role="status"
            aria-label="Status: Pending"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            ⌛ Pending
          </span>
        );
    }
  };

  const formattedTime = dose?.scheduled_time
    ? new Date(dose.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : dose?.scheduled_time;

  return (
    <div
      className={`rounded-2xl border p-4 sm:p-5 transition-all shadow-sm ${
        isNextDose
          ? 'border-emerald-500 bg-emerald-50/40 ring-2 ring-emerald-200 shadow-emerald-50'
          : 'border-slate-200 bg-white hover:border-emerald-300 hover:shadow'
      }`}
      role="article"
      aria-label={`Medication dose: ${dose?.medication_name}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Left Side: Medicine details */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
              {formattedTime}
            </span>
            <h4 className="font-bold text-slate-900 text-base sm:text-lg">
              {dose?.medication_name}
            </h4>
            <span className="text-xs font-semibold text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
              {dose?.dosage}
            </span>
            {getStatusBadge(currentStatus)}
            {isNextDose && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-600 text-white shadow-xs">
                Next Dose
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs sm:text-sm text-slate-600 flex-wrap">
            {/* Food Instruction Badge */}
            {dose?.food_instruction && (
              <span className="inline-flex items-center gap-1 font-medium text-emerald-800 bg-emerald-50 px-2.5 py-0.5 rounded-md border border-emerald-100">
                🍽️ {dose.food_instruction}
              </span>
            )}
            
            {isNextDose && (
              <span className="font-mono text-emerald-700 font-semibold bg-emerald-100/60 px-2.5 py-0.5 rounded">
                ⏳ {formatCountdown(countdown)}
              </span>
            )}
          </div>

          {dose?.instructions && (
            <p className="text-xs text-slate-500 italic">
              💡 {dose.instructions}
            </p>
          )}

          {dose?.taken_at && (
            <p className="text-xs text-emerald-700 font-medium">
              ✓ Taken at {new Date(dose.taken_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          )}
        </div>

        {/* Right Side: Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          {currentStatus !== 'taken' && (
            <button
              onClick={() => handleAction('taken')}
              disabled={disabled || loadingStatus}
              className="px-3.5 py-2 rounded-xl text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50 transition-colors shadow-xs"
              aria-label={`Mark ${dose?.medication_name} as taken`}
            >
              {loadingStatus ? 'Updating...' : '✓ Mark as Taken'}
            </button>
          )}

          {currentStatus !== 'delayed' && currentStatus !== 'taken' && (
            <button
              onClick={() => handleAction('delayed')}
              disabled={disabled || loadingStatus}
              className="px-3 py-2 rounded-xl text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 disabled:opacity-50 transition-colors"
              aria-label={`Mark ${dose?.medication_name} as delayed`}
            >
              Delayed
            </button>
          )}

          {currentStatus !== 'missed' && currentStatus !== 'skipped' && currentStatus !== 'taken' && (
            <button
              onClick={() => handleAction('skipped')}
              disabled={disabled || loadingStatus}
              className="px-3 py-2 rounded-xl text-xs font-semibold bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100 disabled:opacity-50 transition-colors"
              aria-label={`Skip ${dose?.medication_name}`}
            >
              Skip
            </button>
          )}

          {onCheckSafety && (currentStatus === 'missed' || currentStatus === 'delayed' || currentStatus === 'pending') && (
            <button
              onClick={() => onCheckSafety(dose)}
              className="px-2.5 py-2 rounded-xl text-xs font-medium text-emerald-700 hover:bg-emerald-50 border border-emerald-200 transition-colors"
              title="Check dose safety / anti-stacking"
            >
              🛡️ Safety
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DoseCard;
