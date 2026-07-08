import { useState } from "react";
import UploadResume from "./pages/UploadResume";
import SubmitApplication from "./pages/SubmitApplication";
import Applications from "./pages/Applications";
import "./App.css";

const TABS = [
  { key: "submit", label: "Process JD" },
  { key: "applications", label: "Applications" },
  { key: "upload", label: "Knowledge base" },
];

export default function App() {
  const [tab, setTab] = useState("submit");
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-mark">JOB//COPILOT</span>
        <nav className="app-nav">
          {TABS.map((t) => (
            <button
              key={t.key}
              className={`app-nav__item ${tab === t.key ? "app-nav__item--active" : ""}`}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app-main">
        {tab === "submit" && (
          <SubmitApplication onSubmitted={() => setRefreshKey((k) => k + 1)} />
        )}
        {tab === "applications" && <Applications refreshKey={refreshKey} />}
        {tab === "upload" && <UploadResume />}
      </main>
    </div>
  );
}
