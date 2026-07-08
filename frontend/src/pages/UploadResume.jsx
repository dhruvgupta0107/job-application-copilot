import { useState } from "react";
import { uploadResume } from "../api";
import "./UploadResume.css";

export default function UploadResume() {
  const [file, setFile] = useState(null);
  const [source, setSource] = useState("resume");
  const [status, setStatus] = useState("idle"); // idle | uploading | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setStatus("uploading");
    setError("");
    try {
      const res = await uploadResume(file, source);
      setResult(res);
      setStatus("done");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  return (
    <div className="upload-page">
      <h1 className="page-title">Feed the knowledge base</h1>
      <p className="page-subtitle">
        Upload your resume, project READMEs, or internship report. Each gets
        split into chunks and embedded automatically — this is what Chain 2
        retrieves from when tailoring an application.
      </p>

      <form className="upload-form" onSubmit={handleSubmit}>
        <label className="field">
          <span className="field__label">Document</span>
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </label>

        <label className="field">
          <span className="field__label">Source label</span>
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="resume">resume</option>
            <option value="rag_chatbot_readme">rag_chatbot_readme</option>
            <option value="tinify_readme">tinify_readme</option>
            <option value="onechat_readme">onechat_readme</option>
            <option value="internship_report">internship_report</option>
          </select>
        </label>

        <button className="btn" type="submit" disabled={!file || status === "uploading"}>
          {status === "uploading" ? "Processing…" : "Upload & embed"}
        </button>
      </form>

      {status === "done" && result && (
        <div className="upload-result">
          <p className="mono">
            {result.filename} → {result.chunks_stored} chunks stored
          </p>
          <ul className="upload-preview">
            {result.preview.map((p, i) => (
              <li key={i} className="mono">{p}…</li>
            ))}
          </ul>
        </div>
      )}

      {status === "error" && (
        <p className="upload-error">Upload failed: {error}</p>
      )}
    </div>
  );
}
