import React from 'react';

export const EmptyState = ({ message = "No medications scheduled today.", onAction, actionLabel = "Generate Schedule" }) => (
  <div className="bg-[#f1f7f1] rounded-xl border border-slate-200 p-8 text-center space-y-4 shadow-sm">
    <div className="text-4xl">💊</div>
    <h4 className="font-bold text-slate-800 text-lg">No Scheduled Doses Found</h4>
    <p className="text-sm text-slate-500 max-w-sm mx-auto">{message}</p>
    {onAction && (
      <button
        onClick={onAction}
        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg transition-colors"
      >
        {actionLabel}
      </button>
    )}
  </div>
);

export const ErrorState = ({ message = "Failed to load dashboard data.", onRetry }) => (
  <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center space-y-3">
    <div className="text-3xl">⚠️</div>
    <h4 className="font-bold text-red-900 text-base">Service Temporarily Unavailable</h4>
    <p className="text-xs text-red-700 max-w-md mx-auto">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white font-semibold text-xs rounded-lg transition-colors"
      >
        Try Again
      </button>
    )}
  </div>
);
