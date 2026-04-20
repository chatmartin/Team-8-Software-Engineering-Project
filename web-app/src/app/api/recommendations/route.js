import { handleAuthedProxy } from "../../../lib/authedRoute";

export async function GET(request) {
  return handleAuthedProxy(request, "/recommendations");
}

export async function POST(request) {
  return handleAuthedProxy(request, "/recommendations");
}
