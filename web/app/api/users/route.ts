import { proxyWithToken } from "@/lib/server-auth";

export async function GET(request: Request) {
  return proxyWithToken("/api/v1/users" + new URL(request.url).search, request, "GET");
}
