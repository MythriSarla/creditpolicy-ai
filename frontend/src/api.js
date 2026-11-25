const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function call(path, opts) {
  const res = await fetch(`${BASE}/api${path}`, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const generateBriefing = () => call("/generate", { method: "POST" });
export const listBriefings = () => call("/briefings");
export const getBriefing = (id) => call(`/briefings/${id}`);
export const getSources = () => call("/sources");

