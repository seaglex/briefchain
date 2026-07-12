import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

interface ReviewWebhookPayload {
  event: string;
  review_id: string;
  brief_id: string;
  status: string;
  score?: number | null;
  error?: string | null;
  timestamp?: string;
}

function isValidPayload(body: unknown): body is ReviewWebhookPayload {
  if (typeof body !== "object" || body === null) return false;
  const payload = body as Record<string, unknown>;
  return (
    typeof payload.event === "string" &&
    typeof payload.review_id === "string" &&
    typeof payload.brief_id === "string" &&
    typeof payload.status === "string"
  );
}

export async function POST(request: NextRequest) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: { code: "INVALID_JSON", message: "Invalid JSON payload" } },
      { status: 400 }
    );
  }

  if (!isValidPayload(body)) {
    return NextResponse.json(
      { error: { code: "INVALID_PAYLOAD", message: "Missing required webhook fields" } },
      { status: 400 }
    );
  }

  const terminalStatuses = ["passed", "rejected", "failed", "force_skipped"];
  if (!terminalStatuses.includes(body.status)) {
    return NextResponse.json(
      { error: { code: "INVALID_STATUS", message: "Not a terminal review status" } },
      { status: 400 }
    );
  }

  // Revalidate the brief detail page so the next visit sees the latest state.
  revalidatePath(`/briefs/${body.brief_id}`, "page");

  return NextResponse.json({ received: true, brief_id: body.brief_id, status: body.status });
}
