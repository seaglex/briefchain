import { proxyWithToken } from "@/lib/server-auth";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyWithToken(`/api/v1/briefs/${id}/transfers`, request, "GET");
}
