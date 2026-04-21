import { handleAuthedProxy } from "../../../../lib/authedRoute";

export async function GET(request) {
  return handleAuthedProxy(request, "/admin/users");
}
