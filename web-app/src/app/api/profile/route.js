import { handleAuthedProxy } from "../../../lib/authedRoute";

export async function GET(request) {
  return handleAuthedProxy(request, "/profile");
}

export async function POST(request) {
  return handleAuthedProxy(request, "/profile");
}

export async function PUT(request) {
  return handleAuthedProxy(request, "/profile");
}
