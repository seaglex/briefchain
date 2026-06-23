import { apiFetch } from "./auth";
import type { Feedback, Transfer } from "@/components/BriefDetail";

export interface SendBriefRequest {
  is_temporary_user?: boolean;
  assigned_to?: string;
  recipient_name?: string;
  recipient_email?: string;
  recipient_phone?: string;
  note?: string;
}

export interface SendBriefResponse {
  brief: BriefDetail;
  transfer: BriefTransfer | null;
  invite?: InviteMetadata | null;
  message?: string | null;
}

export interface BriefDetail {
  brief_id: string;
  root_id: string;
  parent_id: string | null;
  title: string;
  content: string;
  status: string;
  priority: string;
  created_by: UserRef;
  assigned_to: UserRef | null;
  estimated_man_days: number | null;
  current_version: number;
  version: number;
  is_current: boolean;
  attachments: unknown[];
  created_at: string;
  updated_at: string;
}

export interface BriefTransfer {
  id: string;
  brief_version: number;
  from_user: UserRef;
  to_user: UserRef;
  sent_at: string;
  accepted_at: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
}

export interface UserRef {
  id: string;
  name: string;
}

export interface InviteMetadata {
  invite_url: string;
  accept_deadline: string;
  complete_deadline: string;
}

export interface InviteViewResponse {
  invite: {
    name: string;
    from_user: UserRef;
    accept_deadline: string;
    complete_deadline: string;
  };
  brief: BriefDetail;
}

export interface AcceptInviteRequest {
  name?: string;
}

export interface RejectInviteRequest {
  reason: string;
}

export interface BlockedInviteRequest {
  reason: string;
}

export interface DoneInviteRequest {
  result: string;
}

export async function getInvite(token: string) {
  return apiFetch<InviteViewResponse>(`/api/invites/${token}`);
}

export async function acceptInvite(token: string, body?: AcceptInviteRequest) {
  return apiFetch<SendBriefResponse>(`/api/invites/${token}/accept`, {
    method: "POST",
    body: JSON.stringify(body ?? {}),
  });
}

export async function rejectInvite(token: string, body: RejectInviteRequest) {
  return apiFetch<SendBriefResponse>(`/api/invites/${token}/reject`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function blockInvite(token: string, body: BlockedInviteRequest) {
  return apiFetch<{ id: string; type: string; content: string; from_user: UserRef; created_at: string }>(
    `/api/invites/${token}/blocked`,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
}

export async function doneInvite(token: string, body: DoneInviteRequest) {
  return apiFetch<{ id: string; type: string; content: string; from_user: UserRef; created_at: string }>(
    `/api/invites/${token}/done`,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
}

export async function getInviteTransfers(token: string) {
  return apiFetch<Transfer[]>(`/api/invites/${token}/transfers`);
}

export async function getInviteFeedbacks(token: string) {
  return apiFetch<Feedback[]>(`/api/invites/${token}/feedbacks`);
}

export async function sendBrief(briefId: string, body: SendBriefRequest) {
  return apiFetch<SendBriefResponse>(`/api/briefs/${briefId}/send`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
