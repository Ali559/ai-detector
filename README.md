# ai-detector (Work in progress)

Monorepo for the AI detector browser extension and its backend.

| Path | What | Stack |
| --- | --- | --- |
| `apps/extension` | Browser extension | Vue 3, Vite, Tailwind |
| `apps/api` | API server | Fastify, Drizzle, better-auth |
| `apps/ai_service` | Detection model service | Python |

## Setup

```sh
pnpm install
```

## Common scripts (run from the repo root)

```sh
pnpm dev:extension   # extension dev server
pnpm dev:api         # API in watch mode
pnpm build           # build all JS packages
pnpm lint            # lint all JS packages
```

Run any package script with `pnpm --filter <name> <script>`, e.g. `pnpm --filter @ai-detector/extension test:unit`.

The Python service is managed separately; see `apps/ai_service`. `docker-compose.yml` runs the API, AI service, Postgres and Redis together.

This project is licensed under the GNU Affero General Public License v3.0 – see the [LICENSE](LICENSE) file for details.
