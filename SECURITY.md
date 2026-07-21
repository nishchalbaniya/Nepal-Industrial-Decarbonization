# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing **nishchal.baniya@himalayancarbonnepal.com** (do NOT open a public GitHub issue).

We will:
- Acknowledge within 24 hours
- Investigate and provide a fix timeline within 7 days
- Credit reporters (with their consent) in the fix release notes

## Scope

This is a multi-tenant platform that handles:
- Plant emissions data (often regulated under ISO 14064 / TCFD)
- User credentials (passwords, JWT tokens)
- MQTT sensor data (plant operational data)
- Carbon credit serial numbers (on-chain, financial impact)

**Vulnerabilities we especially care about:**
- Authentication bypass
- SQL injection (multi-tenant isolation)
- MQTT topic ACL bypass
- Smart contract reentrancy / overflow
- Cross-tenant data leakage
- Privilege escalation

## Hardening checklist (production deployments)

- [ ] `JWT_SECRET` is at least 32 random bytes
- [ ] `POSTGRES_PASSWORD` is at least 24 random bytes
- [ ] MQTT `passwd` file has `nepal` user with strong password
- [ ] All secrets stored in AWS Secrets Manager / Vault, not env vars
- [ ] TLS termination at ALB / nginx
- [ ] MQTT over TLS (port 8883, not 1883)
- [ ] Database backups encrypted (S3 SSE)
- [ ] UFW firewall limits MQTT to known plant IPs
- [ ] 2FA enabled on admin accounts
- [ ] Audit log shipped to immutable storage
- [ ] Quarterly penetration test
- [ ] Annual third-party security review of the Solidity contract
