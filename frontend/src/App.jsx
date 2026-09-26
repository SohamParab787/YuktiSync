import React, { useState, useEffect } from "react";
import { BrowserRouter, Link, Navigate, NavLink, Outlet, Route, Routes } from "react-router-dom";
import Dashboard from "./components/caregiver/Dashboard";
import InviteFlow from "./components/caregiver/InviteFlow";
import ChatAssistant from "./components/caregiver/ChatAssistant";
import DashboardPage from "./pages/DashboardPage";
import SchedulePage from "./pages/SchedulePage";
import "./index.css";

function CaregiverApp() {
  const [currentPath, setCurrentPath] = useState("/caregiver/dashboard");
  const [selectedPatientId, setSelectedPatientId] = useState("patient-101");

  // Light / Dark Theme State Management
  const [theme, setTheme] = useState(() => {
    if (typeof window !== "undefined") {
      const savedTheme = localStorage.getItem("yukti_theme");
      if (savedTheme) return savedTheme;
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark";
      }
    }
    return "light";
  });

  // Apply theme to document element & body and persist in localStorage
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", theme);
      document.body.setAttribute("data-theme", theme);
    }
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("yukti_theme", theme);
    }
  }, [theme]);

  // Synchronize with browser URL path and popstate
  useEffect(() => {
    const syncFromUrl = () => {
      const path = window.location.pathname;
      if (path.startsWith("/caregiver/dashboard/")) {
        const parts = path.split("/");
        const pId = parts[parts.length - 1];
        if (pId) setSelectedPatientId(pId);
        setCurrentPath("/caregiver/dashboard");
      } else if (path.startsWith("/caregiver/invite")) {
        setCurrentPath("/caregiver/invite");
      } else if (path.startsWith("/caregiver/chat")) {
        setCurrentPath("/caregiver/chat");
      } else {
        setCurrentPath("/caregiver/dashboard");
      }
    };

    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const navigateTo = (path, patientId = null) => {
    if (patientId) setSelectedPatientId(patientId);

    let targetUrl = path;
    if (path === "/caregiver/dashboard") {
      targetUrl = `/caregiver/dashboard/${patientId || selectedPatientId}`;
    }

    if (window.location.pathname !== targetUrl) {
      window.history.pushState({}, "", targetUrl);
    }
    setCurrentPath(path);
  };

  return (
    <div className="yuktisync-app" data-theme={theme}>
      {/* Navigation Header */}
      <header className="navbar">
        <div className="nav-brand" onClick={() => navigateTo("/caregiver/dashboard")}>
          <div className="brand-icon-box">💊</div>
          <div>
            <div className="brand-name">YuktiSync</div>
            <div className="brand-tagline">Caregiver Coordination & Assistant</div>
          </div>
        </div>

        <nav className="nav-links">
          <button
            className={`nav-item-btn ${currentPath === "/caregiver/dashboard" ? "active" : ""}`}
            onClick={() => navigateTo("/caregiver/dashboard")}
          >
            <span>📊</span>
            <span>Dashboard</span>
          </button>
          <button
            className={`nav-item-btn ${currentPath === "/caregiver/invite" ? "active" : ""}`}
            onClick={() => navigateTo("/caregiver/invite")}
          >
            <span>✉️</span>
            <span>Invites & Access</span>
          </button>
          <button
            className={`nav-item-btn ${currentPath === "/caregiver/chat" ? "active" : ""}`}
            onClick={() => navigateTo("/caregiver/chat")}
          >
            <span>💬</span>
            <span>Clinical Assistant</span>
          </button>
          <Link className="nav-item-btn" to="/dashboard">Medication Dashboard</Link>
          <Link className="nav-item-btn" to="/schedule">Medication Schedule</Link>
        </nav>

        <div className="nav-controls-right">
          {/* Active Patient Switcher */}
          <div className="patient-selector-badge">
            <span>Patient:</span>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="patient-select-dropdown"
              aria-label="Select Monitored Patient"
            >
              <option value="patient-101">Ramesh Patel (patient-101)</option>
              <option value="patient-102">Dev Patient (patient-102)</option>
            </select>
          </div>

          {/* Theme Icon Switcher (No text labels) */}
          <button
            type="button"
            onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
            className="theme-switch-slider"
            title={theme === "light" ? "Switch to Dark" : "Switch to Light"}
            aria-label="Toggle theme"
          >
            <span className={`slider-thumb ${theme}`}>
              {theme === "light" ? "☀️" : "🌙"}
            </span>
          </button>
        </div>
      </header>

      <main className="app-main-layout">
        {currentPath === "/caregiver/dashboard" && (
          <Dashboard
            patientId={selectedPatientId}
            onOpenChat={() => navigateTo("/caregiver/chat")}
            onOpenInvite={() => navigateTo("/caregiver/invite")}
          />
        )}
        {currentPath === "/caregiver/invite" && (
          <InviteFlow
            defaultPatientId={selectedPatientId}
            onNavigateToDashboard={(patientId) => navigateTo("/caregiver/dashboard", patientId)}
          />
        )}
        {currentPath === "/caregiver/chat" && <ChatAssistant patientId={selectedPatientId} />}
      </main>
    </div>
  );
}

function ScheduleLayout() {
  return (
    <>
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
          <Link className="font-bold text-slate-900" to="/dashboard">YuktiSync</Link>
          <nav aria-label="Main navigation" className="flex flex-wrap gap-2 text-sm font-semibold">
            <NavLink className="rounded px-3 py-2 hover:bg-slate-100" to="/dashboard">Dashboard</NavLink>
            <NavLink className="rounded px-3 py-2 hover:bg-slate-100" to="/schedule">Schedule</NavLink>
            <NavLink className="rounded px-3 py-2 hover:bg-slate-100" to="/caregiver/dashboard/patient-101">Caregiver tools</NavLink>
          </nav>
        </div>
      </header>
      <Outlet />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route element={<ScheduleLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/schedule" element={<SchedulePage />} />
        </Route>
        <Route path="/caregiver/*" element={<CaregiverApp />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
