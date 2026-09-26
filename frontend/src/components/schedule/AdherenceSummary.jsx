import React from 'react';

export const AdherenceSummary = ({ summary, title = "Today's Adherence" }) => {
  if (!summary) return null;

  const {
    total_doses = 0,
    taken_doses = 0,
    missed_doses = 0,
    delayed_doses = 0,
    upcoming_doses = 0,
    adherence_percentage = 100.0,
  } = summary;

  const dueDoses = taken_doses + missed_doses + delayed_doses;

  const getProgressColor = (pct) => {
    if (pct >= 80) return 'bg-green-500 text-green-700';
    if (pct >= 50) return 'bg-amber-500 text-amber-700';
    return 'bg-red-500 text-red-700';
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-800 text-base">{title}</h3>
        <span className={`text-2xl font-black ${getProgressColor(adherence_percentage).split(' ')[1]}`}>
          {adherence_percentage}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden flex">
          <div
            className="bg-green-500 h-full transition-all duration-500"
            style={{ width: `${dueDoses > 0 ? (taken_doses / dueDoses) * 100 : 0}%` }}
            title={`Taken: ${taken_doses}`}
          />
          <div
            className="bg-amber-400 h-full transition-all duration-500"
            style={{ width: `${dueDoses > 0 ? (delayed_doses / dueDoses) * 100 : 0}%` }}
            title={`Delayed: ${delayed_doses}`}
          />
          <div
            className="bg-red-500 h-full transition-all duration-500"
            style={{ width: `${dueDoses > 0 ? (missed_doses / dueDoses) * 100 : 0}%` }}
            title={`Missed: ${missed_doses}`}
          />
        </div>
        <div
          role="progressbar"
          aria-valuenow={adherence_percentage}
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label={`${title} adherence percentage: ${adherence_percentage}%`}
          className="sr-only"
        />
      </div>

      <p className="text-xs text-slate-500 font-medium">
        {taken_doses} of {total_doses} doses taken ({upcoming_doses} upcoming)
      </p>

      {/* Breakdown Grid */}
      <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-100 text-center">
        <div className="bg-green-50 rounded-lg p-2">
          <span className="block text-xs text-green-700 font-medium">Taken</span>
          <span className="text-lg font-bold text-green-800">{taken_doses}</span>
        </div>
        <div className="bg-amber-50 rounded-lg p-2">
          <span className="block text-xs text-amber-700 font-medium">Delayed</span>
          <span className="text-lg font-bold text-amber-800">{delayed_doses}</span>
        </div>
        <div className="bg-red-50 rounded-lg p-2">
          <span className="block text-xs text-red-700 font-medium">Missed</span>
          <span className="text-lg font-bold text-red-800">{missed_doses}</span>
        </div>
        <div className="bg-blue-50 rounded-lg p-2">
          <span className="block text-xs text-blue-700 font-medium">Upcoming</span>
          <span className="text-lg font-bold text-blue-800">{upcoming_doses}</span>
        </div>
      </div>
    </div>
  );
};
