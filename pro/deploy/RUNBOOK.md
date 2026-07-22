# Runbook — nepal_decarb_pro production operations

> On-call procedures for the production platform. Read this before going on call.

## Service map

| Service | Port | Container | Healthcheck | Restart cmd |
|---|---|---|---|---|
| PostgreSQL | 5432 | nepal-decarb-db | `pg_isready` | `docker restart nepal-decarb-db` |
| FastAPI | 8000 | nepal-decarb-api | `GET /health` | `docker restart nepal-decarb-api` |
| Streamlit | 8501 | nepal-decarb-streamlit | `GET /_stcore/health` | `docker restart nepal-decarb-streamlit` |
| Mosquitto MQTT | 1883, 9001 | nepal-decarb-mqtt | TCP connect | `docker restart nepal-decarb-mqtt` |
| Redis | 6379 | nepal-decarb-redis | `redis-cli ping` | `docker restart nepal-decarb-redis` |
| Prometheus | 9090 | nepal-decarb-prometheus | `GET /-/ready` | `docker restart nepal-decarb-prometheus` |
| Grafana | 3000 | nepal-decarb-grafana | `GET /api/health` | `docker restart nepal-decarb-grafana` |
| vLLM (GPU) | 8001 | nepal-decarb-vllm | `GET /v1/models` | `docker restart nepal-decarb-vllm` |

## Common operations

### Restart all services
```bash
cd /opt/nepal_decarb_pro
docker compose -f deploy/vps/docker-compose.yml restart
```

### View logs (last 100 lines, follow)
```bash
docker logs -f --tail 100 nepal-decarb-api
```

### Database connection
```bash
docker exec -it nepal-decarb-db psql -U nepal_admin -d nepal_decarb
```

### Reset a user's password
```bash
docker exec nepal-decarb-api python -c "
import sys; sys.path.insert(0, '/app')
from nepal_decarb_pro.auth.service import reset_password
reset_password('user@example.com', 'NewP@ssw0rd!')
"
```

### Force a backup
```bash
/opt/nepal_decarb_pro/deploy/backup/backup.sh
```

### Restore from backup
```bash
/opt/nepal_decarb_pro/deploy/backup/restore.sh /var/backups/nepal-decarb/db/db-YYYYMMDD-HHMMSS.dump.gz
```

### Renew SSL cert
```bash
certbot renew
systemctl reload nginx
```

### Update application
```bash
cd /opt/nepal_decarb_pro
git pull
docker compose -f deploy/vps/docker-compose.yml build
docker compose -f deploy/vps/docker-compose.yml up -d
```

## Incident playbooks

### P1: API is down
1. Check container status: `docker ps -a | grep api`
2. View logs: `docker logs --tail 200 nepal-decarb-api`
3. Common causes:
   - Database connection failure → check `nepal-decarb-db` is healthy
   - Out of memory → `docker stats nepal-decarb-api`
   - Bad config → check `.env` for recent edits
4. If all else fails: `docker restart nepal-decarb-api`
5. Escalate if down > 15 minutes

### P1: Database corruption
1. Stop API immediately: `docker stop nepal-decarb-api nepal-decarb-streamlit`
2. Check disk: `df -h /var/lib/postgresql`
3. If disk full: prune old backups, archives
4. If actual corruption: restore from latest backup using `restore.sh`
5. Verify data integrity: `docker exec nepal-decarb-db vacuumdb -U nepal_admin -d nepal_decarb --analyze`
6. Restart API: `docker start nepal-decarb-api nepal-decarb-streamlit`

### P2: Plant reports missing data
1. Check plant's last data entry: `SELECT * FROM production_records WHERE plant_id = '...' ORDER BY period_end DESC LIMIT 5`
2. Check sensor readings: `SELECT * FROM sensor_readings WHERE plant_id = '...' ORDER BY ts DESC LIMIT 10`
3. If sensor offline: check MQTT, check plant's internet connection
4. If manual entry overdue: contact plant manager
5. If data anomaly (e.g., intensity > 3σ): review anomaly log, contact plant

### P2: Email/Slack alerts not firing
1. Check ALERT_WEBHOOK env var: `cat /opt/nepal_decarb_pro/.env | grep ALERT`
2. Test webhook: `curl -X POST $ALERT_WEBHOOK -H 'Content-Type: application/json' -d '{"text":"test"}'`
3. Check Prometheus AlertManager: `docker logs nepal-decarb-prometheus`

### P3: User can't login
1. Check user exists: `SELECT * FROM users WHERE email = '...'`
2. Reset password (see above)
3. If user inactive: `UPDATE users SET is_active = TRUE WHERE email = '...'`

### P3: vLLM (LLM advisor) down
1. Check GPU: `nvidia-smi`
2. Check logs: `docker logs nepal-decarb-vllm | tail -100`
3. Common: OOM, model loading failure
4. Restart: `docker restart nepal-decarb-vllm`
5. Falls back to "stub" mode (still works, less smart)

## Monitoring

- **Grafana**: `http://<server>:3000` (admin / DB password)
- **Prometheus**: `http://<server>:9090`
- **Uptime monitor**: external (e.g., UptimeRobot) pings `/health` every 60s

## On-call contacts

- **Primary**: [Name] — [phone] — [email]
- **Secondary**: [Name] — [phone] — [email]
- **Himalayan Space Solutions**: support@nepalcarbon.org.np
- **Escalation**: [CTO name] — [phone]

## Postmortem template

After any P1 or P2 incident, write a postmortem with:
1. Summary (one paragraph)
2. Timeline (UTC + NPT)
3. Root cause
4. Resolution
5. Customer impact (plants affected, downtime)
6. Action items to prevent recurrence
