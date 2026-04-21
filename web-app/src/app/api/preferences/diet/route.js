import { handleAuthedProxy } from "../../../../lib/authedRoute";

export async function POST(request) {
  return handleAuthedProxy(request, "/preferences/diet");
}

export async function DELETE(request) {
  return handleAuthedProxy(request, "/preferences/diet");
}
