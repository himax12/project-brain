import { ingestLocalChat, ingestTranscript } from "@/lib/actions";
import { ScopeBar, scopeFrom } from "../scope";

export default async function IngestPage({
  searchParams,
}: {
  searchParams: Promise<{ org?: string; repo?: string }>;
}) {
  const sp = await searchParams;
  const { org, repo } = scopeFrom(sp);
  return (
    <div>
      <h1>Explicit ingest</h1>
      <p className="muted">
        Local chat (Cursor / Claude / GPT export) is evidence. Extract proposes pending
        decisions. Confirm in the inbox to make CockroachDB law.
      </p>
      <ScopeBar org={org} repo={repo} />
      <form
        className="card"
        action={async (form) => {
          "use server";
          await ingestLocalChat(org, repo, String(form.get("path") || ""));
        }}
      >
        <label>
          local chat path (.jsonl / .json / .txt) — empty = latest Cursor agent transcript
          <input name="path" placeholder="C:\Users\...\agent-transcripts\chat.jsonl" />
        </label>
        <button type="submit">Ingest local chat</button>
      </form>
      <form
        className="card"
        action={async (form) => {
          "use server";
          await ingestTranscript(org, repo, String(form.get("transcript") || ""));
        }}
      >
        <label>
          or paste transcript
          <textarea
            name="transcript"
            placeholder={"We decided Stripe retries go through the outbox.\nNever perform sync HTTP Stripe retries."}
            required
          />
        </label>
        <button type="submit">Extract paste to pending</button>
      </form>
    </div>
  );
}
