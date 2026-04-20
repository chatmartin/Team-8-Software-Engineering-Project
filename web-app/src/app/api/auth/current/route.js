import { getSessionUser } from "../../../../lib/session";

export async function GET() {
  const username = await getSessionUser();
  if (!username) {
    return Response.json(
      { success: false, message: "Not authenticated.", data: null },
      { status: 401 }
    );
  }
  return Response.json({
    success: true,
    message: "Current user obtained successfully.",
    data: { username },
  });
}
