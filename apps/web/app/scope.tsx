export function ScopeBar({ org, repo }: { org: string; repo: string }) {
  return (
    <form className="row" method="get">
      <label>
        org
        <input name="org" defaultValue={org} />
      </label>
      <label>
        repo
        <input name="repo" defaultValue={repo} />
      </label>
      <button type="submit">Load</button>
    </form>
  );
}

export function scopeFrom(searchParams: { org?: string; repo?: string }) {
  return {
    org: searchParams.org || process.env.NEXT_PUBLIC_DEFAULT_ORG_ID || "acme",
    repo: searchParams.repo || process.env.NEXT_PUBLIC_DEFAULT_REPO_ID || "billing",
  };
}
