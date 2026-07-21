# Commissioning Guide
## Nepal Industrial Decarbonization Platform v1.0.0

**For:** System integrators, IT administrators, commissioning engineers
**Version:** 1.0.0
**Date:** 2026-07-21

---

## 1. Pre-commissioning checklist

### 1.1 Hardware
- [ ] Server: 8 GB RAM, 50 GB SSD, 2+ cores
- [ ] Network: static IP, port 8501, 8000, 1883 (MQTT) open
- [ ] Optional: Industrial PC for sensor gateway
- [ ] Sensors: temperature, pressure, flow, gas composition

### 1.2 Software prerequisites
- [ ] Docker 24+ OR Python 3.10+
- [ ] Git
- [ ] TLS certificates (for production)
- [ ] DNS records for API and UI

### 1.3 Documentation
- [ ] Plant data (annual operating data)
- [ ] Equipment inventory
- [ ] Sensor list with calibration certificates
- [ ] Process flow diagrams
- [ ] Network diagram

---

## 2. Installation

### 2.1 Local install (for testing)

```bash
# System deps (Ubuntu/Debian)
sudo apt update
sudo apt install -y python3.11 python3.11-venv git

# Clone
git clone https://github.com/<your-org>/nepal-decarb.git
cd nepal-decarb/pro

# Create venv
python3.11 -m venv .venv
source .venv/bin/activate

# Install
pip install --upgrade pip
pip install -e ".[full]"

# Verify
nepal-decarb version
```

### 2.2 Docker (production)

```bash
# Build
cd nepal-decarb/pro
docker build -t nepal-decarb-pro:1.0.0 .

# Or use pre-built image (after pushing to registry)
docker pull himalayancarbon/nepal-decarb-pro:1.0.0

# Run
docker run -d \
    --name nepal-decarb \
    -p 8501:8501 \
    -p 8000:8000 \
    -p 1883:1883 \
    -v /var/lib/nepal-decarb:/data \
    -e NEPAL_DECARB_SECRET=$(openssl rand -hex 32) \
    nepal-decarb-pro:1.0.0
```

### 2.3 Docker Compose (full stack)

```bash
cd nepal-decarb/pro
cp .env.example .env
# Edit .env:
#   NEPAL_DECARB_SECRET=<random-256-bit-key>
#   NEPAL_DECARB_DB=/data/nepal_decarb.db
#   MQTT_BROKER=mqtt://mosquitto:1883

docker-compose up -d
docker-compose ps
```

### 2.4 Kubernetes (Helm)

```bash
# Add repo (after first release)
helm repo add nepal-decarb https://himalayancarbon.github.io/nepal-decarb
helm repo update

# Install
helm install nepal-decarb nepal-decarb/nepal-decarb \
    --namespace nepal-decarb \
    --create-namespace \
    --set image.tag=1.0.0 \
    --set persistence.size=100Gi \
    --set mqtt.enabled=true

# Check
kubectl -n nepal-decarb get pods
kubectl -n nepal-decarb get svc
```

---

## 3. Initial configuration

### 3.1 Set the secret key

```bash
# Generate a strong key
openssl rand -hex 32
# Set it
export NEPAL_DECARB_SECRET=<the-generated-key>
# Persist in .env
echo "NEPAL_DECARB_SECRET=<the-generated-key>" >> .env
```

### 3.2 Create the database

```bash
# Auto-created on first start
# Verify
sqlite3 /var/lib/nepal-decarb/nepal_decarb.db ".tables"
# Should show: tenants, plants, emissions_results, audit_log
```

### 3.3 Create admin tenant and user

```bash
# Use the API to create a tenant
curl -X POST http://localhost:8000/tenants \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Hetauda Cement Industries Ltd",
      "industry": "cement",
      "country": "Nepal"
    }'

# Get an API token
curl -X POST http://localhost:8000/auth/token \
    -H "Content-Type: application/json" \
    -d '{"tenant_id": "hetauda-cement", "user_id": "admin"}'
```

---

## 4. Sensor integration

### 4.1 MQTT setup

**Local broker (for small pilot):**
```bash
# Use the bundled mosquitto
docker-compose up -d mosquitto
```

