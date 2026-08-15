import Link from "next/link";
import { api, qs } from "@/lib/api";
import { ScopeBar, scopeFrom } from "../scope";

type PacketItem = { id: string; statement: string; polarity?: string; authority?: string };

export default async function ContextPage({
  searchParams,
}: {
  searchParams: Promise<{ org?: string; repo?: string }>;
}) {
  const sp = await searchParams;
  const { org, repo } = scopeFrom(sp);
  let packet: { pin?: PacketItem[]; decide?: PacketItem[]; error?: string } = {};
  let error = "";
  try {
    packet = await api(`/v1/context?${qs(org, repo)}`);
  } catch (e) {
    error = e instanceof Error ? e.message : "API down";
  }
  const pin = packet.pin || [];
  const decide = packet.decide || [];

  return (
    <div>
      <h1>Active context</h1>
      <p className="muted">Boot packet. <code>must_not</code> pins first. Pending never appears.</p>
      <ScopeBar org={org} repo={repo} />
      {error ? <p className="error">{error}</p> : null}
      {!error && pin.length + decide.length === 0 ? <p className="muted">Empty brain for this org/repo.</p> : null}
      <h2>Pin (must_obey)</h2>
      {pin.map((item) => (
        <article className="card" key={item.id}>
          <span className={`badge ${item.polarity}`}>{item.polarity}</span>{" "}
          <Link href={`/memories/${item.id}?org=${org}&repo=${repo}`}>{item.statement}</Link>
        </article>
      ))}
      <h2>Decide</h2>
      {decide.map((item) => (
        <article className="card" key={item.id}>
          <span className={`badge ${item.polarity}`}>{item.polarity}</span>{" "}
          <Link href={`/memories/${item.id}?org=${org}&repo=${repo}`}>{item.statement}</Link>
        </article>
      ))}
    </div>
  );
}
