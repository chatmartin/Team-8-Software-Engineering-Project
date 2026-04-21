import { handleAuthedProxy } from "../../../../lib/authedRoute";

export async function POST(request) {
  return handleAuthedProxy(request, "/preferences/sensitivity");
}

export async function PUT(request) {
  return handleAuthedProxy(request, "/preferences/sensitivity");
}

export async function DELETE(request) {
  return handleAuthedProxy(request, "/preferences/sensitivity");
}
