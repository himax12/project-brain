# Video shot list (< 3 minutes)

Do not use seed data. Empty cluster → real writes.

| t | Shot | Proof |
|---|---|---|
| 0:00 | Title: Project Brain — decisions in CockroachDB | Logo / README |
| 0:10 | Empty pending inbox + `SELECT count(*) FROM memories` | Empty brain |
| 0:25 | Remember “Never sync HTTP Stripe retries” (must_not) in UI or MCP | pending_review row |
| 0:45 | Confirm in Next.js | status=active, embedding not null |
| 1:05 | New Cursor chat: `get_context` | pin[0] is the never-rule |
| 1:25 | `/recall` “Can we retry Stripe over HTTP?” | packet pin/decide, not a flat list |
| 1:50 | Supersede to a new statement | old `invalid_at`; recall `do_not_use` |
| 2:10 | Cockroach **Managed MCP** `SELECT id, statement, status FROM memories WHERE status='active'` | CRDB is SoR |
| 2:35 | Name tools: VECTOR + Managed MCP + Bedrock Titan | Eligibility |
| 2:50 | End card: repo URL | Clone path |

Backup if Managed MCP flaky: Cockroach SQL shell same SELECT.
