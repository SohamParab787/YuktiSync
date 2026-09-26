import React from 'react';

export const DoseCardSkeleton = () => (
  <div className="rounded-xl border border-slate-200 p-4 bg-white animate-pulse space-y-3">
    <div className="flex items-center justify-between">
      <div className="h-5 w-40 bg-slate-200 rounded"></div>
      <div className="h-4 w-20 bg-slate-200 rounded-full"></div>
    </div>
    <div className="h-4 w-32 bg-slate-200 rounded"></div>
    <div className="flex justify-end gap-2 pt-2">
      <div className="h-7 w-24 bg-slate-200 rounded-lg"></div>
      <div className="h-7 w-24 bg-slate-200 rounded-lg"></div>
    </div>
  </div>
);

export const DashboardSkeleton = () => (
  <div className="space-y-6 animate-pulse max-w-5xl mx-auto p-4">
    <div className="h-8 w-64 bg-slate-200 rounded-lg"></div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-2 space-y-4">
        <DoseCardSkeleton />
        <DoseCardSkeleton />
      </div>
      <div className="h-64 bg-slate-200 rounded-xl"></div>
    </div>
  </div>
);
