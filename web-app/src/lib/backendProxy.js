const FLASK_API_BASE_URL =
  process.env.FLASK_API_BASE_URL ?? "http://127.0.0.1:5000";

export async function proxyToFlask(path, payload, method = "POST") {
  const response = await fetch(`${FLASK_API_BASE_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  const json = await response.json();
  return { ok: response.ok, status: response.status, json };
}
