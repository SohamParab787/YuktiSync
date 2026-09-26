import React from 'react';

export const RecentActivity = ({ activities = [] }) => {
  if (!activities || activities.length === 0) {
    return (
      <div className="bg-[#f1f7f1] rounded-2xl border border-slate-200 p-5 text-center text-xs text-slate-400">
        No recent medication activity recorded yet.
      </div>
    );
  }

  const getActionBadge = (action) => {
    if (action.includes('Taken')) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (action.includes('Delayed')) return 'text-amber-700 bg-amber-50 border-amber-200';
    if (action.includes('Missed')) return 'text-rose-700 bg-rose-50 border-rose-200';
    if (action.includes('Skipped')) return 'text-slate-600 bg-slate-100 border-slate-200';
    return 'text-blue-700 bg-blue-50 border-blue-200';
  };

  return (
    <div className="bg-[#f1f7f1] rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <h4 className="font-bold text-slate-800 text-sm">Recent Medication Activity</h4>
        <span className="text-xs text-slate-400">Latest events</span>
      </div>

      <div className="space-y-2.5">
        {activities.map((act) => (
          <div key={act.id} className="flex items-start justify-between gap-3 text-xs p-2 rounded-xl hover:bg-slate-50 transition-colors">
            <div className="space-y-0.5">
              <span className="font-bold text-slate-900 block">{act.medication_name}</span>
              <span className="text-slate-500">{act.details || ''}</span>
            </div>
            <div className="text-right shrink-0">
              <span className={`inline-block px-2 py-0.5 rounded-md font-semibold border ${getActionBadge(act.action)}`}>
                {act.action}
              </span>
              <span className="block text-slate-400 text-[10px] mt-0.5">
                {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentActivity;
