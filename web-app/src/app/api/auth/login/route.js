import { proxyToFlask } from "../../../../lib/backendProxy";

export async function POST(request) {
  try {
    const body = await request.json();
    const { status, json } = await proxyToFlask("/login", {
      username: body?.username ?? "",
      password: body?.password ?? "",
    });

    return Response.json(json, { status });
  } catch {
    return Response.json(
      { message: "Backend connection failed. Start Flask service first." },
      { status: 502 }
    );
  }
}
