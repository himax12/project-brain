import Link from "next/link";
import { api, qs } from "@/lib/api";
import { scopeFrom } from "../../scope";

export default async function MemoryPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ org?: string; repo?: string }>;
}) {
  const { id } = await params;
  const { org, repo } = scopeFrom(await searchParams);
  let row: Record<string, unknown> | null = null;
  let error = "";
  try {
    row = await api(`/v1/memories/${id}?${qs(org, repo)}`);
  } catch (e) {
    error = e instanceof Error ? e.message : "not found";
  }
  return (
    <div>
      <p>
        <Link href={`/pending?org=${org}&repo=${repo}`}>← pending</Link>
      </p>
      <h1>Memory</h1>
      {error ? <p className="error">{error}</p> : <pre>{JSON.stringify(row, null, 2)}</pre>}
      {row ? (
        <p>
          <Link href={`/memories/${id}/supersede?org=${org}&repo=${repo}`}>Supersede this decision</Link>
        </p>
      ) : null}
    </div>
  );
}
