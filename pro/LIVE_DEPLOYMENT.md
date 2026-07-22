# LIVE DEPLOYMENT — current session

> Real, running deployment created in this session. URL expires when sandbox session ends.

## Public URLs

| Service | URL | Status |
|---|---|---|
| **Public demo site** | https://fnj58e5yu30lp.space.minimax.io | 🟢 LIVE |
| **Live API (FastAPI)** | https://harvey-aside-striking-spas.trycloudflare.com | 🟢 LIVE |
| API health | https://harvey-aside-striking-spas.trycloudflare.com/health | 🟢 200 |
| Swagger docs | https://harvey-aside-striking-spas.trycloudflare.com/docs | 🟢 200 |
| Hetauda baseline | https://harvey-aside-striking-spas.trycloudflare.com/pilot | 🟢 200 |
| Standards | https://harvey-aside-striking-spas.trycloudflare.com/standards | 🟢 200 |
| Kiln simulator | https://harvey-aside-striking-spas.trycloudflare.com/simulator/kiln | 🟢 200 |
| Brick simulator | https://harvey-aside-striking-spas.trycloudflare.com/simulator/brick | 🟢 200 |
| CAD parameters | https://harvey-aside-striking-spas.trycloudflare.com/cad/kiln | 🟢 200 |
| LLM advisor | https://harvey-aside-striking-spas.trycloudflare.com/advisor/ask (POST) | 🟢 200 |

## How it was deployed (this session)

1. **Installed `cloudflared`** — Cloudflare's tunnel binary, no account needed for quick tunnels
2. **Started FastAPI in this sandbox** — `nohup .venv_demo/bin/python scripts/serve_live.py > /tmp/fastapi.log 2>&1 &`
3. **Tunneled to public** — `nohup /tmp/cloudflared tunnel --url http://localhost:8000`
4. **Cloudflare gave us a public URL** — `harvey-aside-striking-spas.trycloudflare.com`
5. **Built an interactive HTML demo** at `site/index.html` that fetches the live API
6. **Deployed the HTML to the static site** — `fnj58e5yu30lp.space.minimax.io`

## What's running

- **FastAPI 1.1.2** with 8 endpoints (`/`, `/health`, `/pilot`, `/standards`, `/simulator/kiln`, `/simulator/brick`, `/cad/kiln`, `/advisor/ask`)
- **LLM advisor** (stub mode, bilingual EN/नेपाली)
- **Cloudflare tunnel** providing the public URL
- **Static site** with the interactive demo

## What's NOT running (could be added in 5-30 min)

- Streamlit UI (not started — would need port 8501 in the tunnel)
- Postgres (no DB needed for the read-only demo endpoints)
- MQTT broker (no IoT sensors attached)
- GPU vLLM (stub advisor works for demo)
- Grafana (no metrics to show in this demo)

## Try it yourself

```bash
# Health
curl https://harvey-aside-striking-spas.trycloudflare.com/health

# Pilot
curl https://harvey-aside-striking-spas.trycloudflare.com/pilot | jq

# Standards
curl https://harvey-aside-striking-spas.trycloudflare.com/standards | jq

# Ask the advisor in English
curl -X POST https://harvey-aside-striking-spas.trycloudflare.com/advisor/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Why is my CO2 high?","language":"en","baseline_2024":{"intensity_kg_per_t":783,"total_tco2":861025}}' | jq

# Ask in Nepali
curl -X POST https://harvey-aside-striking-spas.trycloudflare.com/advisor/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"किन CO2 बढी छ?","language":"ne","baseline_2024":{"intensity_kg_per_t":783,"total_tco2":861025}}' | jq
```

## Caveat

The `trycloudflare.com` URL is a "quick tunnel" — it has no uptime guarantee and Cloudflare reserves the right to investigate. For production, use a named tunnel with your own domain.

To replicate this on your NVIDIA machine:

```bash
# Install cloudflared
curl -fsSL -o /usr/local/bin/cloudflared \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x /usr/local/bin/cloudflared

# Start your platform
docker compose -f deploy/vps/docker-compose.yml up -d

# Tunnel to the world
cloudflared tunnel --url http://localhost:8000
# Cloudflare gives you a *.trycloudflare.com URL
```

For a permanent URL, create a named tunnel at `one.dash.cloudflare.com` (free), then point your own domain at it.
