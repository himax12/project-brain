import Link from "next/link";
import { api, qs } from "@/lib/api";
import { confirmMemory, rejectMemory, rememberMemory, resolveConflict } from "@/lib/actions";
import { ScopeBar, scopeFrom } from "../scope";

type Conflict = { id: string; statement?: string };
type Item = {
  id: string;
  statement: string;
  polarity: string;
  conflicts?: Conflict[];
  provenance?: { conflicts?: Conflict[] };
};

export default async function PendingPage({
  searchParams,
}: {
  searchParams: Promise<{ org?: string; repo?: string }>;
}) {
  const sp = await searchParams;
  const { org, repo } = scopeFrom(sp);
  let items: Item[] = [];
  let error = "";
  try {
    const data = await api<{ items: Item[] }>(`/v1/pending?${qs(org, repo)}`);
    items = data.items;
  } catch (e) {
    error = e instanceof Error ? e.message : "API down";
  }

  return (
    <div>
      <h1>Pending inbox</h1>
      <p className="muted">Confirm promotes to active (writes embedding). Reject drops the candidate.</p>
      <ScopeBar org={org} repo={repo} />
      <form
        className="card"
        action={async (form) => {
          "use server";
          await rememberMemory(
            org,
            repo,
            String(form.get("statement") || ""),
            String(form.get("polarity") || "must"),
          );
        }}
      >
        <label>
          New decision
          <textarea name="statement" placeholder="Never perform sync HTTP Stripe retries." required />
        </label>
        <div className="row">
          <label>
            polarity
            <select name="polarity" defaultValue="must">
              <option>must</option>
              <option>must_not</option>
              <option>advisory</option>
            </select>
          </label>
          <button type="submit">Remember (pending)</button>
        </div>
      </form>
      {error ? <p className="error">{error}. Is FastAPI running on :8000?</p> : null}
      {!error && items.length === 0 ? <p className="muted">Empty inbox. Save a decision above or via MCP.</p> : null}
      {items.map((item) => (
        <article className="card" key={item.id}>
          <div className="row">
            <span className={`badge ${item.polarity}`}>{item.polarity}</span>
            <Link href={`/memories/${item.id}?org=${org}&repo=${repo}`}>{item.id.slice(0, 8)}</Link>
          </div>
          <p>{item.statement}</p>
          {item.provenance?.conflicts?.length ? (
            <div>
              <p className="muted">Conflicts with active law — keep existing or switch.</p>
              {item.provenance.conflicts.map((c) => (
                <div className="row" key={c.id}>
                  <span className="muted">{c.statement || c.id}</span>
                  <form action={resolveConflict.bind(null, item.id, c.id, "keep_existing", org, repo)}>
                    <button type="submit">Keep existing</button>
                  </form>
                  <form action={resolveConflict.bind(null, item.id, c.id, "switch_to_pending", org, repo)}>
                    <button type="submit">Switch to this</button>
                  </form>
                </div>
              ))}
            </div>
          ) : null}
          <div className="row">
            <form action={confirmMemory.bind(null, item.id, org, repo)}>
              <button type="submit">Confirm</button>
            </form>
            <form action={rejectMemory.bind(null, item.id, org, repo)}>
              <button className="danger" type="submit">
                Reject
              </button>
            </form>
          </div>
        </article>
      ))}
    </div>
  );
}
