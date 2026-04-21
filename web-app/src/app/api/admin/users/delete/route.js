import { handleAuthedProxy } from "../../../../../lib/authedRoute";

export async function DELETE(request) {
  return handleAuthedProxy(request, "/admin/users/delete");
}
