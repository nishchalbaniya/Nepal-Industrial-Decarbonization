-- =====================================================================
-- nepal_decarb_pro: production multi-tenant schema
-- =====================================================================
-- All tables have tenant_id for row-level isolation. The application
-- enforces tenant scoping via SQLAlchemy + Postgres RLS.
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "timescaledb";  -- if available; for time-series

-- ===== Tenants (organizations = one plant owner or one cement group) =====
CREATE TABLE tenants (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name          TEXT NOT NULL,
    slug          TEXT UNIQUE NOT NULL,
    country       TEXT NOT NULL DEFAULT 'NP',
    sector        TEXT,                       -- 'cement' or 'brick'
    plan          TEXT NOT NULL DEFAULT 'free',  -- free, pro, enterprise
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    settings      JSONB NOT NULL DEFAULT '{}',
    contact_email TEXT,
    contact_phone TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_tenants_slug ON tenants(slug);

-- ===== Users =====
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email           TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name       TEXT,
    role            TEXT NOT NULL DEFAULT 'analyst',  -- admin, analyst, viewer, plant_manager
    language        TEXT NOT NULL DEFAULT 'en',       -- en, ne
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- ===== Plants (industrial sites) =====
CREATE TABLE plants (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name                    TEXT NOT NULL,
    plant_type              TEXT NOT NULL,   -- 'cement_dry', 'cement_wet', 'brick_clamp', 'brick_zigzag', 'brick_tunnel', 'brick_hoffman'
    province                TEXT,            -- NP province
    district                TEXT,
    latitude                DECIMAL(9, 6),
    longitude               DECIMAL(9, 6),
    annual_capacity_t       DECIMAL(15, 2),  -- tonnes per year
    installed_year          INT,
    main_fuel               TEXT,            -- primary fuel
    alt_fuel_pct            DECIMAL(5, 2) DEFAULT 0,
    equipment_database_json JSONB,
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);
CREATE INDEX idx_plants_tenant ON plants(tenant_id);
CREATE INDEX idx_plants_type ON plants(plant_type);

-- ===== Production records (monthly/annual) =====
CREATE TABLE production_records (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plant_id            UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    period_start        DATE NOT NULL,
    period_end          DATE NOT NULL,
    clinker_produced_t  DECIMAL(15, 2),
    cement_produced_t   DECIMAL(15, 2),
    bricks_produced_n   BIGINT,
    raw_meal_throughput DECIMAL(15, 2),
    operating_hours     DECIMAL(10, 2),
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(plant_id, period_start, period_end)
);
CREATE INDEX idx_prod_plant_period ON production_records(plant_id, period_start);

-- ===== Fuel consumption records =====
CREATE TABLE fuel_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plant_id        UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    fuel_name       TEXT NOT NULL,           -- coal_bituminous_NP, petcoke, natural_gas, biomass_sawdust, rdf_municipal, diesel, etc.
    consumption_t   DECIMAL(15, 4) NOT NULL,
    ncvc_gj_per_t   DECIMAL(10, 4),          -- net calorific value
    price_usd_per_t DECIMAL(10, 2),
    supplier        TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_fuel_plant_period ON fuel_records(plant_id, period_start);

-- ===== Electricity consumption =====
CREATE TABLE electricity_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plant_id        UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    consumption_kwh DECIMAL(15, 2) NOT NULL,
    source          TEXT,                    -- 'grid', 'solar', 'diesel_gen', 'hydro'
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== Material inputs (raw mix, additives) =====
CREATE TABLE material_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plant_id        UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    material_name   TEXT NOT NULL,           -- limestone, clay, iron_ore, gypsum, fly_ash, slag
    consumption_t   DECIMAL(15, 4) NOT NULL,
    toc_pct         DECIMAL(6, 3),           -- total organic carbon
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== Sensor devices (IoT) =====
CREATE TABLE sensors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plant_id        UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    sensor_type     TEXT NOT NULL,           -- 'temperature', 'co', 'nox', 'co2', 'o2', 'pressure', 'flow'
    unit            TEXT NOT NULL,
    mqtt_topic      TEXT NOT NULL,
    location        TEXT,                    -- 'kiln_burning_zone', 'preheater_top', 'cooler_outlet'
    calibration     JSONB,
    last_value      DECIMAL(15, 4),
    last_reading_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    installed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_sensors_plant ON sensors(plant_id);

-- ===== Sensor readings (time-series; partition by month) =====
CREATE TABLE sensor_readings (
    sensor_id   UUID NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    tenant_id   UUID NOT NULL,
    plant_id    UUID NOT NULL,
    ts          TIMESTAMPTZ NOT NULL,
    value       DECIMAL(15, 4) NOT NULL,
    quality     DECIMAL(4, 3) NOT NULL DEFAULT 1.0  -- 0-1
) PARTITION BY RANGE (ts);

-- Default monthly partition creation function
CREATE OR REPLACE FUNCTION create_monthly_partition(target_date DATE) RETURNS VOID AS $$
DECLARE
    start_date DATE := date_trunc('month', target_date)::DATE;
    end_date   DATE := (date_trunc('month', target_date) + interval '1 month')::DATE;
    part_name  TEXT := 'sensor_readings_' || to_char(start_date, 'YYYY_MM');
BEGIN
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF sensor_readings FOR VALUES FROM (%L) TO (%L)',
        part_name, start_date, end_date
    );
