const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

// The hosted backend (Render) saves times in UTC but older rows have no timezone marker,
// so the browser reads them as local time and shows the wrong hour.
// When talking to the hosted backend, treat marker-less times as UTC.
const HAS_TZ = /[zZ]$|[+-]\d{2}:?\d{2}$/;

function fixTime(value) {
  if (!BASE || typeof value !== "string" || HAS_TZ.test(value)) return value;
  return `${value}Z`;
}

function fixTimes(data) {
  if (Array.isArray(data)) return data.map(fixTimes);
  if (data && typeof data === "object") {
    return { ...data, created_at: fixTime(data.created_at) };
  }
  return data;
}

async function call(path, opts) {
  const res = await fetch(`${BASE}/api${path}`, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return fixTimes(await res.json());
}

export const generateBriefing = () => call("/generate", { method: "POST" });
export const listBriefings = () => call("/briefings");
export const getBriefing = (id) => call(`/briefings/${id}`);
export const getSources = () => call("/sources");
