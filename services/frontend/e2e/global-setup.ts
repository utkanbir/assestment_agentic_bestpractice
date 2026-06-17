const API_BASE = process.env.API_BASE ?? "http://localhost:8000/api/v1";

export default async function globalSetup() {
  const url = `${API_BASE}/question-bank/workstreams`;
  let res: Response;
  try {
    res = await fetch(url, { signal: AbortSignal.timeout(10_000) });
  } catch (err) {
    throw new Error(
      `API healthcheck failed: cannot reach ${url}. ` +
        `Start port-forward: kubectl port-forward -n aakp-information pod/<api-pod> 8000:8000\n` +
        `Error: ${err}`,
    );
  }
  if (!res.ok) {
    throw new Error(`API healthcheck failed: GET ${url} → ${res.status} ${res.statusText}`);
  }
  const workstreams = await res.json();
  if (!Array.isArray(workstreams) || workstreams.length === 0) {
    throw new Error(`API healthcheck failed: expected workstreams array from ${url}`);
  }
}
