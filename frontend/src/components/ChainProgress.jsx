import "./ChainProgress.css";

const STAGES = [
  { key: "parse", label: "Parse JD" },
  { key: "retrieve", label: "Retrieve" },
  { key: "rewrite", label: "Rewrite" },
  { key: "draft", label: "Draft outreach" },
];

// status per stage: 'pending' | 'active' | 'done' | 'error'
export default function ChainProgress({ statuses }) {
  return (
    <div className="chain-progress" role="status" aria-live="polite">
      {STAGES.map((stage, i) => {
        const status = statuses[stage.key] || "pending";
        return (
          <div className="chain-stage" key={stage.key}>
            <div className="chain-stage__row">
              <span className="chain-stage__index mono">0{i + 1}</span>
              <span className="chain-stage__label">{stage.label}</span>
              <span className={`stamp stamp--${status}`}>
                {status === "done" && "PASSED"}
                {status === "active" && "PROCESSING"}
                {status === "error" && "FAILED"}
                {status === "pending" && "—"}
              </span>
            </div>
            {i < STAGES.length - 1 && <div className="chain-stage__connector" />}
          </div>
        );
      })}
    </div>
  );
}
