# Operator Manual
## Nepal Industrial Decarbonization Platform v1.0.0

**For:** Plant operators, shift engineers, control room staff
**Version:** 1.0.0
**Date:** 2026-07-21

---

## 1. Quick start for operators

### What is this system?
A digital platform that:
1. Calculates your plant's emissions in real time
2. Compares your performance against global best practice
3. Helps you identify and capture cost-saving opportunities
4. Generates reports for regulators and carbon markets
5. Predicts equipment issues before they happen

### Where to find what
- **Streamlit UI:** `http://<server>:8501` → visual dashboards
- **FastAPI:** `http://<server>:8000/docs` → API documentation
- **CLI:** `nepal-decarb` command in your terminal
- **PDF reports:** `/reports` directory

### Login
Ask your admin for:
- **Tenant ID** (your company identifier)
- **User ID** (your personal login)
- **API token** (for API access)

---

## 2. Daily operations

### 2.1 Start of shift

```
1. Open browser: http://<server>:8501
2. Log in with your credentials
3. Check "Today" dashboard:
   - Total emissions today (tCO₂)
   - Energy consumption today (GJ)
   - Any alerts (red badges)
4. Review overnight alerts
5. Take corrective action if needed
```

### 2.2 During shift

**Real-time monitoring:**
- The dashboard updates every 30 seconds with new sensor data
- Anomalies are highlighted in red
- Predictions are shown for next hour

**What to watch for:**
- **Burning zone temperature:** should be 1400-1500°C
- **O2 in kiln exhaust:** should be 2-4%
- **NOx:** should be <800 mg/Nm³
- **Clinker cooler discharge temp:** should be <150°C
- **Bag filter pressure drop:** should be <2000 Pa

**Anomaly response:**
- Read the alert message carefully
- Check the suggested action
- Verify sensor reading (is it a sensor fault?)
- Take action: adjust setpoint, change fuel, stop feed, etc.
- Document in shift log

### 2.3 End of shift

```
1. Generate daily emissions report
2. Update plant operating log
3. Hand over to next shift:
   - Current state
   - Pending issues
   - Scheduled activities
```

---

## 3. Weekly tasks

### 3.1 Re-baseline calculation

```bash
nepal-decarb cement \
    --name "Hetauda Cement Industries Ltd" \
    --year 2026 --clinker-t 32000 --cement-t 37000 \
    --coal-t 4000 --petcoke-t 600 --elec-kwh 2900000
```

Review the output:
- Total emissions (tCO₂)
- Intensity (kg CO₂/t cement)
- vs BAT benchmark
- vs Nepal average

### 3.2 Fuel blend optimization

```bash
nepal-decarb fuel-optimize \
    --energy-gj 130000 \
    --max-biomass 0.40
```

Use the recommended blend if it:
- Reduces emissions
- Doesn't increase cost
- Is operationally feasible

### 3.3 Verra monitoring report (if crediting)

```bash
nepal-decarb verra --name "MyProject" \
    --baseline-tco2 861025 --project-tco2 791171
```

This generates a PDF report for VVB verification.

---

## 4. Monthly tasks

### 4.1 Performance review

- Compare this month vs last month
- Compare vs same month last year
- Identify trends (good or bad)
- Discuss with management

### 4.2 Calibration verification

- Verify all CEMS analyzers
- Check flow meters
- Calibrate weigh feeders
- Document calibrations

### 4.3 Update NEA grid factor (annual)

When NEA releases new annual report:
1. Edit `data/emission_factors.yaml`
2. Update `grid.combined_margin`
3. Re-run all calculations

---

## 5. Troubleshooting for operators

### 5.1 Sensor shows wrong value

```
1. Check sensor physical condition
2. Check cable connections
3. Check transmitter
4. Cross-check with manual reading (e.g., handheld)
5. If sensor is faulty: replace, mark data bad
6. Document in shift log
```

### 5.2 Emissions too high

```
1. Check fuel mix (too much coal? too little biomass?)
2. Check raw mix chemistry (high LSF = more CO2)
3. Check kiln temperature (too hot = more NOx)
4. Check preheater performance
5. Check cooler efficiency
6. Run optimization to find best mitigation
```

### 5.3 Power consumption high

```
1. Check VRM / ball mill performance
2. Check ID fan, ESP, bag filter fans
3. Check raw mill utilization
4. Check compressed air leaks
5. Schedule maintenance
```

---

## 6. Safety

⚠️ **Never override safety interlocks to reduce emissions.**

This software is for monitoring and optimization. It is NOT a safety system.
All safety-critical decisions must follow plant safety procedures.

If you see:
- Temperature above 1500°C → follow kiln shutdown procedure
- CO in stack > 1000 ppm → reduce fuel, increase air
- NOx > 1500 mg/Nm³ → follow emission emergency procedure

---

## 7. Frequently asked questions

**Q: How accurate is the emissions calculation?**
A: ±5% for the baseline (Tier 2 method). ±3% for kiln-direct measurements.

**Q: Why does the dashboard show different numbers than my daily log?**
A: Real-time uses CEMS; daily log uses monthly fuel purchase. Both are valid, just different granularity.

**Q: Can I delete an old plant record?**
A: No, all data is kept for compliance. Use the "archive" function instead.

**Q: How do I add a new sensor?**
A: Contact your admin. They will register the sensor in the system.

**Q: The Verra PDF didn't generate. What now?**
A: Check the error message. Common issues: missing fuel data, invalid baseline. See troubleshooting in [`PILOT_DEPLOYMENT.md`](PILOT_DEPLOYMENT.md).

---

## 8. Contact

- **Operator hotline:** +977-XXX-XXXX
- **Email:** nishchal.baniya@himalayancarbonnepal.com
- **Emergency:** Contact your plant shift engineer first

---

**Document version:** 1.0.0 · **Last updated:** 2026-07-21