EXCEPTION
    WHEN duplicate_table THEN
        NULL;  -- already exists
END;
$$ LANGUAGE plpgsql;

-- Pre-create partitions for current and next 3 months
SELECT create_monthly_partition(CURRENT_DATE);
SELECT create_monthly_partition(CURRENT_DATE + interval '1 month');
SELECT create_monthly_partition(CURRENT_DATE + interval '2 month');
SELECT create_monthly_partition(CURRENT_DATE + interval '3 month');

CREATE INDEX idx_readings_sensor_ts ON sensor_readings(sensor_id, ts DESC);
CREATE INDEX idx_readings_plant_ts ON sensor_readings(plant_id, ts DESC);

-- ===== Baselines (computed emissions inventories) =====
CREATE TABLE baselines (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plant_id        UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    methodology     TEXT NOT NULL,           -- 'IPCC_2006_Tier2', 'IPCC_2006_Tier3', 'ISO_14064_1'
    tier            INT,                     -- 1, 2, or 3
    base_year       INT NOT NULL,
    scope1_tco2     DECIMAL(15, 2) NOT NULL,
    scope2_tco2     DECIMAL(15, 2) NOT NULL,
    scope3_tco2     DECIMAL(15, 2) DEFAULT 0,
    total_tco2      DECIMAL(15, 2) NOT NULL,
    intensity_kg_per_t DECIMAL(10, 3),
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    computed_by     UUID REFERENCES users(id),
    parameters_json JSONB,
    notes           TEXT
);
CREATE INDEX idx_baselines_plant ON baselines(plant_id, base_year DESC);

-- ===== Carbon credit projects (Verra / Gold Standard) =====
CREATE TABLE projects (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plant_id            UUID NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    registry            TEXT,                -- 'Verra_VCS', 'Gold_Standard', 'PURO', 'ACR'
    methodology         TEXT,                -- 'VM0009', 'ACM0002', 'GS_TPDDTEC'
    status              TEXT NOT NULL DEFAULT 'draft',  -- draft, pdd_submitted, validated, registered, monitoring, verified, credits_issued
    pdd_json            JSONB,
    baseline_annual_tco2 DECIMAL(15, 2),
    project_annual_tco2  DECIMAL(15, 2),
    credits_issued      BIGINT DEFAULT 0,
    crediting_start     DATE,
    crediting_end       DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

CREATE TABLE credit_issuances (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    vintage_year      INT NOT NULL,
    quantity_tco2     DECIMAL(15, 4) NOT NULL,
    serial_start      TEXT,
    serial_end        TEXT,
    issued_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    registry_status   TEXT
);
CREATE INDEX idx_issuances_project ON credit_issuances(project_id);

-- ===== Audit log (immutable; for ISO 14064-2, ISO 50001) =====
CREATE TABLE audit_log (
    id            BIGSERIAL PRIMARY KEY,
    ts            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tenant_id     UUID,
    user_id       UUID,
    action        TEXT NOT NULL,             -- 'login', 'create_plant', 'compute_baseline', 'edit_fuel', etc.
    resource_type TEXT,
    resource_id   TEXT,
    ip_address    INET,
    user_agent    TEXT,
    diff_json     JSONB
);
CREATE INDEX idx_audit_ts ON audit_log(ts DESC);
CREATE INDEX idx_audit_tenant_ts ON audit_log(tenant_id, ts DESC);

-- Make audit_log append-only
REVOKE UPDATE, DELETE ON audit_log FROM nepal_admin;

-- ===== Row-level security (defense in depth) =====
ALTER TABLE plants              ENABLE ROW LEVEL SECURITY;
ALTER TABLE production_records  ENABLE ROW LEVEL SECURITY;
ALTER TABLE fuel_records        ENABLE ROW LEVEL SECURITY;
ALTER TABLE electricity_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE material_records    ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensors             ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_readings     ENABLE ROW LEVEL SECURITY;
ALTER TABLE baselines           ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects            ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_issuances    ENABLE ROW LEVEL SECURITY;
-- (Policies are created per role by the application; see auth service)

-- ===== Helper view for current month per-plant emission summary =====
CREATE OR REPLACE VIEW v_plant_emissions_summary AS
SELECT
    p.id              AS plant_id,
    p.tenant_id,
    p.name            AS plant_name,
    p.plant_type,
    p.province,
    b.base_year,
    b.scope1_tco2 + b.scope2_tco2 AS total_tco2,
    b.intensity_kg_per_t
FROM plants p
LEFT JOIN LATERAL (
    SELECT * FROM baselines
    WHERE plant_id = p.id
    ORDER BY base_year DESC
    LIMIT 1
) b ON TRUE;

-- ===== Seed: default tenant =====
INSERT INTO tenants (id, name, slug, sector, plan)
VALUES ('00000000-0000-0000-0000-000000000000', 'Himalayan Carbon Nepal (default)', 'himalayan', 'multi', 'enterprise')
ON CONFLICT (id) DO NOTHING;
