# Team Charter — Himalayan Space Solutions

> The team building `nepal_decarb_pro`. Single source of truth for roles, responsibilities, and decisions.

## Company

- **Name**: Himalayan Space Solutions
- **Mission**: Make every cement and brick plant in Nepal measure, reduce, and monetize their CO₂ emissions.
- **Vision**: A net-zero industrial Nepal by 2045, starting with cement and brick.
- **Founder**: Nishchal Baniya
- **Product**: `nepal_decarb_pro` (open-source platform)
- **Repo**: https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization

## Org structure (Month 1-3)

```
Nishchal Baniya
   FOUNDER
   Sales, partnerships, fundraising, customer success
   │
   ├── Mavis (AI Co-founder / CTO-as-a-service)
   │     Architecture, code review, deployment, automation
   │
   ├── Chemical Engineer (cement process)         [part-time, day 1]
   │     Domain accuracy, white paper, customer credibility
   │
   ├── Business Developer (sales/partnerships)   [part-time, day 1]
   │     Outreach, NCMA, DoE, first customer, grants
   │
   ├── Graphics Designer                          [project, day 1]
   │     Brand, pitch deck, marketing site
   │
   ├── Software Engineer (full-stack)             [month 2]
   │     Production hardening, multi-tenant, performance
   │
   ├── Environmental Engineer (compliance)        [month 2]
   │     ISO 14064, Verra, VVB liaison
   │
   ├── AI/ML Engineer (LLM advisor)               [month 3, when LLM needed]
   │     Fine-tuning Qwen on Nepali industrial data
   │
   ├── Data Engineer (DB + IoT)                   [month 3]
   │     Postgres + time-series + MQTT + Grafana
   │
   └── Marketing Lead                             [month 3]
         Content, social, email, PR
```

## Roles & deliverables (first 90 days)

### Nishchal (Founder)
- Owns: sales, partnerships, fundraising, customer relationships
- Weekly: 5 customer calls, 2 partnership meetings, 1 grant application
- Monthly: 1 customer onboarding, 1 revenue event

### Chemical Engineer
- Owns: cement/brick domain accuracy, customer credibility, white paper
- Week 1: Audit cement model accuracy (Tier 2/3) vs. NEA/ICEM data
- Week 2: Audit brick kiln model vs. UNEP/GEF reference
- Week 3: Co-author "Hetauda Cement Decarbonization" technical paper
- Week 4: Customer-facing FAQ + technical FAQ

### Business Developer
- Owns: revenue, partnerships, market intelligence
- Week 1: Identify 50 qualified leads (cement + brick)
- Week 2: Send 50 personalized emails (use OUTREACH.md)
- Week 3: Book 10 discovery calls
- Week 4: Close 1 free PoC, submit 1 grant application

### Graphics Designer
- Owns: brand, pitch, marketing collateral
- Week 1: Logo + color palette + typography
- Week 2: Pitch deck (10-15 slides)
- Week 3: Marketing site (nepalcarbon.org.np)
- Week 4: 2-min demo video + case study 1-pager

### Software Engineer
- Owns: production code, performance, reliability
- Week 5: Audit current code, list top 10 issues
- Week 6: Fix P0 issues (security, data loss, auth)
- Week 7: Multi-tenant hardening (RLS, audit log)
- Week 8: Load test + performance budget

### Environmental Engineer
- Owns: standards, verification, methodology
- Week 5: Audit all 11 standards modules for VVB-readiness
- Week 6: Build relationships with 2-3 VVB firms
- Week 7: Author methodology white paper
- Week 8: ISO 14064-1 audit template for clients

### AI/ML Engineer
- Owns: LLM advisor, forecasting, anomaly detection
- Week 9: Stand up vLLM on user's GPU machine
- Week 10: Fine-tune Qwen2.5-7B on Nepali industrial data
- Week 11: Add 50+ Nepali-language Q&A pairs
- Week 12: Production LLM advisor

### Data Engineer
- Owns: DB, IoT, real-time pipeline
- Week 9: Production Postgres setup
- Week 10: MQTT ingestion at scale (1000+ sensors)
- Week 11: Real-time dashboards
- Week 12: Data quality + backfill

### Marketing Lead
- Owns: content, PR, growth
- Week 9: Content calendar (2 posts/week)
- Week 10: 5 case studies
- Week 11: PR push (climate week, NCMA, GGGI)
- Week 12: Email nurture sequence

## How we work

### Communication
- **Daily**: founder + Mavis (async via this conversation)
- **Weekly**: 1-hour team call (Monday 10am NPT)
- **Async**: GitHub Issues, this conversation, Telegram group

### Repository structure
```
Nepal-Industrial-Decarbonization/
├── pro/                      # the platform code
├── docs/                     # technical docs
├── team/                     # team charter, RACI, meeting notes
│   ├── CHARTER.md            # this file
│   ├── RACI.md               # who's Responsible/Accountable/Consulted/Informed
│   ├── meetings/             # weekly notes
│   └── hiring/               # job descriptions
├── brand/                    # brand assets
│   ├── logo/
│   ├── colors/
│   ├── fonts/
│   └── pitch-deck/
├── docs/strategy/            # GTM, pricing, competitive analysis
├── docs/pitch/               # sales materials
├── docs/case-study/          # customer success stories
├── gtm/                      # lead lists, email templates
└── .team/                    # private team notes (not in repo)
```

### Decision-making
- **Strategic** (pricing, partnerships, hires): founder + Mavis
- **Technical** (architecture, libraries, deployment): Mavis
- **Domain** (cement process, standards): chemical/environmental engineer
- **Sales** (who to target, what to offer): founder + business dev
- **Brand** (logo, voice): founder + graphics

### Cadence
- **Weekly Monday 10am NPT**: team call (everyone, 60 min)
- **Weekly Friday**: progress update (each person, 1 page)
- **Monthly**: review OKRs, adjust plan
- **Quarterly**: review with advisor / funder

## Definition of done (every cycle)

Every deliverable must:
1. Be in the GitHub repo (single source of truth)
2. Be reviewed by 1 person (not the author)
3. Be tested (where applicable)
4. Be documented (1 paragraph in `docs/`)
5. Be linked from this charter

## Current status

| Role | Status | Deliverable this week |
|---|---|---|
| Founder | Active | - |
| Mavis (CTO) | Active | This audit + team charter |
| Chemical Engineer | **OPEN — recruiting** | - |
| Business Developer | **OPEN — recruiting** | - |
| Graphics Designer | **OPEN — recruiting** | - |
| Software Engineer | **OPEN — recruiting** | - |
| Environmental Engineer | **OPEN — recruiting** | - |
| AI/ML Engineer | **OPEN — recruiting** | - |
| Data Engineer | **OPEN — recruiting** | - |
| Marketing Lead | **OPEN — recruiting** | - |
