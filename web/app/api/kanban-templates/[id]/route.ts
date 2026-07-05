import { proxyWithToken } from "@/lib/server-auth";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function GET(request: Request, context: RouteParams) {
  const { id } = await context.params;
  return proxyWithToken(`/api/v1/kanban-templates/${id}`, request);
}
