# Agent access matrix (KUB-55)

Unattended access for the manager agent. No secrets in this file.

## SSH (key: `~/.ssh/homelab-agent`, config block in `~/.ssh/config`)

| Alias | Host | User | Notes |
|---|---|---|---|
| `px-cpu` | 10.10.101.11 | root | PVE node; key in cluster-wide `/etc/pve/priv/authorized_keys` |
| `px-net` | 10.10.101.12 | root | PVE node (same shared key file) |
| `px-nas` | 10.10.101.13 | root | PVE node (same shared key file) |
| `zima` / `pbs` | 10.10.10.34 | root | PBS host (hostname `kbs`); key in `/root/.ssh/authorized_keys` |
| `truenas` | 10.10.10.31 | kuba | passwordless sudo; key managed via TrueNAS middleware (user id 70 `sshpubkey`) — don't edit authorized_keys directly |

## API

| System | Auth | Secret location |
|---|---|---|
| TrueNAS REST v2.0 (`https://10.10.10.31/api/v2.0`) | `Authorization: Bearer <key>` | 1P Homelab `TRUENAS_AGENT_API_KEY` (api_key id 1, user kuba) |
| PBS API (`https://10.10.10.34:8007`) | ticket via `backup@pbs` | password: `/etc/pve/priv/storage/pbs-zima.pw` on any PVE node; root ssh preferred |
| PVE API | not provisioned | root ssh + `pvesh` covers it (YAGNI; add token when an MCP needs it) |
| Gotify (`https://gotify.lab.nobasura.org`) | `X-Gotify-Key: <token>` | 1P Homelab `AGENT_GOTIFY_TOKEN` (app "homelab-agent") |

## 1Password (non-interactive)

- Service account token: `~/.config/homelab-agent/op-token` (chmod 600)
- Usage: `OP_SERVICE_ACCOUNT_TOKEN=$(cat ~/.config/homelab-agent/op-token) op item get <ITEM> --vault Homelab --fields <FIELD> --reveal`
- Scope: **read-only**, Homelab vault only. Writes need the owner's desktop session (`op --account my.1password.com`).

## Escalation (agent blocked on owner)

```bash
GT=$(OP_SERVICE_ACCOUNT_TOKEN=$(cat ~/.config/homelab-agent/op-token) op item get AGENT_GOTIFY_TOKEN --vault Homelab --fields credential --reveal)
curl -sk -X POST https://gotify.lab.nobasura.org/message -H "X-Gotify-Key: $GT" \
  -H "Content-Type: application/json" \
  -d '{"title":"Agent blocked: KUB-XX","message":"<what is needed>","priority":8}' -o /dev/null
```

Park the blocked ticket in Linear with a comment, push Gotify, continue other work. Slack = secondary (not wired yet).
