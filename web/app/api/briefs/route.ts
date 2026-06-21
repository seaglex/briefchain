import { proxyWithToken } from "@/lib/server-auth";

export async function POST(request: Request) {
  return proxyWithToken("/api/v1/briefs", request);
}
