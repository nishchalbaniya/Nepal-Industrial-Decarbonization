# Pilot Deployment Guide
## Nepal Industrial Decarbonization Platform v1.0.0

**For:** Cement plant managers, brick kiln operators, MRV project developers, system integrators
**Version:** 1.0.0
**Date:** 2026-07-21
**Author:** Nishchal Baniya, Himalayan Space Solutions
**Email:** nishchal.baniya@himalayancarbonnepal.com

---

## 1. Pilot deployment overview

This guide covers deploying `nepal_decarb_pro` v1.0.0 for a **pilot project** at a
cement plant or brick kiln in Nepal. The pilot can be:

- **Single-plant pilot:** one cement plant (e.g., PlantA) or one brick cluster
- **Sector pilot:** all plants in one Nepali province
- **Carbon credit pilot:** one project submitted to Verra/Gold Standard

### What's included in the pilot
- ✅ Real-time emissions monitoring via MQTT
- ✅ Verra/Gold Standard PDD generation
- ✅ ISO 14064-1/2/3 compliance checking
- ✅ TCFD/SBTi reporting
- ✅ Operator training simulator
- ✅ Bilingual UI (English + Nepali)
- ✅ Carbon credit tokenization (Solidity contract)
- ✅ Multi-tenant audit trail
- ✅ Production deployment (Docker Compose)

### What's needed for pilot
- **Hardware:** 1 server (8 GB RAM, 50 GB SSD) OR cloud VM
- **Network:** Internet for updates, optional MQTT broker
- **Personnel:** 1 plant engineer (part-time), 1 IT admin (deployment)
- **Optional sensors:** Temperature, pressure, flow, gas composition

### Pilot timeline
- **Week 1:** Deployment + integration with existing data sources
- **Week 2:** Sensor installation (if any)
- **Week 3-4:** Operator training
- **Week 5-8:** Monitoring + baseline verification
- **Week 9-12:** Project scenario testing + PDD generation
- **Week 13-16:** Verra/Gold Standard submission preparation

---

## 2. Deployment options

### Option A: Docker Compose (recommended for pilot)

```bash
# Clone
git clone https://github.com/<your-org>/nepal-decarb.git
cd nepal-decarb/pro

# Configure
cp .env.example .env
# Edit .env with your settings (database path, secret key, MQTT broker, etc.)

# Build and start
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs web

# Access
# Streamlit UI:  http://localhost:8501
# FastAPI:       http://localhost:8000/docs
# MQTT broker:   localhost:1883
```

### Option B: Kubernetes (for production-grade)

```bash
# Add Helm repo
helm repo add nepal-decarb https://himalayancarbon.github.io/nepal-decarb

# Install
helm install nepal-decarb nepal-decarb/nepal-decarb \
    --set image.tag=1.0.0 \
    --set mqtt.broker=mqtts://your-broker.com:8883 \
    --set persistence.size=100Gi

# Check
kubectl get pods
kubectl get svc
```

### Option C: Local Python install

```bash
# Install
git clone https://github.com/<your-org>/nepal-decarb.git
cd nepal-decarb/pro
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"

# Run components
streamlit run app/Home.py &        # UI on :8501
python -m nepal_decarb_pro.api &   # API on :8000
python -m nepal_decarb_pro.io.mqtt_bridge &  # MQTT bridge
```

---

## 3. Configuration

### Environment variables (`.env`)

```bash
# Required
NEPAL_DECARB_SECRET=<random-256-bit-key>
NEPAL_DECARB_DB=/var/lib/nepal-decarb/nepal_decarb.db

# Optional
MQTT_BROKER=mqtt://localhost:1883
MQTT_USERNAME=plant
MQTT_PASSWORD=***
LOG_LEVEL=INFO
PLANT_NAME=PlantA Industries Ltd
TENANT_ID=default
```

### MQTT topic structure (for sensor integration)

```
nepal/<plant_id>/kiln/temperature      # burning zone T
nepal/<plant_id>/kiln/o2               # O2 %
nepal/<plant_id>/kiln/co               # CO ppm
nepal/<plant_id>/kiln/nox              # NOx ppm
nepal/<plant_id>/kiln/dust             # mg/Nm3
nepal/<plant_id>/cooler/clinker_temp   # discharged clinker T
nepal/<plant_id>/mill/power            # kW
nepal/<plant_id>/mill/throughput       # t/h
```

