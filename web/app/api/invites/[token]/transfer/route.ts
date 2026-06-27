import { proxyWithoutToken } from "@/lib/server-auth";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action");
  return proxyWithoutToken(`/api/v1/invites/${token}/transfer?action=${action}`, request, "POST");
}
