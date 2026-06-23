import { proxyWithoutToken } from "@/lib/server-auth";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  return proxyWithoutToken(`/api/v1/invites/${token}`, request, "GET");
}
