import { proxyAuthedToFlask } from "./backendProxy";
import { getSessionUser } from "./session";

export async function handleAuthedProxy(request, flaskPath) {
  const username = await getSessionUser();
  if (!username) {
    return Response.json(
      { success: false, message: "Not authenticated.", data: null },
      { status: 401 }
    );
  }

  try {
    return await proxyAuthedToFlask(request, flaskPath, username);
  } catch {
    return Response.json(
      {
        success: false,
        message: "Backend connection failed. Start Flask service first.",
        data: null,
      },
      { status: 502 }
    );
  }
}
