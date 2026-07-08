const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore parse failure, fall back to statusText */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function uploadResume(file, source) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("source", source);
  const res = await fetch(`${API_BASE}/resume-upload`, {
    method: "POST",
    body: formData,
  });
  return handle(res);
}

export async function submitApplication({ company, role, jd_text }) {
  const res = await fetch(`${API_BASE}/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ company, role, jd_text }),
  });
  return handle(res);
}

export async function listApplications() {
  const res = await fetch(`${API_BASE}/applications`);
  return handle(res);
}

export async function getApplication(id) {
  const res = await fetch(`${API_BASE}/applications/${id}`);
  return handle(res);
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return handle(res);
}
