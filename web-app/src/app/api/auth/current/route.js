import { getSessionUser } from "../../../../lib/session";
import { proxyToFlask } from "../../../../lib/backendProxy";

export async function GET() {
  const username = await getSessionUser();
  if (!username) {
    return Response.json(
      { success: false, message: "Not authenticated.", data: null },
      { status: 401 }
    );
  }

  try {
    const { status, json } = await proxyToFlask("/current_user", { username }, "GET");
    return Response.json(json, { status });
  } catch {
    return Response.json(
      {
        success: true,
        message: "Current user obtained from session.",
        data: { username, role: "user" },
      },
      { status: 200 }
    );
  }
}
