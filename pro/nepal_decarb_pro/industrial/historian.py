"""
Process Historian — production-grade time-series storage.
==========================================================

For development / single-plant: InMemoryHistorian + SQLite.
For production / multi-plant: TimescaleDB (PostgreSQL extension) or InfluxDB.

Pattern: write-through, query-by-time-range, aggregate, downsample.

Why a historian matters:
- Real emissions accounting needs 1-minute resolution, 5-year retention.
- A flat JSON file won't scale past a few weeks.
- Compliance submissions need audit-quality time-series.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TagReading:
    plant_id: str
    tag: str
    value: float
    timestamp: float
    quality: str = "Good"      # Good, Bad, Uncertain
    unit: str = ""
    source: str = "opcua"      # opcua, modbus, manual, derived

    def to_row(self) -> Tuple:
        return (self.plant_id, self.tag, self.value, self.timestamp,
                self.quality, self.unit, self.source)


class Historian(ABC):
    """Abstract base for historian backends."""
    @abstractmethod
    def write(self, reading: TagReading) -> None: ...
    @abstractmethod
    def write_batch(self, readings: Iterable[TagReading]) -> None: ...
    @abstractmethod
    def query(self, plant_id: str, tag: str,
              start_ts: float, end_ts: float) -> List[TagReading]: ...
    @abstractmethod
    def latest(self, plant_id: str, tag: str) -> Optional[TagReading]: ...
    @abstractmethod
    def downsample(self, plant_id: str, tag: str,
                   start_ts: float, end_ts: float,
                   interval_s: float, agg: str = "avg") -> List[Tuple[float, float]]: ...


class InMemoryHistorian(Historian):
    """In-memory ring buffer. For testing, not production."""
    def __init__(self, max_per_tag: int = 1_000_000):
        self._data: Dict[Tuple[str, str], Deque[TagReading]] = {}
        self._max = max_per_tag
        self._lock = threading.Lock()

    def write(self, reading: TagReading) -> None:
        with self._lock:
            key = (reading.plant_id, reading.tag)
            if key not in self._data:
                self._data[key] = deque(maxlen=self._max)
            self._data[key].append(reading)

    def write_batch(self, readings: Iterable[TagReading]) -> None:
        for r in readings:
            self.write(r)

    def query(self, plant_id: str, tag: str, start_ts: float, end_ts: float) -> List[TagReading]:
        with self._lock:
            buf = self._data.get((plant_id, tag), [])
            return [r for r in buf if start_ts <= r.timestamp <= end_ts]

    def latest(self, plant_id: str, tag: str) -> Optional[TagReading]:
        with self._lock:
            buf = self._data.get((plant_id, tag), [])
            return buf[-1] if buf else None

    def downsample(self, plant_id: str, tag: str, start_ts: float, end_ts: float,
                   interval_s: float, agg: str = "avg") -> List[Tuple[float, float]]:
        raw = self.query(plant_id, tag, start_ts, end_ts)
        buckets: Dict[int, List[float]] = {}
        for r in raw:
            b = int(r.timestamp // interval_s)
            buckets.setdefault(b, []).append(r.value)
        result: List[Tuple[float, float]] = []
        for b in sorted(buckets):
            ts = b * interval_s
            vals = buckets[b]
            if agg == "avg":
                v = sum(vals) / len(vals)
            elif agg == "min":
                v = min(vals)
            elif agg == "max":
                v = max(vals)
            elif agg == "sum":
                v = sum(vals)
            else:
                v = sum(vals) / len(vals)
            result.append((ts, v))
        return result


class SQLiteHistorian(Historian):
    """SQLite-backed historian. Good for single-plant, 5+ year retention.

    Tables:
      - readings(plant_id, tag, value, timestamp, quality, unit, source)
      - Index on (plant_id, tag, timestamp)
    """
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS readings (
        plant_id TEXT NOT NULL,
        tag TEXT NOT NULL,
        value REAL NOT NULL,
        timestamp REAL NOT NULL,
        quality TEXT NOT NULL DEFAULT 'Good',
        unit TEXT DEFAULT '',
        source TEXT DEFAULT 'opcua'
    );
    CREATE INDEX IF NOT EXISTS idx_readings_ptt
        ON readings(plant_id, tag, timestamp);
    CREATE INDEX IF NOT EXISTS idx_readings_ts
        ON readings(timestamp);
    """

    def __init__(self, db_path: str = "historian.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.executescript(self.SCHEMA)
            conn.commit()
            conn.close()
        logger.info("SQLiteHistorian initialized at %s", self.db_path)

    def write(self, reading: TagReading) -> None:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO readings(plant_id,tag,value,timestamp,quality,unit,source)"
                " VALUES (?,?,?,?,?,?,?)",
                reading.to_row(),
            )
            conn.commit()
            conn.close()

    def write_batch(self, readings: Iterable[TagReading]) -> None:
        rows = [r.to_row() for r in readings]
        if not rows:
            return
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.executemany(
                "INSERT INTO readings(plant_id,tag,value,timestamp,quality,unit,source)"
                " VALUES (?,?,?,?,?,?,?)",
                rows,
            )
            conn.commit()
            conn.close()

    def query(self, plant_id: str, tag: str, start_ts: float, end_ts: float) -> List[TagReading]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT plant_id,tag,value,timestamp,quality,unit,source FROM readings"
            " WHERE plant_id=? AND tag=? AND timestamp BETWEEN ? AND ?"
            " ORDER BY timestamp",
            (plant_id, tag, start_ts, end_ts),
        ).fetchall()
        conn.close()
        return [TagReading(*r) for r in rows]

    def latest(self, plant_id: str, tag: str) -> Optional[TagReading]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT plant_id,tag,value,timestamp,quality,unit,source FROM readings"
            " WHERE plant_id=? AND tag=? ORDER BY timestamp DESC LIMIT 1",
            (plant_id, tag),
        ).fetchone()
        conn.close()
        return TagReading(*row) if row else None

    def downsample(self, plant_id: str, tag: str, start_ts: float, end_ts: float,
                   interval_s: float, agg: str = "avg") -> List[Tuple[float, float]]:
        agg_sql = {"avg":"AVG(value)","min":"MIN(value)","max":"MAX(value)","sum":"SUM(value)"}.get(agg, "AVG(value)")
        bucket_expr = "CAST(timestamp / ? AS INTEGER) * ?"
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            f"SELECT {bucket_expr} AS bucket, {agg_sql} AS value FROM readings"
            f" WHERE plant_id=? AND tag=? AND timestamp BETWEEN ? AND ?"
            f" GROUP BY bucket ORDER BY bucket",
            (interval_s, interval_s, plant_id, tag, start_ts, end_ts),
        ).fetchall()
        conn.close()
        return [(r[0], r[1]) for r in rows]


