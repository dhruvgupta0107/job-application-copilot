import "./ApplicationCard.css";

const STATUS_LABEL = {
  drafted: "DRAFTED",
  sent: "SENT",
  interview: "INTERVIEW",
  rejected: "REJECTED",
  offer: "OFFER",
};

export default function ApplicationCard({ application, onClick }) {
  const status = application.status || "drafted";
  return (
    <button className="stub" onClick={onClick}>
      <div className="stub__main">
        <span className="stub__id mono">#{application.id.slice(0, 8)}</span>
        <span className="stub__role">{application.role}</span>
        <span className="stub__company">{application.company}</span>
      </div>
      <div className="stub__perforation" aria-hidden="true" />
      <div className={`stub__status stub__status--${status}`}>
        {STATUS_LABEL[status] || status.toUpperCase()}
      </div>
    </button>
  );
}
