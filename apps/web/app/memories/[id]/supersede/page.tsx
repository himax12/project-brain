import Link from "next/link";
import { supersedeMemory } from "@/lib/actions";
import { scopeFrom } from "../../../scope";

export default async function SupersedePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ org?: string; repo?: string }>;
}) {
  const { id } = await params;
  const { org, repo } = scopeFrom(await searchParams);
  return (
    <div>
      <p>
        <Link href={`/memories/${id}?org=${org}&repo=${repo}`}>← detail</Link>
      </p>
      <h1>Supersede</h1>
      <p className="muted">Old row becomes superseded with invalid_at. Recall puts it in do_not_use.</p>
      <form
        className="card"
        action={async (form) => {
          "use server";
          await supersedeMemory(
            id,
            org,
            repo,
            String(form.get("statement") || ""),
            String(form.get("polarity") || "must"),
          );
        }}
      >
        <label>
          replacement statement
          <textarea name="statement" required />
        </label>
        <label>
          polarity
          <select name="polarity" defaultValue="must">
            <option>must</option>
            <option>must_not</option>
            <option>advisory</option>
          </select>
        </label>
        <button type="submit">Replace</button>
      </form>
    </div>
  );
}