class TimescaleDBHistorian(Historian):
    """TimescaleDB (PostgreSQL extension) historian for multi-plant production.

    Schema:
        CREATE TABLE readings (
            ts TIMESTAMPTZ NOT NULL,
            plant_id TEXT NOT NULL,
            tag TEXT NOT NULL,
            value DOUBLE PRECISION NOT NULL,
            quality TEXT NOT NULL DEFAULT 'Good',
            unit TEXT DEFAULT '',
            source TEXT DEFAULT 'opcua'
        );
        SELECT create_hypertable('readings', 'ts');
        CREATE INDEX idx_plant_tag ON readings(plant_id, tag, ts DESC);
    """
    def __init__(self, dsn: str = "postgresql://user:pass@localhost:5532/historian",
                 batch_size: int = 1000):
        self.dsn = dsn
        self.batch_size = batch_size
        self._buffer: List[TagReading] = []
        self._lock = threading.Lock()
        self._conn = None
        try:
            import psycopg
            self._psycopg = psycopg
            self._conn = psycopg.connect(self.dsn)
            logger.info("TimescaleDBHistorian connected")
        except Exception as e:
            logger.warning("TimescaleDB not available: %s — falling back to SQLite", e)
            self._fallback = SQLiteHistorian("historian_fallback.db")
        else:
            self._fallback = None

    def write(self, reading: TagReading) -> None:
        if self._fallback:
            self._fallback.write(reading)
            return
        with self._lock:
            self._buffer.append(reading)
            if len(self._buffer) >= self.batch_size:
                self._flush()

    def _flush(self) -> None:
        if not self._buffer or self._conn is None:
            return
        with self._conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO readings(ts,plant_id,tag,value,quality,unit,source)"
                " VALUES (to_timestamp(%s),%s,%s,%s,%s,%s,%s)",
                [(r.timestamp, r.plant_id, r.tag, r.value, r.quality, r.unit, r.source)
                 for r in self._buffer],
            )
            self._conn.commit()
        self._buffer.clear()

    def write_batch(self, readings: Iterable[TagReading]) -> None:
        for r in readings:
            self.write(r)
        self._flush()

    def query(self, plant_id: str, tag: str, start_ts: float, end_ts: float) -> List[TagReading]:
        if self._fallback:
            return self._fallback.query(plant_id, tag, start_ts, end_ts)
        if self._conn is None:
            return []
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXTRACT(EPOCH FROM ts),plant_id,tag,value,quality,unit,source"
                " FROM readings WHERE plant_id=%s AND tag=%s"
                " AND ts BETWEEN to_timestamp(%s) AND to_timestamp(%s) ORDER BY ts",
                (plant_id, tag, start_ts, end_ts),
            )
            rows = cur.fetchall()
        return [TagReading(plant_id=r[1], tag=r[2], value=r[3], timestamp=r[0],
                           quality=r[4], unit=r[5], source=r[6]) for r in rows]

    def latest(self, plant_id: str, tag: str) -> Optional[TagReading]:
        if self._fallback:
            return self._fallback.latest(plant_id, tag)
        if self._conn is None:
            return None
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXTRACT(EPOCH FROM ts),plant_id,tag,value,quality,unit,source"
                " FROM readings WHERE plant_id=%s AND tag=%s ORDER BY ts DESC LIMIT 1",
                (plant_id, tag),
            )
            row = cur.fetchone()
        if not row:
            return None
        return TagReading(plant_id=row[1], tag=row[2], value=row[3], timestamp=row[0],
                          quality=row[4], unit=row[5], source=row[6])

    def downsample(self, plant_id: str, tag: str, start_ts: float, end_ts: float,
                   interval_s: float, agg: str = "avg") -> List[Tuple[float, float]]:
        if self._fallback:
            return self._fallback.downsample(plant_id, tag, start_ts, end_ts, interval_s, agg)
        if self._conn is None:
            return []
        bucket = f"{int(interval_s)} seconds"
        agg_sql = {"avg":"AVG(value)","min":"MIN(value)","max":"MAX(value)","sum":"SUM(value)"}.get(agg, "AVG(value)")
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT EXTRACT(EPOCH FROM time_bucket('{bucket}', ts)), {agg_sql}"
                f" FROM readings WHERE plant_id=%s AND tag=%s"
                f" AND ts BETWEEN to_timestamp(%s) AND to_timestamp(%s)"
                f" GROUP BY 1 ORDER BY 1",
                (plant_id, tag, start_ts, end_ts),
            )
            rows = cur.fetchall()
        return [(r[0], r[1]) for r in rows]


# Default factory
def default_historian() -> Historian:
    return SQLiteHistorian("nepal_decarb_historian.db")
