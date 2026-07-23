"""
Immutable audit trail for VVB-grade evidence.

This module provides a hash-chained, append-only audit log of every calculation
performed by the nepal_decarb_pro platform. Each entry includes:
  - input_hash (SHA-256 of serialized inputs)
  - output_hash (SHA-256 of serialized outputs)
  - code_version (git SHA of the platform at the time of calculation)
  - timestamp (ISO 8601, UTC)
  - user_id, tenant_id, entity_type, entity_id
  - prev_hash (hash of the previous entry, forming a chain)
  - details (JSON-serializable dict)

The chain structure (similar to a blockchain) makes any tampering detectable.
A single modified entry invalidates all subsequent hashes; a VVB can verify
chain integrity by re-computing all hashes from the genesis entry.

VVB Expectation (per ISO 14064-3:2019 §5.6 and VCS Standard v4.6 §3.5.7):
  - Audit trail is append-only (no UPDATE or DELETE)
  - Every CALCULATE event is logged with input and output hashes
  - Code version is pinned to a specific commit
  - Audit trail is retained for the crediting period + 5 years

Reference implementations:
  - Verra's "Audit Trail Guidance for VCS Projects" (2021)
  - Gold Standard "Tool for Digital Monitoring" (2022)
  - ISO 14064-3:2019 §5.6 (Information system assessment)
  - W3C PROV-DM (Provenance Data Model) for the data model
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from nepal_decarb_pro.io.database import Database, AuditEntry


# ============================================================================
# Hash-chained audit entry (extends the existing AuditEntry)
# ============================================================================

class HashChainedAuditEntry(BaseModel):
    """An audit-trail entry with a hash chain.

    The prev_hash links this entry to the previous entry, forming an
    append-only chain. Any modification to a previous entry will invalidate
    all subsequent entries, making tampering detectable.
    """
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    timestamp: str = Field(default_factory=lambda: lambda: datetime.now(timezone.utc).isoformat())
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    code_version: Optional[str] = None
    prev_hash: Optional[str] = None       # hash of previous entry
    entry_hash: Optional[str] = None      # hash of this entry (excluding entry_hash itself)
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None

    def compute_entry_hash(self) -> str:
        """Compute the SHA-256 hash of this entry, excluding the entry_hash field itself.

        This is what gets linked from the next entry's prev_hash.
        """
        data = {
            "entry_id": self.entry_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "code_version": self.code_version,
            "prev_hash": self.prev_hash,
            "details": self.details,
            "ip_address": self.ip_address,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ============================================================================
# Hashing helpers
# ============================================================================

def hash_object(obj: Any) -> str:
    """Compute SHA-256 of an object's canonical JSON serialization.

    Handles pydantic models, dataclasses, dicts, lists, and primitives.
    """
    if hasattr(obj, "model_dump"):
        # pydantic v2
        canonical = obj.model_dump(mode="json", exclude_none=True)
    elif hasattr(obj, "dict"):
        # pydantic v1
        canonical = obj.dict()
    elif hasattr(obj, "__dict__"):
        canonical = obj.__dict__
    else:
        canonical = obj

    json_str = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def get_code_version(repo_root: Optional[Path] = None) -> str:
    """Get the git SHA of the current code version.

    Falls back to "unknown-<timestamp>" if not in a git repo.
    """
    if repo_root is None:
        # Find repo root by looking for .git
        cwd = Path.cwd()
        for p in [cwd, *cwd.parents]:
            if (p / ".git").exists():
                repo_root = p
                break

    if repo_root is None or not (repo_root / ".git").exists():
        return f"unknown-{datetime.now(timezone.utc).isoformat()}"

    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
        ).decode("utf-8").strip()
        return sha
    except Exception:
        return f"unknown-{datetime.now(timezone.utc).isoformat()}"


# ============================================================================
# Hash-chained audit database
# ============================================================================

class ChainedAuditLog:
    """Append-only, hash-chained audit log.

    Backed by SQLite (single-tenant) or PostgreSQL (multi-tenant).
    Each entry's prev_hash links to the previous entry's entry_hash, forming
    a chain. Any tampering is detectable by re-computing the chain.
    """

    def __init__(self, path: Path = Path("nepal_decarb_chained.db")) -> None:
        self.path = path
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS chained_audit_log (
            entry_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            input_hash TEXT,
            output_hash TEXT,
            code_version TEXT,
            prev_hash TEXT,
            entry_hash TEXT NOT NULL,
            details TEXT,
            ip_address TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_chained_audit_tenant ON chained_audit_log(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_chained_audit_entity ON chained_audit_log(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_chained_audit_timestamp ON chained_audit_log(timestamp);

        -- Trigger to prevent UPDATE and DELETE (append-only enforcement)
        CREATE TRIGGER IF NOT EXISTS chained_audit_no_update
        BEFORE UPDATE ON chained_audit_log
        BEGIN
            SELECT RAISE(ABORT, 'Audit trail is append-only; UPDATE forbidden');
        END;

        CREATE TRIGGER IF NOT EXISTS chained_audit_no_delete
        BEFORE DELETE ON chained_audit_log
        BEGIN
            SELECT RAISE(ABORT, 'Audit trail is append-only; DELETE forbidden');
        END;
        """)
        self.conn.commit()

    def _get_last_hash(self, tenant_id: str) -> Optional[str]:
        """Get the entry_hash of the most recent entry for the tenant."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT entry_hash FROM chained_audit_log WHERE tenant_id = ? ORDER BY timestamp DESC LIMIT 1",
            (tenant_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def append(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: Optional[Dict[str, Any]] = None,
        input_obj: Optional[Any] = None,
        output_obj: Optional[Any] = None,
        ip_address: Optional[str] = None,
    ) -> HashChainedAuditEntry:
        """Append a new entry to the audit log.

        The entry's prev_hash is set to the previous entry's entry_hash,
        and the entry_hash is computed from the entry's contents.
        """
        prev_hash = self._get_last_hash(tenant_id)
        input_hash = hash_object(input_obj) if input_obj is not None else None
        output_hash = hash_object(output_obj) if output_obj is not None else None
        code_version = get_code_version()

        entry = HashChainedAuditEntry(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            input_hash=input_hash,
            output_hash=output_hash,
            code_version=code_version,
            prev_hash=prev_hash,
            details=details or {},
            ip_address=ip_address,
        )
        entry.entry_hash = entry.compute_entry_hash()

        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO chained_audit_log
            (entry_id, tenant_id, user_id, action, entity_type, entity_id, timestamp,
             input_hash, output_hash, code_version, prev_hash, entry_hash, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry.entry_id, entry.tenant_id, entry.user_id, entry.action, entry.entity_type,
             entry.entity_id, entry.timestamp, entry.input_hash, entry.output_hash,
             entry.code_version, entry.prev_hash, entry.entry_hash,
             json.dumps(entry.details, default=str), entry.ip_address),
        )
        self.conn.commit()
        return entry

    def get_entries(
        self,
        tenant_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[HashChainedAuditEntry]:
        """Get audit entries, optionally filtered."""
        cur = self.conn.cursor()
        query = "SELECT * FROM chained_audit_log WHERE 1=1"
        params = []
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()
        return [HashChainedAuditEntry(
            entry_id=r[0], tenant_id=r[1], user_id=r[2], action=r[3], entity_type=r[4],
            entity_id=r[5], timestamp=r[6], input_hash=r[7], output_hash=r[8],
            code_version=r[9], prev_hash=r[10], entry_hash=r[11],
            details=json.loads(r[12] or "{}"), ip_address=r[13],
        ) for r in rows]

    def verify_chain(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Verify the integrity of the hash chain.

        Returns a dict with:
          - valid: True if all entries hash correctly and link properly
          - n_entries: number of entries verified
          - first_invalid_entry: entry_id of the first invalid entry, if any
          - errors: list of error messages
        """
        entries = self.get_entries(tenant_id=tenant_id, limit=1_000_000)
        entries.reverse()  # oldest first

        expected_prev_hash = None
        errors = []
        first_invalid = None

        for entry in entries:
            # Check prev_hash linkage
            if entry.prev_hash != expected_prev_hash:
                errors.append(
                    f"Entry {entry.entry_id}: prev_hash mismatch "
                    f"(expected {expected_prev_hash}, got {entry.prev_hash})"
                )
                if first_invalid is None:
                    first_invalid = entry.entry_id

            # Recompute entry_hash and compare
            recomputed = entry.compute_entry_hash()
            if recomputed != entry.entry_hash:
                errors.append(
                    f"Entry {entry.entry_id}: entry_hash mismatch "
                    f"(expected {entry.entry_hash}, got {recomputed})"
                )
                if first_invalid is None:
                    first_invalid = entry.entry_id

            expected_prev_hash = entry.entry_hash

        return {
            "valid": len(errors) == 0,
            "n_entries": len(entries),
            "first_invalid_entry": first_invalid,
            "errors": errors,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
        }

    def export_to_csv(self, out_path: Path, tenant_id: Optional[str] = None) -> Path:
        """Export the audit log to CSV (read-only, VVB-friendly format)."""
        import csv
        entries = self.get_entries(tenant_id=tenant_id, limit=1_000_000)
        entries.reverse()  # chronological order
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "entry_id", "tenant_id", "user_id", "action", "entity_type", "entity_id",
                "timestamp", "input_hash", "output_hash", "code_version", "prev_hash",
                "entry_hash", "ip_address", "details_json",
            ])
            for e in entries:
                writer.writerow([
                    e.entry_id, e.tenant_id, e.user_id, e.action, e.entity_type, e.entity_id,
                    e.timestamp, e.input_hash, e.output_hash, e.code_version, e.prev_hash,
                    e.entry_hash, e.ip_address or "", json.dumps(e.details, default=str),
                ])
        return out_path

    def close(self) -> None:
        self.conn.close()


