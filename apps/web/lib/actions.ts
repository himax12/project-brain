"use server";

import { revalidatePath } from "next/cache";
import { api, qs } from "./api";

export async function confirmMemory(id: string, org: string, repo: string) {
  await api(`/v1/memories/${id}/confirm?${qs(org, repo)}`, { method: "POST" });
  revalidatePath("/pending");
  revalidatePath("/context");
}

export async function rejectMemory(id: string, org: string, repo: string) {
  await api(`/v1/memories/${id}/reject?${qs(org, repo)}`, { method: "POST" });
  revalidatePath("/pending");
}

export async function supersedeMemory(
  id: string,
  org: string,
  repo: string,
  statement: string,
  polarity: string,
) {
  await api(`/v1/memories/${id}/supersede?${qs(org, repo)}`, {
    method: "POST",
    body: JSON.stringify({ statement, polarity }),
  });
  revalidatePath("/context");
  revalidatePath(`/memories/${id}`);
}

export async function rememberMemory(org: string, repo: string, statement: string, polarity: string) {
  await api("/v1/remember", {
    method: "POST",
    body: JSON.stringify({ org_id: org, repo_id: repo, statement, polarity }),
  });
  revalidatePath("/pending");
}

export async function ingestTranscript(org: string, repo: string, transcript: string) {
  await api("/v1/ingest_session", {
    method: "POST",
    body: JSON.stringify({ org_id: org, repo_id: repo, transcript, session_id: "ui" }),
  });
  revalidatePath("/pending");
}

export async function ingestLocalChat(org: string, repo: string, path: string) {
  await api("/v1/ingest_local_chat", {
    method: "POST",
    body: JSON.stringify({
      org_id: org,
      repo_id: repo,
      path: path || undefined,
    }),
  });
  revalidatePath("/pending");
}

export async function resolveConflict(
  pendingId: string,
  existingId: string,
  choice: "keep_existing" | "switch_to_pending",
  org: string,
  repo: string,
) {
  await api("/v1/resolve_conflict", {
    method: "POST",
    body: JSON.stringify({
      pending_id: pendingId,
      existing_id: existingId,
      choice,
      org_id: org,
      repo_id: repo,
    }),
  });
  revalidatePath("/pending");
  revalidatePath("/context");
}
