import React from "react";
import CaregiverDashboard from "../components/caregiver/Dashboard";

export default function DashboardPage({ patientId = "patient-101" }) {
  return (
    <div className="page-wrapper">
      <CaregiverDashboard patientId={patientId} />
    </div>
  );
}
