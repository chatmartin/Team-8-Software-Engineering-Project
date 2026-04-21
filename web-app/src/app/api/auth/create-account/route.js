import { NextResponse } from "next/server";

import { proxyToFlask } from "../../../../lib/backendProxy";
import { setSessionCookie } from "../../../../lib/session";

export async function POST(request) {
  try {
    const body = await request.json();
    const { status, json } = await proxyToFlask("/create_acc", {
      username: body?.username ?? "",
      password: body?.password ?? "",
      email: body?.email ?? "",
    });

    const response = NextResponse.json(json, { status });
    if (json.success && json.data?.username) {
      setSessionCookie(response, json.data.username);
    }
    return response;
  } catch {
    return NextResponse.json(
      {
        success: false,
        message: "Backend connection failed. Start Flask service first.",
        data: null,
      },
      { status: 502 }
    );
  }
}
