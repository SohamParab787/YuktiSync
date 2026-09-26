import React, { useState, useEffect } from 'react';
import { fetchScheduleTimeline, markDoseStatus, generateSchedule, checkAntiStacking } from '../api/schedule';
import { ScheduleTimeline } from '../components/schedule/ScheduleTimeline';
import { AntiStackingAdvisor } from '../components/schedule/AntiStackingAdvisor';
import { DashboardSkeleton } from '../components/schedule/SkeletonLoaders';
import { ErrorState } from '../components/schedule/EmptyState';

export const SchedulePage = ({ userId = 'user-1' }) => {
  const [viewType, setViewType] = useState('daily');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [safetyAdvice, setSafetyAdvice] = useState(null);

  const loadTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchScheduleTimeline(userId, viewType, selectedDate);
      setTimelineData(data);
    } catch (err) {
      setError(err.message || 'Failed to load medication schedule.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, [userId, viewType, selectedDate]);

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

  const handleCheckSafety = async (dose) => {
    try {
      const advice = await checkAntiStacking(userId, dose.medication_name, dose.id);
      setSafetyAdvice(advice);
    } catch (err) {
      alert(`Failed to check dose safety: ${err.message}`);
    }
  };

  if (loading && !timelineData) {
    return <DashboardSkeleton />;
  }

  if (error && !timelineData) {
    return (
      <div className="w-full max-w-[1680px] mx-auto p-6">
        <ErrorState message={error} onRetry={loadTimeline} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-emerald-50/60 pb-16">
      <div className="w-full max-w-[1680px] mx-auto px-4 sm:px-6 lg:px-10 pt-6 space-y-6">
        
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-emerald-800 to-emerald-900 rounded-3xl p-6 sm:p-8 text-white shadow-lg shadow-emerald-950/10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <span className="text-xs font-bold text-emerald-300 uppercase tracking-widest">YuktiSync Schedule</span>
            <h1 className="text-2xl sm:text-3xl font-black text-white">Medication Timetable & Calendar</h1>
            <p className="text-xs sm:text-sm text-emerald-100/90 max-w-xl">
              View your personalized daily and weekly medication routine, instructions, meal timings, and status.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-white/10 border border-white/20 rounded-xl px-3 py-2 text-xs font-medium text-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>
        </div>

        {/* Safety Advisor Popup */}
        {safetyAdvice && (
          <AntiStackingAdvisor
            advice={safetyAdvice}
            onClose={() => setSafetyAdvice(null)}
          />
        )}

        {/* Timeline View */}
        <ScheduleTimeline
          timelineData={timelineData}
          viewType={viewType}
          currentDate={selectedDate}
          onViewTypeChange={setViewType}
          onDateChange={setSelectedDate}
          onMarkStatus={handleMarkDose}
          onCheckSafety={handleCheckSafety}
          onGenerateSchedule={handleGenerateSchedule}
          loading={loading}
        />
      </div>
    </div>
  );
};

export default SchedulePage;
