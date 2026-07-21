"""
Multi-tenant database with audit trail (SQLite-based, swappable to PostgreSQL).
"""
from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class Tenant(BaseModel):
    """A tenant (organization) using the platform."""
    tenant_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    industry: str
    country: str = "Nepal"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    settings: Dict = Field(default_factory=dict)


class AuditEntry(BaseModel):
    """An audit-trail entry for compliance."""
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    action: str                                 # CREATE | UPDATE | DELETE | CALCULATE | EXPORT
    entity_type: str
    entity_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    details: Dict = Field(default_factory=dict)
    ip_address: Optional[str] = None


class Database:
    """SQLite-backed multi-tenant database with audit trail."""

    def __init__(self, path: Path = Path("nepal_decarb.db")) -> None:
        self.path = path
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            industry TEXT,
            country TEXT,
            created_at TEXT,
            settings TEXT
        );

        CREATE TABLE IF NOT EXISTS plants (
            plant_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT,
            location TEXT,
            sector TEXT,
            year INTEGER,
            data TEXT,
            created_at TEXT,
            FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
        );

        CREATE TABLE IF NOT EXISTS emissions_results (
            result_id TEXT PRIMARY KEY,
            plant_id TEXT NOT NULL,
            tier TEXT,
            e_total_tco2 REAL,
            intensity_kgco2_per_t REAL,
            data TEXT,
            created_at TEXT,
            FOREIGN KEY (plant_id) REFERENCES plants(plant_id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            entry_id TEXT PRIMARY KEY,
            tenant_id TEXT,
            user_id TEXT,
            action TEXT,
            entity_type TEXT,
            entity_id TEXT,
            timestamp TEXT,
            details TEXT,
            ip_address TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_plants_tenant ON plants(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id);
        """)
        self.conn.commit()

    def create_tenant(self, tenant: Tenant) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO tenants VALUES (?, ?, ?, ?, ?, ?)",
            (tenant.tenant_id, tenant.name, tenant.industry, tenant.country,
             tenant.created_at, json.dumps(tenant.settings)),
        )
        self.conn.commit()

    def add_audit(self, entry: AuditEntry) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (entry.entry_id, entry.tenant_id, entry.user_id, entry.action,
             entry.entity_type, entry.entity_id, entry.timestamp,
             json.dumps(entry.details), entry.ip_address),
        )
        self.conn.commit()

    def get_audit_log(self, tenant_id: str, limit: int = 100) -> List[AuditEntry]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM audit_log WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT ?",
            (tenant_id, limit),
        )
        return [AuditEntry(
            entry_id=row[0], tenant_id=row[1], user_id=row[2], action=row[3],
            entity_type=row[4], entity_id=row[5], timestamp=row[6],
            details=json.loads(row[7] or "{}"), ip_address=row[8]
        ) for row in cur.fetchall()]

    def close(self) -> None:
        self.conn.close()
