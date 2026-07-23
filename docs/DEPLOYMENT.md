# Deployment Guide

> **Status (2026-07-23):** This document is the single entry
> point for deploying the Nepal Industrial Decarbonization
> Platform. The deployment story spans five layers, each
> with its own configuration: the root `Dockerfile` (FastAPI
> server), the `pro/Dockerfile` (Streamlit dashboard), the
> `pro/deploy/vps/` tree (VPS turnkey), the `pro/deploy/one-click/`
> tree (free cloud), and the GitHub Actions CI (Pages deploy).

---

## 1. The five deploy paths

| Path | Cost | Time to live | When to use |
|---|---|---|---|
| **VPS one-command** (pro/deploy/vps/) | $20/mo | 5 min | Pilot, single plant, NCMA cohort (1-20 plants) |
| **AWS Terraform** (pro/deploy/terraform/) | ~$150/mo | 30 min | National rollout, 20-500 plants |
| **GPU + vLLM** (pro/deploy/vllm/) | +$0.60/hr | 15 min | LLM advisor at scale (50+ concurrent users) |
| **Free one-click** (pro/deploy/one-click/) | Free tier | 5 min | Demo / hackathon / low-traffic |
| **GitHub Pages** (auto) | Free | 1 min | Static demo, 4-plant e2e, no backend |

