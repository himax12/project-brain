import { api } from "@/lib/api";
import { ScopeBar, scopeFrom } from "../scope";

export default async function RecallPage({
  searchParams,
}: {
  searchParams: Promise<{ org?: string; repo?: string; q?: string }>;
}) {
  const sp = await searchParams;
  const { org, repo } = scopeFrom(sp);
  const q = sp.q || "";
  let packet: unknown = null;
  let error = "";
  if (q) {
    try {
      packet = await api("/v1/recall", {
        method: "POST",
        body: JSON.stringify({ org_id: org, repo_id: repo, query: q }),
      });
    } catch (e) {
      error = e instanceof Error ? e.message : "API down";
    }
  }
  return (
    <div>
      <h1>Recall playground</h1>
      <p className="muted">Authority packet: pin / decide / do_not_use — not a flat top-k list.</p>
      <ScopeBar org={org} repo={repo} />
      <form className="card" method="get">
        <input type="hidden" name="org" value={org} />
        <input type="hidden" name="repo" value={repo} />
        <label>
          query
          <input name="q" defaultValue={q} placeholder="Can we use Redis for billing cache?" />
        </label>
        <button type="submit">Recall</button>
      </form>
      {error ? <p className="error">{error}</p> : null}
      {packet ? <pre>{JSON.stringify(packet, null, 2)}</pre> : null}
    </div>
  );
}
