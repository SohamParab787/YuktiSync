import React, { useState, useEffect } from 'react';
import { fetchScheduleTimeline, markDoseStatus, generateSchedule } from '../api/schedule';
import { ScheduleTimeline } from '../components/schedule/ScheduleTimeline';
import { AdherenceSummary } from '../components/schedule/AdherenceSummary';
import { DashboardSkeleton } from '../components/schedule/SkeletonLoaders';
import { ErrorState } from '../components/schedule/EmptyState';

export const SchedulePage = ({ userId = 'user-1' }) => {
  const [viewType, setViewType] = useState('daily');
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchScheduleTimeline(userId, viewType);
      setTimelineData(data);
    } catch (err) {
      setError(err.message || 'Failed to load medication schedule.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, [userId, viewType]);

  const handleMarkDose = async (doseId, status) => {
    try {
      await markDoseStatus(doseId, status);
      await loadTimeline();
    } catch (err) {
      alert(`Error updating dose: ${err.message}`);
    }
  };

  const handleGenerateSchedule = async () => {
    try {
      setLoading(true);
      await generateSchedule(userId);
      await loadTimeline();
    } catch (err) {
      alert(`Error generating schedule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !timelineData) {
    return <DashboardSkeleton />;
  }

  if (error && !timelineData) {
    return (
      <div className="max-w-4xl mx-auto p-4">
        <ErrorState message={error} onRetry={loadTimeline} />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-widest">MediAdhere Schedule Module</span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1">Medication Schedule & Calendar</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Track daily and weekly dose schedules, log adherence, and generate timetables.
          </p>
        </div>
      </div>

      <ScheduleTimeline
        timelineData={timelineData}
        viewType={viewType}
        onViewTypeChange={setViewType}
        onMarkStatus={handleMarkDose}
        onGenerateSchedule={handleGenerateSchedule}
        loading={loading}
      />
    </div>
  );
};

export default SchedulePage;
