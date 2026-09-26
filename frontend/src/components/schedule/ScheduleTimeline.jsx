import React, { useState } from 'react';
import { DoseCard } from './DoseCard';

export const ScheduleTimeline = ({
  timelineData,
  viewType = 'daily',
  currentDate,
  onViewTypeChange,
  onDateChange,
  onMarkStatus,
  onCheckSafety,
  onGenerateSchedule,
  loading = false
}) => {
  const [statusFilter, setStatusFilter] = useState('ALL');

  if (!timelineData) return null;

  const { doses = [], daily_breakdown = [], start_date, end_date } = timelineData;

  const filterDoses = (doseList) => {
    if (statusFilter === 'ALL') return doseList;
    if (statusFilter === 'PENDING') {
      return doseList.filter((d) => ['pending', 'upcoming'].includes(d.status?.toLowerCase()));
    }
    if (statusFilter === 'MISSED') {
      return doseList.filter((d) => ['missed', 'skipped'].includes(d.status?.toLowerCase()));
    }
    return doseList.filter((d) => d.status?.toUpperCase() === statusFilter);
  };

  const filteredDoses = filterDoses(doses);

  const handlePrevDay = () => {
    if (!onDateChange) return;
    const d = new Date(start_date || new Date());
    d.setDate(d.getDate() - 1);
    onDateChange(d.toISOString().split('T')[0]);
  };

  const handleNextDay = () => {
    if (!onDateChange) return;
    const d = new Date(start_date || new Date());
    d.setDate(d.getDate() + 1);
    onDateChange(d.toISOString().split('T')[0]);
  };

  const handleToday = () => {
    if (!onDateChange) return;
    onDateChange(new Date().toISOString().split('T')[0]);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
      {/* Header controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">YuktiSync Timetable</span>
          <h3 className="font-bold text-slate-900 text-xl">Medication Schedule</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {viewType === 'weekly'
              ? `Week view: ${start_date} to ${end_date}`
              : `Day view: ${new Date(start_date).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}`}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Day navigation for daily view */}
          {viewType === 'daily' && onDateChange && (
            <div className="flex items-center bg-slate-50 rounded-xl border border-slate-200 p-1 text-xs">
              <button
                onClick={handlePrevDay}
                className="px-2.5 py-1 text-slate-600 hover:text-emerald-700 font-bold hover:bg-white rounded-lg transition-colors"
                title="Previous Day"
              >
                ← Prev
              </button>
              <button
                onClick={handleToday}
                className="px-2.5 py-1 text-emerald-800 font-bold hover:bg-white rounded-lg transition-colors"
              >
                Today
              </button>
              <button
                onClick={handleNextDay}
                className="px-2.5 py-1 text-slate-600 hover:text-emerald-700 font-bold hover:bg-white rounded-lg transition-colors"
                title="Next Day"
              >
                Next →
              </button>
            </div>
          )}

          {/* View toggle */}
          <div className="inline-flex rounded-xl border border-slate-200 p-1 bg-slate-100 text-xs font-semibold">
            <button
              onClick={() => onViewTypeChange && onViewTypeChange('daily')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewType === 'daily' ? 'bg-white shadow-xs text-emerald-700 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Daily View
            </button>
            <button
              onClick={() => onViewTypeChange && onViewTypeChange('weekly')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewType === 'weekly' ? 'bg-white shadow-xs text-emerald-700 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Weekly View
            </button>
          </div>

          {onGenerateSchedule && (
            <button
              onClick={onGenerateSchedule}
              className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-xs"
            >
              + Sync Prescription
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-100 pb-3 overflow-x-auto text-xs font-medium text-slate-600">
        {[
          { key: 'ALL', label: 'All Doses' },
          { key: 'PENDING', label: 'Pending / Due' },
          { key: 'TAKEN', label: 'Taken' },
          { key: 'DELAYED', label: 'Delayed' },
          { key: 'MISSED', label: 'Missed / Skipped' }
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setStatusFilter(f.key)}
            className={`px-3.5 py-1.5 rounded-xl transition-colors whitespace-nowrap ${
              statusFilter === f.key
                ? 'bg-emerald-700 text-white font-bold shadow-xs'
                : 'hover:bg-slate-100 text-slate-600'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Timeline List */}
      {viewType === 'daily' ? (
        <div className="space-y-3">
          {filteredDoses.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm bg-slate-50 rounded-2xl border border-dashed border-slate-200">
              <span className="text-3xl block mb-2">🌿</span>
              No doses match the selected filter for this day.
            </div>
          ) : (
            filteredDoses.map((dose) => (
              <DoseCard
                key={dose.id}
                dose={dose}
                onMarkStatus={onMarkStatus}
                onCheckSafety={onCheckSafety}
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
              <div key={day.date} className="space-y-2.5">
                <div className="flex items-center justify-between bg-emerald-50/50 px-4 py-2.5 rounded-xl border border-emerald-100">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span className="font-bold text-slate-900 text-sm">
                      {new Date(day.date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                  <span className="text-xs font-semibold text-emerald-800 bg-white px-2.5 py-1 rounded-md border border-emerald-200">
                    Adherence: {day.adherence_percentage}% ({day.taken_doses}/{day.total_doses} taken)
                  </span>
                </div>

                <div className="space-y-2 pl-2">
                  {dayDoses.length === 0 ? (
                    <p className="text-xs text-slate-400 italic py-2 pl-2">No doses scheduled for this day.</p>
                  ) : (
                    dayDoses.map((dose) => (
                      <DoseCard
                        key={dose.id}
                        dose={dose}
                        onMarkStatus={onMarkStatus}
                        onCheckSafety={onCheckSafety}
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

export default ScheduleTimeline;
