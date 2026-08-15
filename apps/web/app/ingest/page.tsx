import { ingestTranscript } from "@/lib/actions";
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
      <p className="muted">Lean E: you trigger extract. Candidates stay pending until confirm. Never silent-active.</p>
      <ScopeBar org={org} repo={repo} />
      <form
        className="card"
        action={async (form) => {
          "use server";
          await ingestTranscript(org, repo, String(form.get("transcript") || ""));
        }}
      >
        <label>
          transcript
          <textarea
            name="transcript"
            placeholder={"We decided Stripe retries go through the outbox.\nNever perform sync HTTP Stripe retries."}
            required
          />
        </label>
        <button type="submit">Extract to pending</button>
      </form>
    </div>
  );
}
