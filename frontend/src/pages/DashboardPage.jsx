import React, { useState, useEffect } from 'react';
import { fetchDashboard, markDoseStatus, generateSchedule, checkAntiStacking, fetchAdherenceSummary } from '../api/schedule';
import { DoseCard } from '../components/schedule/DoseCard';
import { AdherenceSummary } from '../components/schedule/AdherenceSummary';
import { RiskAlertBanner } from '../components/schedule/RiskAlertBanner';
import { AntiStackingAdvisor } from '../components/schedule/AntiStackingAdvisor';
import { RecentActivity } from '../components/schedule/RecentActivity';
import { DashboardSkeleton } from '../components/schedule/SkeletonLoaders';
import { EmptyState, ErrorState } from '../components/schedule/EmptyState';

export const DashboardPage = ({ userId = 'user-1' }) => {
  const [data, setData] = useState(null);
  const [weeklyAdherence, setWeeklyAdherence] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const [selectedSafetyAdvice, setSelectedSafetyAdvice] = useState(null);
  const [safetyLoading, setSafetyLoading] = useState(false);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashRes, weekRes] = await Promise.all([
        fetchDashboard(userId),
        fetchAdherenceSummary(userId, 'week')
      ]);
      setData(dashRes);
      setWeeklyAdherence(weekRes);
      if (dashRes.anti_stacking_advice) {
        setSelectedSafetyAdvice(dashRes.anti_stacking_advice);
      }
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
      setTimeout(() => setActionMessage(null), 3500);
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

  const handleCheckSafety = async (dose) => {
    setSafetyLoading(true);
    try {
      const advice = await checkAntiStacking(userId, dose.medication_name, dose.id);
      setSelectedSafetyAdvice(advice);
    } catch (err) {
      alert(`Failed to check dose safety: ${err.message}`);
    } finally {
      setSafetyLoading(false);
    }
  };

  if (loading && !data) {
    return <DashboardSkeleton />;
  }

  if (error && !data) {
    return (
      <div className="w-full max-w-[1680px] mx-auto p-6">
        <ErrorState message={error} onRetry={loadDashboardData} />
      </div>
    );
  }

  const {
    greeting = 'Good Morning',
    todays_doses = [],
    next_dose = null,
    adherence_summary = null,
    missed_alerts = [],
    risk_alerts = [],
    escalation_status = null,
    recent_activities = []
  } = data || {};

  const missedDoses = todays_doses.filter(d => ['missed', 'skipped'].includes(d.status?.toLowerCase()));
  const pendingDoses = todays_doses.filter(d => ['pending', 'upcoming'].includes(d.status?.toLowerCase()));
  const completedDoses = todays_doses.filter(d => ['taken', 'delayed'].includes(d.status?.toLowerCase()));

  return (
    <div className="min-h-screen bg-emerald-50/60 pb-16">
      <div className="w-full max-w-[1680px] mx-auto px-4 sm:px-6 lg:px-10 pt-6 space-y-6">
        
        {/* Top Header Card */}
        <div className="bg-gradient-to-r from-emerald-800 to-emerald-900 rounded-3xl p-6 sm:p-8 text-white shadow-lg shadow-emerald-950/10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-700/60 border border-emerald-500/40 text-emerald-200 text-xs font-semibold tracking-wide">
              <span>🌿 YuktiSync Health Portal</span>
              <span>•</span>
              <span>Patient Dashboard</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
              {greeting}
            </h1>
            <p className="text-emerald-100/90 text-sm max-w-xl leading-relaxed">
              Welcome back to your medication schedule. You have <strong>{pendingDoses.length}</strong> upcoming doses scheduled for today.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadDashboardData}
              className="px-4 py-2.5 rounded-xl text-xs font-bold bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all backdrop-blur-xs flex items-center gap-1.5"
            >
              🔄 Refresh
            </button>
            <button
              onClick={handleGenerateSchedule}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-400 hover:bg-emerald-300 text-emerald-950 transition-all shadow-md flex items-center gap-1.5"
            >
              + Sync Prescription
            </button>
          </div>
        </div>

        {/* Action Alert Banner */}
        {actionMessage && (
          <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs sm:text-sm font-semibold px-5 py-3 rounded-2xl animate-fade-in shadow-xs flex items-center gap-2">
            <span>✓</span> {actionMessage}
          </div>
        )}

        {/* Missed Dose Escalation Banner */}
        {escalation_status && escalation_status.escalated_to_caregiver && (
          <div className="bg-rose-50 border-2 border-rose-300 text-rose-950 p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-lg">🚨</span>
                <span className="font-bold text-sm sm:text-base">Caregiver Escalation Triggered</span>
                <span className="px-2 py-0.5 bg-rose-600 text-white text-[10px] font-black rounded uppercase">
                  {escalation_status.alert_level}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-rose-800 leading-relaxed">
                {escalation_status.message} Caregiver module has been alerted via YuktiSync escalation protocol.
              </p>
            </div>
            <button
              onClick={() => handleCheckSafety(missedDoses[0] || { medication_name: 'Medication' })}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl transition-colors shrink-0"
            >
              Review Safety
            </button>
          </div>
        )}

        {/* Anti-Stacking Safety Advice Box */}
        {selectedSafetyAdvice && (
          <AntiStackingAdvisor
            advice={selectedSafetyAdvice}
            onClose={() => setSelectedSafetyAdvice(null)}
          />
        )}

        {/* Drug Safety / Interaction Alerts */}
        {risk_alerts.length > 0 && (
          <div className="space-y-2">
            <h3 className="font-bold text-slate-800 text-sm flex items-center gap-1.5">
              <span>🛡️</span> Medication Risk & Interaction Alerts
            </h3>
            <RiskAlertBanner alerts={risk_alerts} />
          </div>
        )}

        {/* Next Scheduled Dose Highlight Card */}
        {next_dose && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Next Due Medication
              </span>
              <span className="text-xs text-slate-400">Scheduled chronologically</span>
            </div>
            <DoseCard
              dose={{
                id: next_dose.dose_id,
                medication_id: next_dose.medication_id,
                medication_name: next_dose.medication_name,
                dosage: next_dose.dosage,
                scheduled_time: next_dose.scheduled_time,
                status: 'pending',
                food_instruction: next_dose.food_instruction,
                instructions: next_dose.instructions,
              }}
              isNextDose={true}
              secondsRemaining={next_dose.seconds_remaining}
              onMarkStatus={handleMarkDose}
              onCheckSafety={handleCheckSafety}
            />
          </div>
        )}

        {/* Main Two-Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column (2/3 width): Today's Schedule */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Missed Doses Section */}
            {missedDoses.length > 0 && (
              <div className="bg-rose-50/60 border border-rose-200 p-5 rounded-2xl space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">⚠️</span>
                    <h3 className="font-bold text-rose-900 text-sm uppercase tracking-wide">
                      Missed Doses Needing Attention ({missedDoses.length})
                    </h3>
                  </div>
                  <span className="text-xs text-rose-700 font-medium">Auto-detected past grace window</span>
                </div>
                <div className="space-y-2.5">
                  {missedDoses.map((dose) => (
                    <DoseCard
                      key={dose.id}
                      dose={dose}
                      onMarkStatus={handleMarkDose}
                      onCheckSafety={handleCheckSafety}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Today's Full Schedule */}
            <div className="bg-[#f1f7f1] rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h2 className="font-bold text-slate-900 text-lg">Today's Medication</h2>
                  <p className="text-xs text-slate-500">
                    {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                  </p>
                </div>
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-100">
                  {todays_doses.length} doses total
                </span>
              </div>

              {todays_doses.length === 0 ? (
                <EmptyState
                  message="No medications scheduled for today. Sync your prescription to generate your timetable."
                  onAction={handleGenerateSchedule}
                />
              ) : (
                <div className="space-y-3 pt-1">
                  {todays_doses.map((dose) => (
                    <DoseCard
                      key={dose.id}
                      dose={dose}
                      onMarkStatus={handleMarkDose}
                      onCheckSafety={handleCheckSafety}
                    />
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Right Column (1/3 width): Adherence, Weekly Stats, and Activity */}
          <div className="space-y-6">
            
            {/* Today's Adherence Summary */}
            <AdherenceSummary
              summary={adherence_summary}
              title="Today's Adherence"
            />

            {/* Weekly Adherence Summary */}
            {weeklyAdherence && (
              <AdherenceSummary
                summary={{
                  total_doses: weeklyAdherence.total_doses,
                  taken_doses: weeklyAdherence.taken_doses,
                  missed_doses: weeklyAdherence.missed_doses,
                  delayed_doses: weeklyAdherence.delayed_doses,
                  upcoming_doses: weeklyAdherence.upcoming_doses,
                  adherence_percentage: weeklyAdherence.adherence_percentage
                }}
                title="Weekly Adherence"
              />
            )}

            {/* Recent Medication Activity */}
            <RecentActivity activities={recent_activities} />

            {/* Healthcare Guidance Card */}
            <div className="bg-emerald-900 text-white rounded-2xl p-6 space-y-3 shadow-md">
              <div className="flex items-center gap-2">
                <span className="text-lg">🌿</span>
                <h4 className="font-bold text-sm tracking-wide text-white">YuktiSync Healthcare Care</h4>
              </div>
              <p className="text-xs text-emerald-100/90 leading-relaxed">
                Consistency is key to positive therapeutic outcomes. Please consult your physician or pharmacist before modifying any prescribed dose or schedule.
              </p>
              <div className="pt-3 border-t border-emerald-800/80 flex items-center justify-between text-[11px] text-emerald-300">
                <span>Grace Window: 60 mins</span>
                <span>Anti-Stacking: Active</span>
              </div>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
};

export default DashboardPage;
