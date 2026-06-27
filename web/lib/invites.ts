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
  upstream_state: string;
  downstream_state: string | null;
  priority: string;
  created_by_id: string;
  created_by_name: string;
  assigned_to_id: string | null;
  assigned_to_name: string | null;
  status_changed_by_id: string;
  status_changed_by_name: string;
  status_changed_at: string;
  estimated_man_days: number | null;
  expected_completion_at: string | null;
  current_version: number | null;
  current_version_status: string | null;
  version: number;
  is_current: boolean;
  attachments: unknown[];
  created_at: string;
  updated_at: string;
}

export interface BriefTransfer {
  id: string;
  brief_version: number;
  from_user_id: string;
  from_user_name: string;
  to_user_id: string;
  to_user_name: string;
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

export interface BlockInviteRequest {
  reason: string;
}

export interface SubmitInviteRequest {
  content: string;
}

export interface OpenInviteRequest {
  reason: string;
}

export interface DelegateInviteRequest {
  content?: string;
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

export async function blockInvite(token: string, body: BlockInviteRequest) {
  return apiFetch<{ id: string; type: string; content: string; from_user: UserRef; created_at: string }>(
    `/api/invites/${token}/block`,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
}

export async function submitInvite(token: string, body: SubmitInviteRequest) {
  return apiFetch<{ id: string; type: string; content: string; from_user: UserRef; created_at: string }>(
    `/api/invites/${token}/submit`,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
}

export async function openInvite(token: string, body: OpenInviteRequest) {
  return apiFetch<BriefDetail>(`/api/invites/${token}/open`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function delegateInvite(token: string, body?: DelegateInviteRequest) {
  return apiFetch<BriefDetail>(`/api/invites/${token}/delegate`, {
    method: "POST",
    body: JSON.stringify(body ?? {}),
  });
}

export async function getInviteTransfers(token: string) {
  return apiFetch<Transfer[]>(`/api/invites/${token}/transfers`);
}

export async function getInviteFeedbacks(token: string) {
  return apiFetch<Feedback[]>(`/api/invites/${token}/feedbacks`);
}

export async function sendBrief(briefId: string, body: SendBriefRequest) {
  return apiFetch<SendBriefResponse>(`/api/briefs/${briefId}/transfer?action=send`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
