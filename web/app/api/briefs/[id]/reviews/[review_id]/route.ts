import { proxyWithToken } from "@/lib/server-auth";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string; review_id: string }> }
) {
  const { id, review_id } = await params;
  return proxyWithToken(`/api/v1/briefs/${id}/reviews/${review_id}`, _request, "GET");
}
