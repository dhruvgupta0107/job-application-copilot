import { useRef, useState } from "react";
import ChainProgress from "../components/ChainProgress";
import { submitApplication } from "../api";
import "./SubmitApplication.css";

const INITIAL_STATUSES = { parse: "pending", retrieve: "pending", rewrite: "pending", draft: "pending" };

// The backend runs all 4 chains in one request (no streaming yet), so we
// advance the visual stage-by-stage on a timer while the real request is
// in flight, then reconcile with done/error once the response lands.
const STAGE_ORDER = ["parse", "retrieve", "rewrite", "draft"];
const STAGE_INTERVAL_MS = 1400;

export default function SubmitApplication({ onSubmitted }) {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [jdText, setJdText] = useState("");
  const [statuses, setStatuses] = useState(INITIAL_STATUSES);
  const [phase, setPhase] = useState("idle"); // idle | running | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const timers = useRef([]);

  function clearTimers() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setPhase("running");
    setError("");
    setResult(null);
    const next = { ...INITIAL_STATUSES, [STAGE_ORDER[0]]: "active" };
    setStatuses(next);

    STAGE_ORDER.forEach((stage, i) => {
      if (i === 0) return;
      const t = setTimeout(() => {
        setStatuses((prev) => ({
          ...prev,
          [STAGE_ORDER[i - 1]]: "done",
          [stage]: "active",
        }));
      }, STAGE_INTERVAL_MS * i);
      timers.current.push(t);
    });

    try {
      const res = await submitApplication({ company, role, jd_text: jdText });
      clearTimers();
      setStatuses({ parse: "done", retrieve: "done", rewrite: "done", draft: "done" });
      setResult(res);
      setPhase("done");
      onSubmitted?.(res);
    } catch (err) {
      clearTimers();
      setStatuses((prev) => {
        const active = STAGE_ORDER.find((s) => prev[s] === "active") || "parse";
        return { ...prev, [active]: "error" };
      });
      setError(err.message);
      setPhase("error");
    }
  }

  return (
    <div className="submit-page">
      <h1 className="page-title">Process an application</h1>
      <p className="page-subtitle">
        Paste a job description. It runs through all four chains and comes
        back with rewritten bullets and draft outreach, grounded in whatever
        you've uploaded to the knowledge base.
      </p>

      <div className="submit-layout">
        <form className="submit-form" onSubmit={handleSubmit}>
          <label className="field">
            <span className="field__label">Company</span>
            <input value={company} onChange={(e) => setCompany(e.target.value)} required />
          </label>
          <label className="field">
            <span className="field__label">Role</span>
            <input value={role} onChange={(e) => setRole(e.target.value)} required />
          </label>
          <label className="field">
            <span className="field__label">Job description</span>
            <textarea
              rows={10}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              required
            />
          </label>
          <button className="btn" type="submit" disabled={phase === "running"}>
            {phase === "running" ? "Processing…" : "Run pipeline"}
          </button>
        </form>

        <div className="submit-progress">
          <ChainProgress statuses={statuses} />
          {phase === "error" && <p className="upload-error">{error}</p>}
        </div>
      </div>

      {phase === "done" && result?.tailored_output && (
        <div className="submit-result">
          <h2 className="result-heading">Rewritten bullets</h2>
          <ul className="bullet-list">
            {result.tailored_output.rewritten_bullets.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>

          <h2 className="result-heading">Cold email draft</h2>
          <pre className="draft-block mono">{result.tailored_output.outreach_email}</pre>

          <h2 className="result-heading">LinkedIn message draft</h2>
          <pre className="draft-block mono">{result.tailored_output.outreach_linkedin}</pre>
        </div>
      )}
    </div>
  );
}
