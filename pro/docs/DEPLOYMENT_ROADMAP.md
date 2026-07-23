# Nepal-Wide Deployment Roadmap

> How to take `nepal_decarb_pro` from "works on my machine" to "every cement plant in Nepal uses it."

## The opportunity

**Cement industry in Nepal (2024 estimates):**
- ~150 cement plants, 95% small/medium (100-1000 TPD), 5% large (>1000 TPD)
- ~6 million tonnes CO₂/yr total emissions
- 3-5 plants cover 50% of emissions; the long tail is small plants
- ~5% have any kind of emissions accounting
- 0% have ISO 14064 / TCFD / SBTi compliance
- 0% participate in voluntary carbon markets

**Brick industry:**
- ~2000 brick kilns, mostly traditional clamp
- ~2 million tonnes CO₂/yr
- UNEP/GEF has been trying to migrate to zigzag for 20 years; success rate ~15%
- 0% have any kind of emissions accounting

**This platform = 100% open source + 100% free for the first 12 months + full ISO 14064 / TCFD / SBTi / Verra / GCCA compliance + bilingual UI + IoT integration + LLM advisor + carbon credit revenue**.

If we get 50% of cement plants onboarded = 3 Mt CO₂/yr under management, 200,000 Verra credits/yr, $6-15M/yr revenue for plants.

## Phased rollout

### Phase 0 — Soft launch (Month 1-2)
- Deploy to a $20/mo Hetzner VPS in Mumbai
- Single domain (nepalcarbon.org.np or similar)
- Onboard PlantA (already verified) as reference
- Onboard 5 friendly plants (NCMA intro)
- Total: 6 plants, ~3 Mt CO₂/yr under management

### Phase 1 — Pilot cohort (Month 3-6)
- 20 plants on the platform
- Free for the first 12 months (grant-funded)
- Each plant gets: 1 onboarding visit, 1 training session, 1 IoT sensor stack
- Total: 20 plants, ~4.5 Mt CO₂/yr

### Phase 2 — NCMA partnership (Month 6-12)
- Joint announcement with NCMA
- White-label option: "NCMA Carbon Platform"
- 50 plants on the platform
- Bulk onboarding via CSV (50 plants in 1 week)
- Government endorsement (Department of Environment)

### Phase 3 — National system (Year 2)
- All 150+ cement plants
- 200+ brick kilns (focus on the largest first)
- Connection to NEA grid EF (live update)
- Connection to NPL (Nepal Bureau of Standards) for verification
- Carbon credit registry integration (Verra API, GS API)

### Phase 4 — Regional (Year 3)
- Bangladesh, Sri Lanka, Bhutan (similar regulatory environments)
- Pakistan (much larger cement industry)

## Go-to-market strategy

### Free tier (default for everyone)
- 1 plant per tenant
- Up to 1 year of historical data
- All 11 standards reports
- Bilingual UI
- 50 API calls/day
- 1 user

### Pro tier ($50/mo per plant)
- Unlimited history
- IoT sensor integration
- Multi-user
- Alerting
- Priority support
- 5000 API calls/day

### Enterprise tier ($500/mo, 20+ plants)
- White-label
- SSO integration
- On-premise deployment option
- Custom integrations
- SLA: 99.9% uptime, 4-hour response
- Dedicated account manager

### Verifier / auditor tier ($100/mo)
- Time-limited read-only access to specific reports
- Audit trail
- ISO 14064-3 / 14065 compliant

### Government / NCMA (free)
- All Pro features
- Bulk onboarding tools
- Cross-plant benchmarking
- Public dashboard

## Funding model

- **Year 1**: Grant-funded (GIZ, GCF, World Bank)
- **Year 2**: 50% grant, 50% subscription
- **Year 3+**: 25% grant, 75% subscription + carbon credit commission
- **Carbon credit commission**: 5% of issued credit revenue (voluntary market norm)

## Operations

### Team (Year 1)
- 1 platform lead (Nishchal — full time)
- 2 backend engineers (full time)
- 1 frontend / Streamlit engineer (full time)
- 1 DevOps / SRE (part time)
- 2 plant onboarding specialists (each handles 50 plants/yr)
- 1 LLM/data scientist (part time, GPU)

### Tech stack
- **Compute**: Hetzner VPS ($20/mo) + AWS for HA
- **Database**: Postgres 15 with row-level security
- **Cache**: Redis 7
- **IoT**: Mosquitto MQTT + ESP32 sensors
- **API**: FastAPI + Uvicorn
- **UI**: Streamlit
- **LLM**: vLLM on a single A100 (when enabled)
- **Monitoring**: Prometheus + Grafana
- **Backups**: Daily pg_dump to S3 Glacier (90d)
- **SSL**: Let's Encrypt
- **DNS**: Cloudflare
- **CDN**: Cloudflare (free tier)

### SLAs
- API uptime: 99.5% (free) → 99.9% (pro) → 99.95% (enterprise)
- Support response: 24h (free) → 4h (pro) → 1h (enterprise)
- Data retention: 7 years (carbon credit audit requirement)
- Backup RTO: 4 hours, RPO: 24 hours

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Plants don't trust the data | Open source — anyone can audit the code |
| NCMA doesn't endorse | Direct outreach, demo with their data, free for members |
| Government doesn't adopt | Pilot with 2-3 plants first, build case studies |
| Funding runs out | Multiple grants + subscription + credit commission |
| Plants can't afford IoT | Manual data entry is fully supported |
| Nepal internet too slow | Streamlit works on 3G; offline data entry via mobile app (future) |
| Carbon prices collapse | Independent of credits — ISO 14064 / TCFD compliance is mandatory anyway |
| Cyberattack | Row-level security, audit log, encrypted backups, 2FA |

## Success metrics (Year 1)

- 20 plants onboarded
- 4.5 Mt CO₂/yr under management
- 50,000 Verra credits issued
- $1.5M revenue (credit commission + subscriptions)
- 5 ISO 14064-1 compliant audits completed
- 2 NCMA / government endorsements
- 1 journal paper published (methodology)

## Why this works

1. **Free for the user** (first 12 months) — removes the cost objection
2. **Open source** (MIT) — removes the trust objection
3. **Bilingual** (EN/NE) — removes the language barrier
4. **Standards-compliant** (11 standards) — makes it a no-brainer for verifiers
5. **Carbon credit revenue** — gives the plant a financial reason to participate
6. **Already proven** at PlantA — removes the "will it work?" objection
7. **Built for Nepal** (Nepali fuels, NEA grid EF, NCMA integration) — not a Western tool retrofitted

The only question is execution speed. Let's go.

---

*Last updated: 2026-07-22 — v1.1.0 of nepal_decarb_pro*