Payload format:
```json
{"value": 1450, "unit": "C", "quality": 0.95, "timestamp": "2026-07-21T12:00:00"}
```

---

## 4. First-week checklist

- [ ] Server provisioned (8 GB RAM, 50 GB SSD)
- [ ] Docker Compose stack running
- [ ] Streamlit UI accessible
- [ ] FastAPI returning 200 on `/health`
- [ ] Database created and tenants seeded
- [ ] Initial API token issued
- [ ] First cement plant data loaded (PlantA or your plant)
- [ ] First baseline calculation run and verified
- [ ] ISO 14064-1 compliance check run
- [ ] PDF report generated and reviewed
- [ ] MQTT broker running (if sensors deployed)
- [ ] User accounts created with appropriate roles
- [ ] Backup configured

---

## 5. Day-2 onwards

### What to do daily
1. Check `/v1/audit` for activity log
2. Verify MQTT bridge is receiving sensor data
3. Run `nepal-decarb cement` CLI for spot-checks
4. Review any anomalies from digital twin
5. Update plant operating data

### What to do weekly
1. Re-run baseline calculation
2. Generate Verra monitoring report (if crediting period active)
3. Review TCFD disclosure with management
4. Update SBTi targets (if interim year)

### What to do monthly
1. Update fuel prices (in `data/emission_factors.yaml`)
2. Review NEA grid factor (annual update)
3. Generate executive summary PDF
4. Audit user access

---

## 6. Scaling from pilot to production

When the pilot proves out, scale to:
- **Multiple plants:** each plant gets its own tenant in multi-tenant DB
- **Higher sensor rate:** upgrade MQTT broker to Mosquitto cluster
- **Real-time dashboards:** Streamlit + WebSocket
- **Mobile apps:** FastAPI endpoints already JSON-based
- **Carbon credit issuance:** deploy Solidity contract on Polygon/Arbitrum
- **Audit firm integration:** ISO 14064-3 verifier gets read-only API access

---

## 7. Troubleshooting

### Common issues

| Issue | Resolution |
|---|---|
| `ModuleNotFoundError: nepal_decarb_pro` | Run `pip install -e ".[full]"` |
| `MQTT connection refused` | Check broker URL, firewall, credentials |
| `Database is locked` | Reduce concurrent writes; check for stale connections |
| `Pydantic validation error` | Check API request body matches Pydantic schema |
| `Out of memory on Monte Carlo` | Reduce n_samples (e.g., 1000 instead of 5000) |
| `Solc not found` | Install via `npm install -g solc` or use Foundry |

### Logs

```bash
# Docker Compose
docker-compose logs -f web
docker-compose logs -f api
docker-compose logs -f mqtt-bridge

# Kubernetes
kubectl logs -f deployment/nepal-decarb-web
kubectl logs -f deployment/nepal-decarb-api

# Local
# Logs go to stdout
```

---

## 8. Support & maintenance

- **Email:** nishchal.baniya@himalayancarbonnepal.com
- **GitHub Issues:** https://github.com/<your-org>/nepal-decarb/issues
- **Documentation:** `/docs` in the repository
- **Updates:** Quarterly releases (LTS) + monthly patches

---

## 9. Compliance & regulatory

This software supports:
- ✅ Verra VCS project registration & monitoring
- ✅ Gold Standard project registration & monitoring
- ✅ EU CBAM (Carbon Border Adjustment Mechanism) reporting
- ✅ Nepal Climate Change Policy 2025
- ✅ Nepal NDC reporting to UNFCCC
- ✅ SBTi target submission
- ✅ TCFD disclosure (e.g., for SEBON in Nepal)
- ✅ ISO 14064-1, -2, -3 audits
- ✅ ISO 14001, ISO 50001 management systems

---

**Ready to deploy?** See [`OPERATOR_MANUAL.md`](OPERATOR_MANUAL.md) and [`COMMISSIONING.md`](COMMISSIONING.md).
