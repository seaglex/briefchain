import { proxyWithToken } from "@/lib/server-auth";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function PUT(request: Request, context: RouteParams) {
  const { id } = await context.params;
  return proxyWithToken(`/api/v1/comments/${id}`, request);
}

export async function DELETE(request: Request, context: RouteParams) {
  const { id } = await context.params;
  return proxyWithToken(`/api/v1/comments/${id}`, request);
}