**Cloud MQTT (HiveMQ Cloud, AWS IoT, etc.):**
```bash
# Update .env
MQTT_BROKER=mqtts://<your-broker>:8883
MQTT_USERNAME=<username>
MQTT_PASSWORD=<password>
```

### 4.2 ESP32 firmware deployment

See `firmware/` directory for ESP32 Arduino sketch:

```cpp
// firmware/esp32_sensor.ino
// - Reads DHT22 (temperature + humidity)
// - Reads MQ-7 (CO)
// - Reads MQ-135 (NOx, CO2)
// - Publishes to MQTT every 10s
// - Auto-reconnect
// - OTA update support
```

Flash with:
```bash
# Install Arduino CLI
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# Install ESP32 board support
arduino-cli core install esp32:esp32

# Install libraries
arduino-cli lib install "PubSubClient" "DHT sensor library" "ArduinoJson"

# Compile and upload
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/esp32_sensor.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 firmware/esp32_sensor.ino
```

### 4.3 Verify data flow

```bash
# Subscribe to MQTT
mosquitto_sub -h localhost -p 1883 -t "nepal/#" -v

# Should see messages from your sensors

# Check API for processed state
curl -H "Authorization: Bearer <token>" \
    http://localhost:8000/v1/audit
```

---

## 5. Commissioning tests

### 5.1 Unit tests
```bash
pytest tests/ -v
# Should show 50+ tests passing
```

### 5.2 Integration test
```bash
# Start full stack
docker-compose up -d

# Run the full demo
python scripts/full_demo.py

# Should complete without errors and generate 3 PDFs
ls -la reports/
```

### 5.3 Performance test

```bash
# Load test the API
pip install locust
locust -f tests/load_test.py --host=http://localhost:8000 -u 50 -r 5 -t 60s
```

Expected:
- 50+ concurrent users
- <500ms p95 latency
- 100+ RPS

### 5.4 Standards compliance test

```bash
# ISO 14064-1
curl -X POST http://localhost:8000/v1/standards/iso-14064-1 \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -d @sample_plant.json

# Should return 100/100 score
```

---

## 6. Acceptance criteria

The pilot is considered commissioned when:

- [x] Stack running stably for 7 days
- [x] All sensors reporting data via MQTT
- [x] Dashboard accessible to operators
- [x] Baseline calculation matches manual reference (within 5%)
- [x] Verra PDD generates successfully
- [x] ISO 14064-1 score >90/100
- [x] Audit log captures all user actions
- [x] All tests pass
- [x] PDF reports generate and download
- [x] Disaster recovery tested (backup/restore)

---

## 7. Handover to operations

After commissioning:

1. **Training session** for plant operators (4 hours)
2. **Training session** for IT support (2 hours)
3. **Handover document** with admin credentials, backup procedures
4. **SLA agreement** with vendor (Himalayan Carbon Nepal)
5. **Escalation matrix** for issues
6. **Quarterly review** schedule

---

## 8. Post-commissioning

### 8.1 Monitoring

```bash
# Check disk usage
df -h /var/lib/nepal-decarb

# Check memory
free -h

# Check Docker
docker stats

# Check API
curl http://localhost:8000/health
```

### 8.2 Backup

```bash
# Daily DB backup
sqlite3 /var/lib/nepal-decarb/nepal_decarb.db ".backup '/backups/nepal-decarb-$(date +%Y%m%d).db'"

# Weekly full backup
tar czf /backups/nepal-decarb-full-$(date +%Y%m%d).tgz \
    /var/lib/nepal-decarb \
    /etc/nepal-decarb
```

### 8.3 Update

```bash
# Pull latest
git pull

# Rebuild
cd pro && docker build -t nepal-decarb-pro:1.0.1 .

# Restart
docker-compose up -d
```

---

## 9. Support contacts

- **Himalayan Carbon Nepal:** nishchal.baniya@himalayancarbonnepal.com
- **GitHub issues:** https://github.com/<your-org>/nepal-decarb/issues
- **Operator hotline:** +977-XXX-XXXX
- **Emergency (24/7):** +977-XXX-XXXX

---

**Document version:** 1.0.0 · **Last updated:** 2026-07-21
