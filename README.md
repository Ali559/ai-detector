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
pnpm dev:ai          # AI service on :8000 (needs the venv below)
pnpm test:ai         # AI service unit tests
pnpm build           # build all JS packages
pnpm lint            # lint all JS packages
```

Run any package script with `pnpm --filter <name> <script>`, e.g. `pnpm --filter @ai-detector/extension test:unit`.

The Python service is managed separately. Set up its virtualenv once:

```sh
cd apps/ai_service
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
```

On first start it downloads about 4 GB of model weights into `apps/ai_service/weights/`. See [ARCHITECTURE.md](ARCHITECTURE.md) for how detection works, and [plans/](plans/README.md) for renting GPUs and training the models.

The API needs Postgres: set `DATABASE_URL` in `apps/api/.env` (see `.env.example`), then run `pnpm --filter @ai-detector/api db:migrate`. `docker-compose.yml` runs the API, AI service, Postgres and Redis together.

This project is licensed under the GNU Affero General Public License v3.0 – see the [LICENSE](LICENSE) file for details.
