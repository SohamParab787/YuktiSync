import React, { useState, useEffect } from 'react';

export const DoseCard = ({
  dose,
  isNextDose = false,
  secondsRemaining = 0,
  onMarkStatus,
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

  const currentStatus = (dose?.status || 'upcoming').toLowerCase();

  const getStatusBadge = (statusStr) => {
    switch (statusStr) {
      case 'taken':
        return (
          <span
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800"
            role="status"
            aria-label="Status: Taken"
          >
            ✓ Taken
          </span>
        );
      case 'missed':
        return (
          <span
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800"
            role="status"
            aria-label="Status: Missed"
          >
            ✕ Missed
          </span>
        );
      case 'delayed':
        return (
          <span
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800"
            role="status"
            aria-label="Status: Delayed"
          >
            ⏰ Delayed
          </span>
        );
      case 'upcoming':
      default:
        return (
          <span
            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800"
            role="status"
            aria-label="Status: Upcoming"
          >
            ⌛ Upcoming
          </span>
        );
    }
  };

  const formattedTime = dose?.scheduled_time
    ? new Date(dose.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : dose?.scheduled_time;

  return (
    <div
      className={`rounded-xl border p-4 transition-all shadow-sm ${
        isNextDose
          ? 'border-blue-500 bg-blue-50/40 ring-2 ring-blue-200'
          : 'border-slate-200 bg-white hover:border-slate-300'
      }`}
      role="article"
      aria-label={`Medication dose: ${dose?.medication_name}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-bold text-slate-900 text-lg">{dose?.medication_name}</h4>
            <span className="text-sm font-medium text-slate-500">({dose?.dosage})</span>
            {getStatusBadge(currentStatus)}
            {isNextDose && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blue-600 text-white">
                Next Scheduled Dose
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 text-sm text-slate-600">
            <span>Scheduled: <strong>{formattedTime}</strong></span>
            {isNextDose && (
              <span className="font-mono text-blue-700 font-semibold">
                ⏳ {formatCountdown(countdown)}
              </span>
            )}
          </div>

          {dose?.instructions && (
            <p className="text-xs text-slate-500 italic mt-1">
              💡 {dose.instructions}
            </p>
          )}

          {dose?.taken_at && (
            <p className="text-xs text-green-700 mt-1">
              Recorded at: {new Date(dose.taken_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 mt-2 sm:mt-0">
          {currentStatus !== 'taken' && (
            <button
              onClick={() => handleAction('taken')}
              disabled={disabled || loadingStatus}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-green-600 text-white hover:bg-green-700 active:bg-green-800 disabled:opacity-50 transition-colors"
              aria-label={`Mark ${dose?.medication_name} as taken`}
            >
              {loadingStatus ? 'Saving...' : 'Mark Taken'}
            </button>
          )}

          {currentStatus !== 'missed' && (
            <button
              onClick={() => handleAction('missed')}
              disabled={disabled || loadingStatus}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-100 text-red-700 hover:bg-red-200 active:bg-red-300 disabled:opacity-50 transition-colors"
              aria-label={`Mark ${dose?.medication_name} as missed`}
            >
              {loadingStatus ? 'Saving...' : 'Mark Missed'}
            </button>
          )}

          {currentStatus !== 'delayed' && currentStatus !== 'taken' && (
            <button
              onClick={() => handleAction('delayed')}
              disabled={disabled || loadingStatus}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-100 text-amber-800 hover:bg-amber-200 disabled:opacity-50 transition-colors"
              aria-label={`Mark ${dose?.medication_name} as delayed`}
            >
              {loadingStatus ? 'Saving...' : 'Mark Delayed'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
