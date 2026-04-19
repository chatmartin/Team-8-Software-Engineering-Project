import { proxyToFlask } from "../../../../lib/backendProxy";

export async function POST(request) {
  try {
    const body = await request.json();
    const { status, json } = await proxyToFlask("/create_acc", {
      username: body?.username ?? "",
      password: body?.password ?? "",
      email: body?.email ?? "",
    });

    return Response.json(json, { status });
  } catch {
    return Response.json(
      { message: "Backend connection failed. Start Flask service first." },
      { status: 502 }
    );
  }
}
