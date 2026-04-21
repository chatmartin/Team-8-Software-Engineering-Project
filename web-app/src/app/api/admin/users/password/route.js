import { handleAuthedProxy } from "../../../../../lib/authedRoute";

export async function PUT(request) {
  return handleAuthedProxy(request, "/admin/users/password");
}
