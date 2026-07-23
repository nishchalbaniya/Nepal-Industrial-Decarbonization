# Plant Onboarding Guide — nepal_decarb_pro

> How to bring a new cement or brick plant onto the platform. 15 minutes for a basic onboarding, 2 hours for a full historical data import.

## Who this is for

- **Plant owners** of Nepali cement or brick operations
- **Industry consultants** doing MRV for multiple plants
- **NCMA / industry association staff** rolling this out to members
- **Government officials** setting up a national MRV system

## Two-tier onboarding

| Tier | Time | What you get | Cost |
|---|---|---|---|
| **Express** | 15 min | Tenant + 1 plant, current month only, manual entry, dashboard | Free |
| **Full** | 2-4 hours | Express + 3-5 yr historical data via CSV, IoT sensors, alerts, reports | Pro (paid) |

---

## Step 1 — Create a tenant account (Express)

### Via Web UI
1. Go to `https://nepalcarbon.org.np/`
2. Click "Sign up" (top right)
3. Fill in: company name, email, password, language (English / नेपाली)
4. Verify email (link sent immediately)
5. Login → land on the empty dashboard

### Via API
```bash
curl -X POST https://nepalcarbon.org.np/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "info@planta-cement.com.np",
    "password": "StrongP@ss123",
    "full_name": "PlantA Manager",
    "tenant_name": "PlantA Industries Ltd",
    "language": "en"
  }'
```

Response:
```json
{
  "user_id": "...",
  "tenant_id": "...",
  "tenant_slug": "planta-cement",
  "verification_url": "..."
}
```

---

## Step 2 — Register a plant

### Via Web UI
1. From dashboard, click "+ Add Plant"
2. Fill in:
   - Plant name: `PlantA Industries Ltd`
   - Plant type: dropdown — `cement_dry` / `cement_wet` / `brick_clamp` / `brick_zigzag` / `brick_tunnel` / `brick_hoffman`
   - Location: province (Bagmati), district (Makwanpur), lat/lng (auto from dropdown)
   - Capacity: 1,100,000 t/yr (cement)
   - Installed year: 1990
   - Main fuel: dropdown of Nepali fuels
3. Click "Save"
4. The system auto-generates: a unique `plant_id`, an MQTT topic prefix `nepal/<tenant>/<plant>/`, and a starter dashboard

### Via API
```bash
curl -X POST https://nepalcarbon.org.np/api/v1/plants \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PlantA Industries Ltd",
    "plant_type": "cement_dry",
    "province": "Bagmati",
    "district": "Makwanpur",
    "annual_capacity_t": 1100000,
    "installed_year": 1990,
    "main_fuel": "coal_bituminous_NP"
  }'
```

---

## Step 3 — Add monthly production + fuel data (Full tier)

### Option A: Web form (manual)
For each month, enter:
- Clinker produced (t), cement produced (t)
- Coal consumed (t), petcoke (t), diesel (L)
- Electricity (kWh)
- Raw materials (limestone, clay, etc.)

### Option B: CSV bulk import (recommended for historical data)
Download the template:
```bash
curl -O https://nepalcarbon.org.np/templates/historical_data.csv
```

CSV format (one row per plant per month):
```csv
period_start,period_end,clinker_t,cement_t,bricks_n,coal_t,petcoke_t,biomass_t,electricity_kwh,limestone_t,clay_t,iron_ore_t
2022-01-01,2022-01-31,78500,91500,,3200,580,0,7100000,102000,16500,3800
2022-02-01,2022-02-28,71200,82100,,2900,520,0,6450000,92500,15000,3450
...
```

Import via:
```bash
curl -X POST https://nepalcarbon.org.np/api/v1/plants/$PLANT_ID/import \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@historical_data.csv"
```

The system validates each row, computes the baseline, and reports any anomalies (e.g., coal intensity 3 sigma above plant mean).

### Option C: Excel upload
Same as CSV but `.xlsx`. Use the `Tools > Import` menu in the UI.

---

## Step 4 — Compute baseline (Tier 2 / Tier 3)

1. From plant page, click "Compute baseline"
2. Select: methodology (IPCC Tier 2 recommended), year (e.g., 2024)
3. The system runs:
   - Fuel CO₂ from combustion
   - Process CO₂ from clinker calcination
   - Electricity CO₂ from NEA grid EF
   - Monte Carlo (5,000 samples by default)
   - Tier 3 if raw mix TOC data is available
