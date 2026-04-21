const FLASK_API_BASE_URL =
  process.env.FLASK_API_BASE_URL ?? "http://127.0.0.1:5000";

export async function proxyToFlask(path, payload, method = "POST") {
  const upperMethod = method.toUpperCase();
  const url = new URL(`${FLASK_API_BASE_URL}${path}`);
  const options = {
    method: upperMethod,
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  };

  if (upperMethod === "GET") {
    Object.entries(payload ?? {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  } else {
    options.body = JSON.stringify(payload ?? {});
  }

  const response = await fetch(url, options);
  const text = await response.text();
  let json;
  try {
    json = text
      ? JSON.parse(text)
      : { success: response.ok, message: response.statusText, data: null };
  } catch {
    json = {
      success: false,
      message: `Backend returned a non-JSON ${response.status} response.`,
      data: null,
    };
  }

  return { ok: response.ok, status: response.status, json };
}

export async function readRequestJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}

export async function proxyAuthedToFlask(request, path, username) {
  const method = request.method.toUpperCase();
  const payload =
    method === "GET"
      ? Object.fromEntries(new URL(request.url).searchParams.entries())
      : await readRequestJson(request);

  const { status, json } = await proxyToFlask(
    path,
    { ...payload, username },
    method,
  );

  return Response.json(json, { status });
}
