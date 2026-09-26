import React, { useState, useEffect } from 'react';
import { fetchDashboard, markDoseStatus, generateSchedule } from '../api/schedule';
import { DoseCard } from '../components/schedule/DoseCard';
import { AdherenceSummary } from '../components/schedule/AdherenceSummary';
import { RiskAlertBanner } from '../components/schedule/RiskAlertBanner';
import { DashboardSkeleton } from '../components/schedule/SkeletonLoaders';
import { EmptyState, ErrorState } from '../components/schedule/EmptyState';

export const DashboardPage = ({ userId = 'user-1' }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDashboard(userId);
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load patient dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [userId]);

  const handleMarkDose = async (doseId, status) => {
    try {
      await markDoseStatus(doseId, status);
      setActionMessage(`Dose successfully updated to ${status}.`);
      setTimeout(() => setActionMessage(null), 3000);
      await loadDashboardData();
    } catch (err) {
      alert(`Error updating dose: ${err.message}`);
    }
  };

  const handleGenerateSchedule = async () => {
    try {
      setLoading(true);
      await generateSchedule(userId);
      await loadDashboardData();
    } catch (err) {
      alert(`Error generating schedule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return <DashboardSkeleton />;
  }

  if (error && !data) {
    return (
      <div className="max-w-4xl mx-auto p-4">
        <ErrorState message={error} onRetry={loadDashboardData} />
      </div>
    );
  }

  const {
    todays_doses = [],
    next_dose = null,
    adherence_summary = null,
    missed_alerts = [],
    risk_alerts = [],
    escalation_status = null,
  } = data || {};

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-widest">MediAdhere Patient Portal</span>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1">Patient Dashboard</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Today is {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadDashboardData}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            🔄 Refresh
          </button>
          <button
            onClick={handleGenerateSchedule}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white transition-colors shadow-sm"
          >
            + Sync Prescription Schedule
          </button>
        </div>
      </div>

      {/* Action Notification */}
      {actionMessage && (
        <div className="bg-green-100 border border-green-300 text-green-800 text-xs font-semibold px-4 py-2.5 rounded-xl animate-fade-in">
          ✓ {actionMessage}
        </div>
      )}

      {/* Missed Dose Escalation Alert */}
      {escalation_status && escalation_status.escalated_to_caregiver && (
        <div className="bg-red-50 border-2 border-red-400 text-red-900 p-4 rounded-xl flex items-center justify-between gap-3">
          <div>
            <span className="font-bold text-sm block">🚨 Caregiver Alert Escalation Active</span>
            <span className="text-xs text-red-700">{escalation_status.message}</span>
          </div>
          <span className="px-2.5 py-1 bg-red-600 text-white font-black text-xs rounded uppercase">
            {escalation_status.alert_level}
          </span>
        </div>
      )}

      {/* Risk Alert Banner (Person 3 Risk Data Display) */}
      {risk_alerts.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-bold text-slate-800 text-sm">Drug Safety & Interaction Alerts</h3>
          <RiskAlertBanner alerts={risk_alerts} />
        </div>
      )}

      {/* Main Grid: Left Column (Medication Doses) & Right Column (Adherence & Summary) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column - Today's Schedule */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-900 text-lg">Today's Schedule</h2>
            <span className="text-xs font-medium text-slate-500">{todays_doses.length} doses scheduled</span>
          </div>

          {/* Next Dose Banner (Highlighted) */}
          {next_dose && (
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-blue-700 uppercase tracking-wider">Up Next</h3>
              <DoseCard
                dose={{
                  id: next_dose.dose_id,
                  medication_id: next_dose.medication_id,
                  medication_name: next_dose.medication_name,
                  dosage: next_dose.dosage,
                  scheduled_time: next_dose.scheduled_time,
                  status: 'upcoming',
                  instructions: next_dose.instructions,
                }}
                isNextDose={true}
                secondsRemaining={next_dose.seconds_remaining}
                onMarkStatus={handleMarkDose}
              />
            </div>
          )}

          {/* Missed Doses Section */}
          {missed_alerts.length > 0 && (
            <div className="bg-red-50/50 border border-red-200 p-4 rounded-xl space-y-2">
              <h3 className="text-xs font-bold text-red-800 uppercase tracking-wider">Missed Doses Needing Attention</h3>
              {todays_doses.filter((d) => d.status === 'missed').map((d) => (
                <DoseCard
                  key={d.id}
                  dose={d}
                  onMarkStatus={handleMarkDose}
                />
              ))}
            </div>
          )}

          {/* All Today's Doses */}
          <div className="space-y-3">
            {todays_doses.length === 0 ? (
              <EmptyState message="No scheduled doses for today." onAction={handleGenerateSchedule} />
            ) : (
              todays_doses.map((dose) => (
                <DoseCard
                  key={dose.id}
                  dose={dose}
                  onMarkStatus={handleMarkDose}
                />
              ))
            )}
          </div>
        </div>

        {/* Right Column - Summary & Quick Actions */}
        <div className="space-y-6">
          <AdherenceSummary summary={adherence_summary} title="Today's Adherence" />

          {/* Quick Info Box */}
          <div className="bg-slate-900 text-white rounded-xl p-5 space-y-3 shadow-md">
            <h3 className="font-bold text-base">MediAdhere Assistant</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Timely medication adherence significantly improves health outcomes. Need help with your dosage times? Consult your caregiver or doctor.
            </p>
            <div className="pt-2 border-t border-slate-800 flex justify-between text-xs text-slate-400">
              <span>Auto grace window: 60 mins</span>
              <span>Escalation: 2+ missed</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default DashboardPage;