4. Result is stored in `baselines` table and shown in dashboard
5. ISO 14064-1 compliance report auto-generated (PDF)

### Via API
```bash
curl -X POST https://nepalcarbon.org.np/api/v1/plants/$PLANT_ID/baselines \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "methodology": "IPCC_2006_Tier2",
    "tier": 2,
    "base_year": 2024,
    "include_monte_carlo": true,
    "n_mc_samples": 5000
  }'
```

---

## Step 5 — Set up IoT sensors (optional but recommended)

For each ESP32 + sensor stack installed at the plant:

1. From plant page, click "Add sensor"
2. Fill in:
   - Sensor type: `temperature` / `co` / `nox` / `co2` / `pressure`
   - MQTT topic: auto-generated as `nepal/<tenant>/<plant>/<sensor_id>/<type>`
   - Location: e.g., "kiln burning zone", "preheater outlet", "clinker cooler"
   - Unit: °C / ppm / Pa
3. The system provisions MQTT credentials and an auth token
4. Flash the ESP32 with the firmware (`firmware/esp32_sensor.ino`)
5. Set the MQTT credentials in the firmware and reboot
6. Readings appear in the real-time dashboard within 10s

See `docs/OPERATOR_MANUAL.md` § 3 for full sensor setup details.

---

## Step 6 — Configure alerts

1. From plant page, click "Alerts"
2. Set thresholds:
   - High kiln temperature: > 1500 °C
   - High CO: > 500 ppm
   - High NOx: > 800 ppm
   - Production drop: > 20% vs trailing 30-day avg
3. Choose channels: email, Slack, SMS
4. Save — alerts active immediately

---

## Step 7 — Generate reports

Available reports (all auto-generated as PDF):
- **Executive summary** — 1-page, for plant manager
- **ISO 14064-1 compliance** — 20+ pages, for VVB audit
- **Verra monitoring report** — for carbon credit verification
- **TCFD disclosure** — for investors
- **SBTi target tracking** — for science-based targets

Download from the "Reports" tab on any plant page.

---

## Multi-plant onboarding

For NCMA / industry associations onboarding 50+ plants at once:

```bash
# 1. Download the bulk onboarding template
curl -O https://nepalcarbon.org.np/templates/bulk_onboarding.csv

# 2. Fill in one row per plant (template has example rows)

# 3. Upload via the admin panel
#    Settings > Bulk Onboard > Upload CSV
```

CSV format:
```csv
tenant_name,plant_name,plant_type,province,district,capacity_t,installed_year,main_fuel,manager_email
PlantA,PlantA Main Plant,cement_dry,Bagmati,Makwanpur,1100000,1990,coal_bituminous_NP,info@planta.com.np
Shree Cement,Unit 1,cement_dry,Bagmati,Kathmandu,250000,2012,coal_bituminous_NP,unit1@shreecement.com
...
```

Each manager receives a welcome email with their login credentials and a 5-minute video tour.

---

## Roles & permissions

| Role | Can do |
|---|---|
| `admin` | Everything: create users, manage billing, view all plants, export |
| `plant_manager` | Their assigned plant(s): enter data, view reports, manage sensors |
| `analyst` | All plants in tenant: view data, run baseline, generate reports, no editing |
| `viewer` | Read-only: dashboards, reports, no editing |
| `auditor` (external) | Time-limited access to specific reports for ISO 14064 / Verra audit |

---

## Localization

- UI language: set per-user (English / नेपाली)
- Reports: per-user language preference
- All Nepali translations done by domain experts (not machine-translated)
- Date format: AD (BS conversion available on demand)

---

## Support

- **Email**: support@nepalcarbon.org.np
- **Phone**: +977-1-XXXXXXX (10am-6pm NPT)
- **WhatsApp group** for plant managers (link in welcome email)
- **Quarterly webinar** for new features (calendar invite on signup)

---

## What happens after onboarding

1. **Day 0**: Account + plant created, welcome email sent
2. **Day 1**: Manager logs in, enters 1st month data, sees first baseline
3. **Week 1**: IoT sensors installed at large plants; real-time data flowing
4. **Month 1**: First full baseline + ISO 14064-1 report generated
5. **Quarter 1**: First carbon credit issuance (if applicable)
6. **Year 1**: Annual report + benchmarking vs industry peers

---

*Last updated: 2026-07-22 — v1.0.1 of nepal_decarb_pro*
