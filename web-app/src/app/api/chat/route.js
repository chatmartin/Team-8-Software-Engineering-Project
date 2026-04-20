import { handleAuthedProxy } from "../../../lib/authedRoute";

export async function POST(request) {
  return handleAuthedProxy(request, "/chat");
}
