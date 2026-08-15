# Threat model (short)

| Risk | Mitigation |
|---|---|
| Secrets stored as “memory” | Deny-list (`api_key`, `sk-`, `AKIA`, passwords) before insert |
| Wrong-memory / stale law | `pending_review` until confirm; supersede sets `invalid_at`; recall `do_not_use` |
| Cross-project leak | Every SQL path filters `org_id` + `repo_id`; boot/recall `status='active'` only |
| Silent junk from extract | Lean E: extract always pending; never auto-active |
| API abuse | `X-API-Key` on `/v1/*`; key stays server-side in Next.js |
| Multiplayer overwrite | Conflicts stay pending; `resolve_conflict` keep vs switch |

Not in MVP: production RLS roles, Clerk auth, encryption at rest beyond CRDB Cloud defaults.
