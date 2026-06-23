import { getInviteBriefId, proxyWithoutToken } from "@/lib/server-auth";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params;
  const briefId = await getInviteBriefId(token);
  if (!briefId) {
    return Response.json(
      { error: { code: "INVITE_INVALID", message: "邀请无效或已过期" } },
      { status: 401 }
    );
  }
  return proxyWithoutToken(`/api/v1/briefs/${briefId}/feedbacks`, request, "GET");
}
