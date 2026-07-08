import { useEffect, useState } from "react";
import ApplicationCard from "../components/ApplicationCard";
import { listApplications } from "../api";
import "./Applications.css";

export default function Applications({ refreshKey }) {
  const [applications, setApplications] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    listApplications()
      .then((data) => {
        setApplications(data);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [refreshKey]);

  return (
    <div className="applications-page">
      <h1 className="page-title">Applications</h1>
      <p className="page-subtitle">
        Every job description you've processed, with its tailored output.
      </p>

      {loading && <p className="mono status-line">Loading…</p>}
      {error && <p className="upload-error">Couldn't reach the backend: {error}</p>}

      {!loading && !error && applications.length === 0 && (
        <p className="mono status-line">
          Nothing here yet. Process a job description to see it appear.
        </p>
      )}

      <div className="stub-list">
        {applications.map((app) => (
          <ApplicationCard
            key={app.id}
            application={app}
            onClick={() => setSelected(app)}
          />
        ))}
      </div>

      {selected && (
        <div className="detail-overlay" onClick={() => setSelected(null)}>
          <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
            <button className="detail-close" onClick={() => setSelected(null)} aria-label="Close">
              ×
            </button>
            <span className="detail-id mono">#{selected.id.slice(0, 8)}</span>
            <h2 className="detail-title">
              {selected.role} · {selected.company}
            </h2>

            {selected.tailored_output ? (
              <>
                <h3 className="result-heading">Rewritten bullets</h3>
                <ul className="bullet-list">
                  {selected.tailored_output.rewritten_bullets.map((b, i) => (
                    <li key={i}>{b}</li>
                  ))}
                </ul>
                <h3 className="result-heading">Cold email</h3>
                <pre className="draft-block mono">{selected.tailored_output.outreach_email}</pre>
                <h3 className="result-heading">LinkedIn message</h3>
                <pre className="draft-block mono">{selected.tailored_output.outreach_linkedin}</pre>
              </>
            ) : (
              <p className="mono status-line">No tailored output yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