The first three are production paths. The fourth and fifth
are demo paths. The static demo at
https://jfp4xr4woteju.space.minimax.io is the current
end-to-end demo; the GitHub Pages site
(https://nishchalbaniya.github.io/Nepal-Industrial-Decarbonization/)
is the keeper.

---

## 2. The VPS path (most common, for a pilot)

This is the path the user used for the v1.0.0 plant pilot
deployment. The .lnk shortcuts on the Windows Desktop
(`NepalDecarb Dashboard.lnk`, `NepalDecarb Run Demo.lnk`,
`NepalDecarb Uninstall.lnk`) all call into this path.

### Server-side (Ubuntu 22.04 in Mumbai region)

```bash
# On a fresh VPS as root
DOMAIN=carbon.example.com ADMIN_EMAIL=ops@example.com \
  bash <(curl -sSL https://raw.githubusercontent.com/nishchalbaniya/Nepal-Industrial-Decarbonization/main/pro/deploy/vps/deploy.sh)
```

This installs:
- PostgreSQL 15 (for the `nepal_decarb_pro.core.audit` trail
  and the multi-tenant plant registry)
- Mosquitto MQTT (for the IoT / `pro/nepal_decarb_pro/io/mqtt_bridge.py`)
- Prometheus + Grafana (for the cooler / kiln sensor dashboards)
- The FastAPI server (`uvicorn nepal_decarb_pro.api:app --host 0.0.0.0 --port 8000`)
- The Streamlit dashboard (`streamlit run app/Home.py --server.port=8501`)
- Caddy as reverse proxy (auto-TLS via Let's Encrypt)

### Client-side (Windows)

1. Double-click `C:\Users\TG\Desktop\NepalDecarb Dashboard.lnk`.
   The .vbs launcher sets `NEPAL_DECARB_ROOT` in HKCU\Environment
   and starts the FastAPI server in a hidden cmd window.
2. Browser opens to `http://127.0.0.1:8000/` (the dashboard).
3. To remove: double-click `C:\Users\TG\Desktop\NepalDecarb
   Uninstall.lnk`.

The .lnk magic header byte is `0x4C` ('L') per `[MS-SHLLINK]`.
The shortcuts are written via WScript.Shell COM (Windows
Script Host), so they require no Python runtime to launch.

---

## 3. The Docker path (any machine)

```bash
# Clone the repo
git clone https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization.git
cd Nepal-Industrial-Decarbonization

# Build the root image (FastAPI server, single stage)
docker build -t nepal-decarb:dev .

# Run on port 8000
docker run -p 8000:8000 nepal-decarb:dev
# -> http://localhost:8000/docs (Swagger UI)

# Or the pro/Dockerfile (multi-stage, Streamlit on 8501)
cd pro
docker build -t nepal-decarb-pro:dev -f Dockerfile .
docker run -p 8501:8501 -p 8000:8000 nepal-decarb-pro:dev
# -> http://localhost:8501/ (dashboard)
# -> http://localhost:8000/docs (API)
```

Health check: `curl http://localhost:8000/api/status`.

---

## 4. The free one-click path (demo, hackathon, low traffic)

The three configs at `pro/deploy/one-click/` are minimal
manifests for free cloud providers. They are **unmaintained**
in the sense that the WP0 ground-truth audit noted, but they
do still work for a low-traffic demo.

| Service | What you get | Cost | How |
|---|---|---|---|
| **GitHub Pages** (auto) | Static demo + downloadable reports | Free | Push to main; .github/workflows/release.yml deploys |
| **Render.com** | FastAPI + Postgres + static site, from `render.yaml` | Free tier | Click "Apply" at https://render.com/deploy?repo=https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization |
| **Railway.app** | Docker-based, $5/mo credit | Free trial | `railway up` after `railway link` |
| **Fly.io** | 3 shared VMs free | Free tier | `fly launch` then `fly deploy` |

The current live demos are:
- `https://jfp4xr4woteju.space.minimax.io` (end-to-end 4-plant)
- `https://nishchalbaniya.github.io/Nepal-Industrial-Decarbonization/` (GitHub Pages, keeper)

The previous demo URLs (fnj58e5yu30lp.space.minimax.io and
harvey-aside-striking-spas.trycloudflare.com) are dead and were
removed from the README in WP3.

---

## 5. The Kubernetes path (AWS, multi-region)

For 20-500 plants with a regional multi-tenant deployment:

```bash
cd pro/deploy/terraform
terraform init
terraform plan -var-file=prod.tfvars
terraform apply
```

This creates:
- EKS cluster with 3-9 worker nodes (autoscaling)
- RDS Postgres 15
- ALB for the FastAPI + Streamlit endpoints
- CloudFront for the static assets
- S3 bucket for the CAD / P&ID / JSON artifacts
- IAM roles for the GitHub Actions OIDC deployment

Then:
```bash
cd pro/deploy/helm
helm install nepal-decarb .
```

This deploys:
- The FastAPI server (3 replicas)
- The Streamlit dashboard (2 replicas)
- The MQTT bridge (1 replica)
- The digital twin (1 replica)
- The LLM advisor (1 GPU pod, if vLLM is enabled)

---

## 6. The IoT edge path (ESP32 firmware)

For a plant that wants real-time sensor ingestion:

```bash
# Flash the ESP32 firmware (in pro/firmware/)
cd pro/firmware/esp32_cooler_sensor
arduino-cli compile --fqbn esp32:esp32:esp32 .
arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32 .

# The firmware publishes to the MQTT bridge:
# - DHT22 (ambient T, RH)
# - MQ-7 (CO, kiln exhaust)
# - MQ-135 (NH3, NOx)
# - MAX31855 (Type-K thermocouple, kiln shell T)
```

The MQTT bridge (`pro/nepal_decarb_pro/io/mqtt_bridge.py`)
subscribes to the `nepal_decarb/+/+/+` topic pattern and writes
to the audit log + the digital twin.

---

## 7. The CI / CD path (GitHub Actions)

`.github/workflows/ci.yml` runs the full pytest on Python
3.11 and 3.12 on every push and PR.

`.github/workflows/release.yml` (pre-existing) builds and
publishes a Docker image on every `v*` tag.

To release v1.0.0:
```bash
git tag v1.0.0-credible
git push origin v1.0.0-credible
```

This triggers the release workflow and pushes the image to
GitHub Container Registry (ghcr.io).

---

## 8. What this document does NOT cover

- **A real plant on-boarding**: that's a separate document
  (pro/docs/PLANT_ONBOARDING.md, 7 steps, not yet written).
- **A VVB engagement**: that's a separate process
  (docs/METHODOLOGY.md section 5, 8 missing Verra VCS sections).
- **A real PDD submission**: see the gap list in
  docs/METHODOLOGY.md section 5. The current PDD generator
  is a sizing tool, not submittable.

The deployment story is the easy part. The hard part is
turning the sizing output into a real registry submission,
and that is the next quarter's work.
