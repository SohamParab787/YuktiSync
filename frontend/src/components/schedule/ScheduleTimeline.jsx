import React, { useState } from 'react';
import { DoseCard } from './DoseCard';

export const ScheduleTimeline = ({
  timelineData,
  viewType = 'daily',
  onViewTypeChange,
  onMarkStatus,
  onGenerateSchedule,
  loading = false
}) => {
  const [statusFilter, setStatusFilter] = useState('ALL');

  if (!timelineData) return null;

  const { doses = [], daily_breakdown = [], start_date, end_date } = timelineData;

  const filterDoses = (doseList) => {
    if (statusFilter === 'ALL') return doseList;
    return doseList.filter((d) => d.status?.toUpperCase() === statusFilter);
  };

  const filteredDoses = filterDoses(doses);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-5">
      {/* Header controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <h3 className="font-bold text-slate-900 text-lg">Medication Schedule</h3>
          <p className="text-xs text-slate-500">
            {viewType === 'weekly'
              ? `Week view: ${start_date} to ${end_date}`
              : `Day view: ${start_date}`}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* View toggle */}
          <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-100 text-xs font-semibold">
            <button
              onClick={() => onViewTypeChange && onViewTypeChange('daily')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewType === 'daily' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Daily View
            </button>
            <button
              onClick={() => onViewTypeChange && onViewTypeChange('weekly')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewType === 'weekly' ? 'bg-white shadow-sm text-blue-600' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Weekly View
            </button>
          </div>

          {onGenerateSchedule && (
            <button
              onClick={onGenerateSchedule}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              + Sync Schedule
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 border-b border-slate-100 pb-2 overflow-x-auto text-xs font-medium text-slate-600">
        {['ALL', 'UPCOMING', 'TAKEN', 'MISSED', 'DELAYED'].map((filter) => (
          <button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            className={`px-3 py-1.5 rounded-md transition-colors whitespace-nowrap ${
              statusFilter === filter
                ? 'bg-slate-900 text-white font-bold'
                : 'hover:bg-slate-100 text-slate-600'
            }`}
          >
            {filter.charAt(0) + filter.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Timeline List */}
      {viewType === 'daily' ? (
        <div className="space-y-3">
          {filteredDoses.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm">
              No doses match the selected filter.
            </div>
          ) : (
            filteredDoses.map((dose) => (
              <DoseCard
                key={dose.id}
                dose={dose}
                onMarkStatus={onMarkStatus}
                disabled={loading}
              />
            ))
          )}
        </div>
      ) : (
        /* Weekly View Breakdown */
        <div className="space-y-6">
          {daily_breakdown.map((day) => {
            const dayDoses = filterDoses(day.doses || []);
            return (
              <div key={day.date} className="space-y-2">
                <div className="flex items-center justify-between bg-slate-50 px-3 py-2 rounded-lg border border-slate-200">
                  <span className="font-bold text-slate-800 text-sm">
                    {new Date(day.date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                  </span>
                  <span className="text-xs font-semibold text-slate-600">
                    Adherence: {day.adherence_percentage}% ({day.taken_doses}/{day.total_doses} taken)
                  </span>
                </div>

                <div className="space-y-2 pl-2">
                  {dayDoses.length === 0 ? (
                    <p className="text-xs text-slate-400 italic py-1">No doses scheduled for this day.</p>
                  ) : (
                    dayDoses.map((dose) => (
                      <DoseCard
                        key={dose.id}
                        dose={dose}
                        onMarkStatus={onMarkStatus}
                        disabled={loading}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
