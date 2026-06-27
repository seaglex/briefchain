import { proxyWithoutToken } from "@/lib/server-auth";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  return proxyWithoutToken(`/api/v1/invites/${token}/delegate`, request, "POST");
}
