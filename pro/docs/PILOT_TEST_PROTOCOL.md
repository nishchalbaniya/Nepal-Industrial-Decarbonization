# Pilot Test Protocol
## Nepal Industrial Decarbonization Platform v1.0.0

**For:** QA engineers, VVB (Verification & Validation Bodies), plant auditors
**Version:** 1.0.0
**Date:** 2026-07-21

---

## 1. Purpose

This protocol tests the `nepal_decarb_pro` v1.0.0 platform against:
1. **Functional requirements** — does it calculate correctly?
2. **Standards compliance** — does it meet 11 international standards?
3. **Engineering rigor** — does it produce defensible numbers?
4. **Deployment readiness** — does it run reliably?
5. **Security** — is data protected?
6. **Performance** — is it fast enough?

## 2. Test categories

### 2.1 Unit tests
- **Goal:** Verify each function/class works correctly in isolation
- **Coverage target:** ≥85% line coverage
- **Current:** 50+ tests, all passing

### 2.2 Integration tests
- **Goal:** Verify modules work together (e.g., cement + LCA + Verra)
- **Coverage:** All major user workflows

### 2.3 Standards tests
- **Goal:** Verify compliance checkers return correct scores
- **Method:** Test against known good and known bad inputs

### 2.4 Performance tests
- **Goal:** Verify API responds in <500ms p95
- **Method:** Locust load test, 50 concurrent users, 60 seconds

### 2.5 Security tests
- **Goal:** Verify auth, RBAC, audit, no SQL injection
- **Method:** OWASP API Top 10 checklist

---

## 3. Functional tests

### 3.1 Cement baseline (Tier 2)

**Test ID:** F-CEM-001
**Input:** Hetauda Cement, 950k t clinker, 1.1M t cement, 120k t coal, 85 GWh elec
**Expected output:**
- Total emissions: 800,000 - 900,000 tCO₂/yr
- Intensity: 750-820 kg CO₂/t cement
- vs BAT (700): positive (worse than BAT)
- vs Nepal avg (950): negative (better than avg)

**Pass criteria:** All 4 expected ranges met.

### 3.2 Cement baseline (Tier 3)

**Test ID:** F-CEM-002
**Input:** Same as F-CEM-001
**Expected output:**
- Process emissions: slightly higher than Tier 2 (due to TOC and precalc)
- Otherwise similar

**Pass criteria:** Tier 3 process emissions > Tier 2 process emissions.

### 3.3 Brick baseline (5 kiln types)

**Test ID:** F-BRK-001 through F-BRK-005
**Input:** 5 million bricks/yr for each kiln type
**Expected output:**
- Clamp: highest emissions (~720 kg CO₂/1000 bricks)
- Vertical shaft: lowest emissions (~220 kg/1000)
- Tunnel < Hoffman < Clamp in efficiency

**Pass criteria:** Ordering correct; values in ±20% of reference.

### 3.4 Monte Carlo UQ

**Test ID:** F-MC-001
**Input:** Hetauda plant, 3000 samples
**Expected output:**
- CoV < 10% (typically ~3% for Hetauda)
- 90% CI covers nominal value
- Converged = True

**Pass criteria:** All 3 conditions met.

### 3.5 MILP fuel blend

**Test ID:** F-OPT-001
**Input:** 1,000,000 GJ energy, max 40% biomass
**Expected output:**
- Sum of shares = 1.0
- Biomass share ≤ 0.40
- Cost-optimal solution found

**Pass criteria:** All 3 met.

### 3.6 LCA

**Test ID:** F-LCA-001
**Input:** Hetauda plant
**Expected output:**
- GWP100: 600-1500 kg CO₂-eq/t cement
- 6 impact categories computed
- Stage contributions sum to total

**Pass criteria:** All 3 met.

---

## 4. Standards tests

### 4.1 ISO 14064-1

**Test ID:** S-ISO-001
**Input:** Cement plant with full data
**Expected:**
- All 20 required criteria
- Score = 100/100 (when all data provided)
- Recommendations for any gaps

