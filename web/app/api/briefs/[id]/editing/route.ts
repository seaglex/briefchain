import { proxyWithToken } from "@/lib/server-auth";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action");
  return proxyWithToken(`/api/v1/briefs/${id}/editing?action=${action}`, request, "POST");
}
