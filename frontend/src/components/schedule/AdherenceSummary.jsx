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

  const getScoreColor = (pct) => {
    if (pct >= 80) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (pct >= 50) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  return (
    <div className="bg-[#f1f7f1] rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">Health Adherence</span>
          <h3 className="font-bold text-slate-900 text-lg">{title}</h3>
        </div>
        <div className={`px-3 py-1.5 rounded-xl border text-xl font-black ${getScoreColor(adherence_percentage)}`}>
          {adherence_percentage}%
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden flex">
          <div
            className="bg-emerald-500 h-full transition-all duration-500"
            style={{ width: `${dueDoses > 0 ? (taken_doses / dueDoses) * 100 : 0}%` }}
            title={`Taken: ${taken_doses}`}
          />
          <div
            className="bg-amber-400 h-full transition-all duration-500"
            style={{ width: `${dueDoses > 0 ? (delayed_doses / dueDoses) * 100 : 0}%` }}
            title={`Delayed: ${delayed_doses}`}
          />
          <div
            className="bg-rose-500 h-full transition-all duration-500"
            style={{ width: `${dueDoses > 0 ? (missed_doses / dueDoses) * 100 : 0}%` }}
            title={`Missed: ${missed_doses}`}
          />
        </div>
        <div className="flex justify-between text-xs text-slate-500 font-medium">
          <span>{taken_doses} of {total_doses} doses recorded</span>
          <span>{upcoming_doses} pending today</span>
        </div>
      </div>

      {/* Breakdown Grid */}
      <div className="grid grid-cols-4 gap-2 pt-2 border-t border-slate-100 text-center">
        <div className="bg-emerald-50/70 border border-emerald-100 rounded-xl p-2.5">
          <span className="block text-xs text-emerald-800 font-medium">Taken</span>
          <span className="text-lg font-bold text-emerald-900">{taken_doses}</span>
        </div>
        <div className="bg-amber-50/70 border border-amber-100 rounded-xl p-2.5">
          <span className="block text-xs text-amber-800 font-medium">Delayed</span>
          <span className="text-lg font-bold text-amber-900">{delayed_doses}</span>
        </div>
        <div className="bg-rose-50/70 border border-rose-100 rounded-xl p-2.5">
          <span className="block text-xs text-rose-800 font-medium">Missed</span>
          <span className="text-lg font-bold text-rose-900">{missed_doses}</span>
        </div>
        <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5">
          <span className="block text-xs text-slate-600 font-medium">Pending</span>
          <span className="text-lg font-bold text-slate-800">{upcoming_doses}</span>
        </div>
      </div>
    </div>
  );
};

export default AdherenceSummary;