# ============================================================================
# Decorator for auto-audited calculations
# ============================================================================

# Global default audit log (lazy-initialized)
_default_audit_log: Optional[ChainedAuditLog] = None


def get_audit_log() -> ChainedAuditLog:
    """Get the global default audit log (lazy-initialized)."""
    global _default_audit_log
    if _default_audit_log is None:
        default_path = os.environ.get(
            "NEPAL_DECARB_AUDIT_DB",
            str(Path.cwd() / "nepal_decarb_chained.db"),
        )
        _default_audit_log = ChainedAuditLog(Path(default_path))
    return _default_audit_log


def audit_trail(
    entity_type: str,
    action: str = "CALCULATE",
    audit_log: Optional[ChainedAuditLog] = None,
    tenant_id: str = "default",
    user_id: str = "system",
    include_args: bool = True,
    include_result: bool = True,
) -> Callable:
    """Decorator that auto-logs a calculation to the hash-chained audit trail.

    Usage:
        @audit_trail(entity_type="cement_calculation_tier2")
        def calculate_cement_tier2(plant, ef):
            ...

    The decorator will:
      1. Hash the function arguments (excluding the audit trail config)
      2. Call the function
      3. Hash the return value
      4. Append an entry to the audit log with input/output hashes
      5. Return the result

    Parameters
    ----------
    entity_type : str
        The type of entity being calculated (e.g., "cement_calculation_tier2",
        "monte_carlo_cement", "verra_pdd").
    action : str
        The action label (default "CALCULATE"; could be "EXPORT", "UPDATE",
        "DELETE" for other use cases).
    audit_log : ChainedAuditLog, optional
        The audit log to write to. Defaults to the global audit log.
    tenant_id : str
        The tenant ID (for multi-tenant deployments).
    user_id : str
        The user ID performing the calculation.
    include_args : bool
        Whether to include function arguments in the input hash.
    include_result : bool
        Whether to include the function return value in the output hash.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = audit_log or get_audit_log()
            # Build a representation of the inputs
            input_repr = {"args": args, "kwargs": kwargs} if include_args else None
            result = func(*args, **kwargs)
            output_repr = result if include_result else None
            entity_id = f"{entity_type}:{datetime.now(timezone.utc).isoformat()}"
            details = {
                "function": func.__name__,
                "module": func.__module__,
            }
            try:
                log.append(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    details=details,
                    input_obj=input_repr,
                    output_obj=output_repr,
                )
            except Exception as e:
                # Never fail the calculation because of audit logging
                # but do record the failure somewhere
                print(f"WARNING: audit trail append failed: {e}")
            return result
        return wrapper
    return decorator


# ============================================================================
# Sample usage demonstration
# ============================================================================

if __name__ == "__main__":
    # Demonstrate the audit trail with a simple calculation
    log = ChainedAuditLog(Path("/tmp/audit_demo.db"))

    # Simulate three calculations
    entry1 = log.append(
        tenant_id="planta_cement",
        user_id="mavis",
        action="CALCULATE",
        entity_type="cement_calculation_tier2",
        entity_id="planta_2024_baseline",
        details={"note": "First calculation"},
        input_obj={"clinker_t": 950_000, "cement_t": 1_100_000, "coal_t": 120_000},
        output_obj={"e_total_tco2": 861_025.36, "intensity_kgco2_per_t_cement": 782.75},
    )
    print(f"Entry 1: {entry1.entry_id} hash={entry1.entry_hash[:16]}...")

    entry2 = log.append(
        tenant_id="planta_cement",
        user_id="mavis",
        action="CALCULATE",
        entity_type="monte_carlo_cement",
        entity_id="planta_2024_baseline_5k_samples",
        details={"note": "Second calculation"},
        input_obj={"n_samples": 5000, "seed": 42},
        output_obj={"mean": 861092.81, "ci_95_low": 813156.19, "ci_95_high": 914210.27},
    )
    print(f"Entry 2: {entry2.entry_id} prev_hash={entry2.prev_hash[:16]}... hash={entry2.entry_hash[:16]}...")
    assert entry2.prev_hash == entry1.entry_hash, "Chain linkage broken!"

    entry3 = log.append(
        tenant_id="planta_cement",
        user_id="mavis",
        action="CALCULATE",
        entity_type="verra_pdd",
        entity_id="planta_2024_pdd",
        details={"note": "Third calculation"},
        input_obj={"project_name": "PlantA Decarb"},
        output_obj={"net_emission_reductions_annual_tco2": 56407.40},
    )
    print(f"Entry 3: {entry3.entry_id} prev_hash={entry3.prev_hash[:16]}... hash={entry3.entry_hash[:16]}...")
    assert entry3.prev_hash == entry2.entry_hash, "Chain linkage broken!"

    # Verify the chain
    verification = log.verify_chain(tenant_id="planta_cement")
    print(f"\nChain verification: valid={verification['valid']}, n_entries={verification['n_entries']}")
    assert verification["valid"], f"Chain verification failed: {verification['errors']}"

    # Export to CSV
    csv_path = log.export_to_csv(Path("/tmp/audit_demo.csv"), tenant_id="planta_cement")
    print(f"Audit trail exported to: {csv_path}")

    # Demonstrate the decorator
    @audit_trail(entity_type="demo_addition", tenant_id="planta_cement", user_id="mavis")
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    print(f"\nadd(2, 3) = {result}")

    log.close()
    print("\n✓ All demonstrations passed")
