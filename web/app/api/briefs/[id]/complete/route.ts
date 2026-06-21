import { proxyWithToken } from "@/lib/server-auth";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  return proxyWithToken(`/api/v1/briefs/${id}/complete`, request, "POST");
}