**Pass:** Score ≥ 80/100 with full data.

### 4.2 ISO 14064-2

**Test ID:** S-ISO-002
**Input:** Project with full verification
**Expected:**
- All 14 required criteria
- Score = 100/100

**Pass:** Score ≥ 80/100.

### 4.3 ISO 14064-3

**Test ID:** S-ISO-003
**Input:** VVB-verified project
**Expected:** Score = 100/100

**Pass:** Score ≥ 80/100.

### 4.4 ISO 50001

**Test ID:** S-50001-001
**Input:** Plant with energy review
**Expected:** Score = 100/100

**Pass:** Score ≥ 80/100.

### 4.5 ISO 14001

**Test ID:** S-14001-001
**Input:** Plant with documented EMS
**Expected:** Score = 100/100

**Pass:** Score ≥ 80/100.

### 4.6 TCFD

**Test ID:** S-TCFD-001
**Input:** Cement plant
**Expected:**
- 4 pillars covered
- 3 scenarios analyzed

**Pass:** All 4 pillars populated.

### 4.7 SBTi

**Test ID:** S-SBTi-001
**Input:** Target 56% reduction by 2030
**Expected:** Aligned (56% > 38% required for 1.5°C)

**Pass:** `aligned_with_1_5c = True`.

### 4.8 GCCA

**Test ID:** S-GCCA-001
**Input:** Hetauda plant
**Expected:** 7 KPIs computed

**Pass:** All 7 KPIs returned.

### 4.9 PCAF

**Test ID:** S-PCAF-001
**Input:** Loan portfolio
**Expected:** Financed emissions with DQ score

**Pass:** DQ score 1-5, attribution factor 0-1.

### 4.10 Verra VCS

**Test ID:** S-VERRA-001
**Input:** Project
**Expected:** Full PDD with all sections

**Pass:** All sections populated.

### 4.11 Gold Standard

**Test ID:** S-GS-001
**Input:** Project
**Expected:** Full PDD + SDGs

**Pass:** ≥3 SDGs claimed.

---

## 5. Performance tests

### 5.1 API latency

**Test:** 50 concurrent users, 60 seconds
**Expected:**
- p50 < 100ms
- p95 < 500ms
- p99 < 1000ms
- 0 errors

**Pass:** All metrics met.

### 5.2 Monte Carlo performance

**Test:** 5000 samples on Hetauda plant
**Expected:**
- < 30 seconds
- < 200 MB memory

**Pass:** Both met.

### 5.3 WebSocket throughput

**Test:** 1000 sensor readings per second
**Expected:**
- < 100ms processing per reading
- < 1% drop rate

**Pass:** Both met.

---

## 6. Security tests

### 6.1 Authentication
- [ ] No endpoint accessible without token
- [ ] Token expires after 24 hours
- [ ] Invalid token returns 401

### 6.2 Authorization
- [ ] Tenant A cannot read Tenant B's data
- [ ] Read-only token cannot write

### 6.3 Input validation
- [ ] SQL injection blocked
- [ ] XSS blocked
- [ ] Path traversal blocked

### 6.4 Audit trail
- [ ] All user actions logged
- [ ] Audit log immutable
- [ ] Audit log queryable by tenant

---

## 7. Acceptance criteria

The pilot is accepted when:

1. ✅ All 50+ unit tests pass
2. ✅ All 11 standards reach ≥80/100
3. ✅ All functional tests pass
4. ✅ Performance tests meet SLOs
5. ✅ Security tests pass
6. ✅ Documentation complete
7. ✅ Deployment guide verified
8. ✅ Operator training complete
9. ✅ Disaster recovery tested
10. ✅ Stakeholder sign-off

---

## 8. Sign-off

| Role | Name | Signature | Date |
|---|---|---|---|
| Plant manager | __________ | __________ | _______ |
| IT admin | __________ | __________ | _______ |
| QA lead | __________ | __________ | _______ |
| VVB | __________ | __________ | _______ |
| Project sponsor | __________ | __________ | _______ |

---

**Document version:** 1.0.0 · **Last updated:** 2026-07-21
