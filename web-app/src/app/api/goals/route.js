import { handleAuthedProxy } from "../../../lib/authedRoute";

export async function GET(request) {
  return handleAuthedProxy(request, "/goals");
}

export async function POST(request) {
  return handleAuthedProxy(request, "/goals");
}

export async function PUT(request) {
  return handleAuthedProxy(request, "/goals");
}

export async function DELETE(request) {
  return handleAuthedProxy(request, "/goals");
}
