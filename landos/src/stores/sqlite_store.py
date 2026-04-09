"""SQLite persistence layer for LandOS pipeline output.

Stores pipeline results (clusters, parcels, listings, opportunities, events,
subdivisions) in a single SQLite database so the FastAPI server can query them.

Design:
  - Each object is stored as a JSON blob with indexed columns for common queries.
  - Pydantic models serialize via .model_dump_json() and deserialize via .model_validate_json().
  - Plain dataclasses (StallAssessment, ParcelClusterResult) use json.dumps/loads.
  - Tables are created on first use (CREATE IF NOT EXISTS).
  - All writes are upserts (INSERT OR REPLACE).
"""

from __future__ import annotations

import json
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.models.listing import Listing
from src.models.municipality import MunicipalEvent
from src.models.opportunity import Opportunity
from src.models.owner import OwnerCluster
from src.models.parcel import Parcel
from src.models.development import Subdivision

# ── Default DB location ──────────────────────────────────────────────────────

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "landos.db"

# ── Singleton for API server (avoids opening a new connection per request) ────

_instances: dict[str, "SQLiteStore"] = {}


def get_store(db_path: Path | str | None = None) -> "SQLiteStore":
    """Return a shared SQLiteStore instance for the given path.

    The API server should use this instead of SQLiteStore() directly
    to avoid opening a new connection on every request.
    """
    key = str(db_path or DEFAULT_DB_PATH)
    if key not in _instances:
        _instances[key] = SQLiteStore(db_path=db_path)
    return _instances[key]


def _str(val: Any) -> Optional[str]:
    """Convert UUID or other to string for SQLite, None-safe."""
    if val is None:
        return None
    return str(val)


def _json(val: Any) -> Optional[str]:
    """Serialize a list/dict to JSON string for SQLite, None-safe."""
    if val is None:
        return None
    return json.dumps(val, default=str)


def _history_fingerprint(listing: Listing) -> str:
    payload = {
        "listing_key": listing.listing_key,
        "status": listing.standard_status.value if listing.standard_status else None,
        "list_price": listing.list_price,
        "dom": listing.dom,
        "cdom": listing.cdom,
        "list_date": str(listing.list_date) if listing.list_date else None,
        "expiration_date": str(listing.expiration_date) if listing.expiration_date else None,
        "off_market_date": str(listing.off_market_date) if listing.off_market_date else None,
        "withdrawal_date": str(listing.withdrawal_date) if listing.withdrawal_date else None,
        "back_on_market_date": str(listing.back_on_market_date) if listing.back_on_market_date else None,
        "status_change_timestamp": str(listing.status_change_timestamp) if listing.status_change_timestamp else None,
        "major_change_timestamp": str(listing.major_change_timestamp) if listing.major_change_timestamp else None,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


class SQLiteStore:
    """Unified SQLite persistence for all LandOS pipeline objects."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=OFF")
        self._create_tables()

    def _create_tables(self) -> None:
        c = self._conn
        c.executescript("""
            CREATE TABLE IF NOT EXISTS listings (
                listing_key TEXT PRIMARY KEY,
                listing_id TEXT NOT NULL,
                source_system TEXT NOT NULL,
                standard_status TEXT,
                list_price INTEGER,
                property_type TEXT,
                municipality_id TEXT,
                address_raw TEXT,
                latitude REAL,
                longitude REAL,
                lot_size_acres REAL,
                dom INTEGER,
                cdom INTEGER,
                listing_agent_name TEXT,
                listing_agent_id TEXT,
                listing_office_name TEXT,
                listing_office_id TEXT,
                seller_name_raw TEXT,
                private_remarks TEXT,
                subdivision_name_raw TEXT,
                owner_name_raw TEXT,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS parcels (
                regrid_id TEXT PRIMARY KEY,
                parcel_id TEXT NOT NULL,
                municipality_id TEXT,
                county TEXT,
                vacancy_status TEXT,
                acreage REAL,
                owner_name_raw TEXT,
                opportunity_score REAL,
                centroid_lat REAL,
                centroid_lon REAL,
                subdivision_id TEXT,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_parcels_municipality
                ON parcels(municipality_id);
            CREATE INDEX IF NOT EXISTS idx_parcels_vacancy
                ON parcels(vacancy_status);
            CREATE INDEX IF NOT EXISTS idx_parcels_subdivision
                ON parcels(subdivision_id);

            CREATE TABLE IF NOT EXISTS clusters (
                cluster_id TEXT PRIMARY KEY,
                cluster_type TEXT NOT NULL,
                detection_method TEXT,
                member_count INTEGER,
                municipality_id TEXT,
                total_acreage REAL,
                total_list_value INTEGER,
                group_key TEXT,
                parcel_count INTEGER,
                listing_count INTEGER,
                has_active_listings INTEGER DEFAULT 0,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_clusters_type
                ON clusters(cluster_type);
            CREATE INDEX IF NOT EXISTS idx_clusters_municipality
                ON clusters(municipality_id);

            CREATE TABLE IF NOT EXISTS opportunities (
                opportunity_id TEXT PRIMARY KEY,
                opportunity_type TEXT NOT NULL,
                municipality_id TEXT,
                subdivision_id TEXT,
                status TEXT,
                opportunity_score REAL,
                parcel_count INTEGER,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_opps_type
                ON opportunities(opportunity_type);
            CREATE INDEX IF NOT EXISTS idx_opps_municipality
                ON opportunities(municipality_id);

            CREATE TABLE IF NOT EXISTS subdivisions (
                subdivision_id TEXT PRIMARY KEY,
                name TEXT,
                municipality_id TEXT,
                county TEXT,
                total_lots INTEGER,
                vacant_lots INTEGER,
                vacancy_ratio REAL,
                stall_flag INTEGER,
                stall_score REAL,
                infrastructure_status TEXT,
                plat_date TEXT,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_subs_municipality
                ON subdivisions(municipality_id);
            CREATE INDEX IF NOT EXISTS idx_subs_stall
                ON subdivisions(stall_flag);

            CREATE TABLE IF NOT EXISTS municipal_events (
                municipal_event_id TEXT PRIMARY KEY,
                municipality_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT,
                source_system TEXT,
                subdivision_id TEXT,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_muni_events_municipality
                ON municipal_events(municipality_id);

            CREATE TABLE IF NOT EXISTS owners (
                owner_id TEXT PRIMARY KEY,
                owner_name_normalized TEXT,
                entity_type TEXT,
                parcel_count INTEGER,
                total_acreage_owned REAL,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pipeline_signals (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_id TEXT,
                entity_ref_summary TEXT,
                fired_rules TEXT,
                payload_summary TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_signals_created
                ON pipeline_signals(created_at);
            CREATE INDEX IF NOT EXISTS idx_signals_type
                ON pipeline_signals(event_type);

            CREATE TABLE IF NOT EXISTS pipeline_stats (
                stat_key TEXT PRIMARY KEY,
                stat_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS listing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                snapshot_fingerprint TEXT,
                listing_key TEXT NOT NULL,
                snapshot_status TEXT NOT NULL,
                list_price INTEGER,
                cdom INTEGER,
                dom INTEGER,
                original_list_price INTEGER,
                previous_list_price REAL,
                parcel_number TEXT,
                subdivision_name TEXT,
                seller_name TEXT,
                owner_name_raw TEXT,
                listing_agent_name TEXT,
                listing_office_name TEXT,
                address_raw TEXT,
                private_remarks TEXT,
                showing_instructions TEXT,
                list_date TEXT,
                close_date TEXT,
                expiration_date TEXT,
                off_market_date TEXT,
                withdrawal_date TEXT,
                back_on_market_date TEXT,
                latitude REAL,
                longitude REAL,
                lot_size_acres REAL,
                data_json TEXT NOT NULL,
                ingested_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_history_key ON listing_history(listing_key);
            CREATE INDEX IF NOT EXISTS idx_history_parcel ON listing_history(parcel_number);
            CREATE INDEX IF NOT EXISTS idx_history_subdivision ON listing_history(subdivision_name);
            CREATE INDEX IF NOT EXISTS idx_history_status ON listing_history(snapshot_status);
            CREATE INDEX IF NOT EXISTS idx_history_seller ON listing_history(seller_name);
            CREATE TABLE IF NOT EXISTS strategic_opportunities (
                opportunity_id TEXT PRIMARY KEY,
                name TEXT,
                opportunity_type TEXT,
                precedence_tier INTEGER DEFAULT 4,
                municipality_id TEXT,
                lot_count INTEGER,
                total_acreage REAL,
                infrastructure_invested INTEGER DEFAULT 0,
                stall_confidence REAL,
                vacancy_ratio REAL,
                composite_score REAL,
                has_active_listings INTEGER DEFAULT 0,
                listing_count INTEGER DEFAULT 0,
                owner_name TEXT,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_strategic_score
                ON strategic_opportunities(composite_score DESC);
            CREATE INDEX IF NOT EXISTS idx_strategic_lots
                ON strategic_opportunities(lot_count);

            CREATE TABLE IF NOT EXISTS listing_genealogy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_key TEXT NOT NULL,
                related_listing_key TEXT,
                relationship TEXT,
                event_type TEXT,
                event_date TEXT,
                list_price INTEGER,
                status TEXT,
                agent_name TEXT,
                office_name TEXT,
                days_on_market INTEGER,
                source_data_json TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_genealogy_listing
                ON listing_genealogy(listing_key);
            CREATE INDEX IF NOT EXISTS idx_genealogy_related
                ON listing_genealogy(related_listing_key);

            CREATE TABLE IF NOT EXISTS market_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT NOT NULL,
                county TEXT NOT NULL,
                property_type TEXT NOT NULL,
                period TEXT NOT NULL,
                value REAL,
                year INTEGER,
                month INTEGER,
                source_data_json TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_mkt_stat_type
                ON market_statistics(stat_type);
            CREATE INDEX IF NOT EXISTS idx_mkt_period
                ON market_statistics(period);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_mkt_unique
                ON market_statistics(stat_type, county, property_type, period);
        """)
        self._ensure_column("listing_history", "run_id", "TEXT")
        self._ensure_column("listing_history", "snapshot_fingerprint", "TEXT")
        self._ensure_column("listing_history", "owner_name_raw", "TEXT")
        self._ensure_column("strategic_opportunities", "precedence_tier", "INTEGER DEFAULT 4")
        c.execute("CREATE INDEX IF NOT EXISTS idx_history_run ON listing_history(run_id)")
        c.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_history_run_fingerprint "
            "ON listing_history(run_id, snapshot_fingerprint)"
        )
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_strategic_tier_score "
            "ON strategic_opportunities(precedence_tier ASC, composite_score DESC)"
        )
        c.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        cols = {
            row["name"]
            for row in self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in cols:
            self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    # ── Listings ──────────────────────────────────────────────────────────────

    def save_listing(self, listing: Listing) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO listings
               (listing_key, listing_id, source_system, standard_status, list_price,
                property_type, municipality_id, address_raw, latitude, longitude,
                lot_size_acres, dom, cdom, listing_agent_name, listing_agent_id,
                listing_office_name, listing_office_id, seller_name_raw,
                private_remarks, subdivision_name_raw, owner_name_raw,
                data_json, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                listing.listing_key,
                _str(listing.listing_id),
                listing.source_system,
                listing.standard_status.value if listing.standard_status else None,
                listing.list_price,
                listing.property_type,
                _str(listing.municipality_id),
                listing.address_raw,
                listing.latitude,
                listing.longitude,
                listing.lot_size_acres,
                listing.dom,
                listing.cdom,
                listing.listing_agent_name,
                listing.listing_agent_id,
                listing.listing_office_name,
                listing.listing_office_id,
                listing.seller_name_raw,
                listing.private_remarks,
                listing.subdivision_name_raw,
                getattr(listing, "owner_name_raw", None)
                or listing.seller_name_raw,
                listing.model_dump_json(),
                now,
            ),
        )

    def save_listings_batch(self, listings: list[Listing]) -> None:
        for listing in listings:
            self.save_listing(listing)
        self._conn.commit()

    def get_all_listings(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT data_json FROM listings"
        ).fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    def get_listing_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM listings").fetchone()
        return row["c"]

    # ── Parcels ───────────────────────────────────────────────────────────────

    def save_parcel(self, parcel: Parcel) -> None:
        now = datetime.now(timezone.utc).isoformat()
        regrid_id = parcel.source_system_ids.get("regrid_id", _str(parcel.parcel_id))
        centroid_lat = None
        centroid_lon = None
        if parcel.centroid and "coordinates" in parcel.centroid:
            coords = parcel.centroid["coordinates"]
            if len(coords) >= 2:
                centroid_lon, centroid_lat = coords[0], coords[1]

        self._conn.execute(
            """INSERT OR REPLACE INTO parcels
               (regrid_id, parcel_id, municipality_id, county, vacancy_status,
                acreage, owner_name_raw, opportunity_score, centroid_lat,
                centroid_lon, subdivision_id, data_json, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                regrid_id,
                _str(parcel.parcel_id),
                _str(parcel.municipality_id),
                parcel.county,
                parcel.vacancy_status.value if parcel.vacancy_status else None,
                parcel.acreage,
                parcel.owner_name_raw,
                parcel.opportunity_score,
                centroid_lat,
                centroid_lon,
                _str(parcel.subdivision_id),
                parcel.model_dump_json(),
                now,
            ),
        )

    def save_parcels_batch(self, parcels: list[Parcel]) -> None:
        for p in parcels:
            self.save_parcel(p)
        self._conn.commit()

    def get_parcels_by_cluster(self, parcel_ids: list[str]) -> list[dict]:
        if not parcel_ids:
            return []
        placeholders = ",".join("?" * len(parcel_ids))
        rows = self._conn.execute(
            f"SELECT data_json FROM parcels WHERE parcel_id IN ({placeholders})",
            parcel_ids,
        ).fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    def get_vacant_parcel_count(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as c FROM parcels WHERE UPPER(vacancy_status) = 'VACANT'"
        ).fetchone()
        return row["c"]

    def get_total_parcel_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM parcels").fetchone()
        return row["c"]

    # ── Clusters ──────────────────────────────────────────────────────────────

    def save_cluster(self, cluster: OwnerCluster, group_key: str = "",
                     parcel_count: int = 0, listing_count: int = 0,
                     has_active_listings: bool = False) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO clusters
               (cluster_id, cluster_type, detection_method, member_count,
                municipality_id, total_acreage, total_list_value,
                group_key, parcel_count, listing_count, has_active_listings,
                data_json, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                _str(cluster.cluster_id),
                cluster.cluster_type.value if hasattr(cluster.cluster_type, 'value') else str(cluster.cluster_type),
                cluster.detection_method,
                cluster.member_count,
                _str(cluster.municipality_id),
                cluster.total_acreage,
                cluster.total_list_value,
                group_key,
                parcel_count,
                listing_count,
                1 if has_active_listings else 0,
                cluster.model_dump_json(),
                now,
            ),
        )

    def save_clusters_batch(self, clusters: list[tuple[OwnerCluster, str, int, int, bool]]) -> None:
        for cluster, group_key, parcel_count, listing_count, has_listings in clusters:
            self.save_cluster(cluster, group_key, parcel_count, listing_count, has_listings)
        self._conn.commit()

    def get_all_clusters(self, min_lots: int | None = None,
                         infrastructure: bool | None = None,
                         cluster_type: str | None = None) -> list[dict]:
        query = "SELECT data_json, group_key, parcel_count, listing_count, has_active_listings, cluster_type FROM clusters WHERE 1=1"
        params: list[Any] = []
        if min_lots is not None:
            query += " AND parcel_count >= ?"
            params.append(min_lots)
        if cluster_type is not None:
            query += " AND cluster_type = ?"
            params.append(cluster_type)
        query += " ORDER BY parcel_count DESC"
        rows = self._conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            data = json.loads(r["data_json"])
            data["_group_key"] = r["group_key"]
            data["_parcel_count"] = r["parcel_count"]
            data["_listing_count"] = r["listing_count"]
            data["_has_active_listings"] = bool(r["has_active_listings"])
            data["_cluster_type"] = r["cluster_type"]
            results.append(data)
        return results

    def get_cluster_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM clusters").fetchone()
        return row["c"]

    def get_clusters_with_listings_count(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as c FROM clusters WHERE has_active_listings = 1"
        ).fetchone()
        return row["c"]

    # ── Opportunities ─────────────────────────────────────────────────────────

    def save_opportunity(self, opp: Opportunity) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO opportunities
               (opportunity_id, opportunity_type, municipality_id, subdivision_id,
                status, opportunity_score, parcel_count, data_json, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                _str(opp.opportunity_id),
                opp.opportunity_type.value if hasattr(opp.opportunity_type, 'value') else str(opp.opportunity_type),
                _str(opp.municipality_id),
                _str(opp.subdivision_id),
                opp.status.value if hasattr(opp.status, 'value') else str(opp.status),
                opp.opportunity_score,
                len(opp.parcel_ids) if opp.parcel_ids else 0,
                opp.model_dump_json(),
                now,
            ),
        )

    def save_opportunities_batch(self, opps: list[Opportunity]) -> None:
        for opp in opps:
            self.save_opportunity(opp)
        self._conn.commit()

    def get_all_opportunities(self, opp_type: str | None = None) -> list[dict]:
        query = "SELECT data_json FROM opportunities WHERE 1=1"
        params: list[Any] = []
        if opp_type is not None:
            query += " AND opportunity_type = ?"
            params.append(opp_type)
        query += " ORDER BY opportunity_score DESC NULLS LAST"
        rows = self._conn.execute(query, params).fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    def get_opportunity_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) as c FROM opportunities").fetchone()
        return row["c"]

    # ── Subdivisions ──────────────────────────────────────────────────────────

    def save_subdivision(self, sub: Subdivision) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO subdivisions
               (subdivision_id, name, municipality_id, county, total_lots,
                vacant_lots, vacancy_ratio, stall_flag, stall_score,
                infrastructure_status, plat_date, data_json, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                _str(sub.subdivision_id),
                sub.name,
                _str(sub.municipality_id),
                sub.county,
                sub.total_lots,
                sub.vacant_lots,
                sub.vacancy_ratio,
                1 if sub.stall_flag else 0,
                sub.stall_score,
                sub.infrastructure_status.value if sub.infrastructure_status and hasattr(sub.infrastructure_status, 'value') else _str(sub.infrastructure_status),
                str(sub.plat_date) if sub.plat_date else None,
                sub.model_dump_json(),
                now,
            ),
        )

    def save_subdivisions_batch(self, subs: list[Subdivision]) -> None:
        for sub in subs:
            self.save_subdivision(sub)
        self._conn.commit()

    def get_stalled_subdivisions(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT data_json FROM subdivisions WHERE stall_flag = 1 ORDER BY stall_score DESC"
        ).fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    # ── Municipal Events ──────────────────────────────────────────────────────

    def save_municipal_event(self, me: MunicipalEvent) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO municipal_events
               (municipal_event_id, municipality_id, event_type, occurred_at,
                source_system, subdivision_id, data_json, updated_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                _str(me.municipal_event_id),
                _str(me.municipality_id),
                me.event_type.value if hasattr(me.event_type, 'value') else str(me.event_type),
                str(me.occurred_at) if me.occurred_at else None,
                me.source_system,
                _str(me.subdivision_id),
                me.model_dump_json(),
                now,
            ),
        )

    def save_municipal_events_batch(self, events: list[MunicipalEvent]) -> None:
        for me in events:
            self.save_municipal_event(me)
        self._conn.commit()

    # ── Pipeline Signals (event log for the signal feed) ──────────────────────

    def save_signal(self, event_type: str, event_id: str,
                    entity_ref_summary: str, fired_rules: list[str],
                    payload_summary: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT INTO pipeline_signals
               (event_type, event_id, entity_ref_summary, fired_rules,
                payload_summary, created_at)
               VALUES (?,?,?,?,?,?)""",
            (
                event_type,
                event_id,
                entity_ref_summary,
                json.dumps(fired_rules),
                payload_summary,
                now,
            ),
        )

    def save_signals_batch(self, signals: list[dict]) -> None:
        for s in signals:
            self.save_signal(
                s["event_type"], s["event_id"], s["entity_ref_summary"],
                s["fired_rules"], s["payload_summary"],
            )
        self._conn.commit()

    def get_signals(self, since: str | None = None, limit: int = 50) -> list[dict]:
        query = "SELECT * FROM pipeline_signals"
        params: list[Any] = []
        if since is not None:
            query += " WHERE created_at > ?"
            params.append(since)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ── Pipeline Stats ────────────────────────────────────────────────────────

    def save_stat(self, key: str, value: Any) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT OR REPLACE INTO pipeline_stats (stat_key, stat_value, updated_at) VALUES (?,?,?)",
            (key, json.dumps(value, default=str), now),
        )

    def save_stats(self, stats: dict[str, Any]) -> None:
        for k, v in stats.items():
            self.save_stat(k, v)
        self._conn.commit()

    def get_all_stats(self) -> dict[str, Any]:
        rows = self._conn.execute("SELECT stat_key, stat_value FROM pipeline_stats").fetchall()
        return {r["stat_key"]: json.loads(r["stat_value"]) for r in rows}

    # ── Strategic Opportunities ───────────────────────────────────────────────

    def save_strategic_opportunity(self, opp: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT OR REPLACE INTO strategic_opportunities
               (opportunity_id, name, opportunity_type, precedence_tier, municipality_id,
                lot_count, total_acreage, infrastructure_invested,
                stall_confidence, vacancy_ratio, composite_score,
                has_active_listings, listing_count, owner_name,
                data_json, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                opp["opportunity_id"],
                opp.get("name", ""),
                opp.get("opportunity_type", ""),
                opp.get("precedence_tier", 4),
                opp.get("municipality_id"),
                opp.get("lot_count", 0),
                opp.get("total_acreage", 0.0),
                1 if opp.get("infrastructure_invested") else 0,
                opp.get("stall_confidence", 0.0),
                opp.get("vacancy_ratio", 0.0),
                opp.get("composite_score", 0.0),
                1 if opp.get("has_active_listings") else 0,
                opp.get("listing_count", 0),
                opp.get("owner_name", ""),
                json.dumps(opp, default=str),
                now,
            ),
        )

    def save_strategic_opportunities_batch(self, opps: list[dict]) -> None:
        for opp in opps:
            self.save_strategic_opportunity(opp)
        self._conn.commit()

    def get_strategic_opportunities(self, min_lots: int | None = None,
                                     infrastructure_only: bool = False,
                                     limit: int = 100) -> list[dict]:
        query = "SELECT data_json FROM strategic_opportunities WHERE 1=1"
        params: list[Any] = []
        if min_lots is not None:
            query += " AND lot_count >= ?"
            params.append(min_lots)
        if infrastructure_only:
            query += " AND infrastructure_invested = 1"
        query += " ORDER BY precedence_tier ASC, composite_score DESC LIMIT ?"
        params.append(limit)
        rows = self._conn.execute(query, params).fetchall()
        return [json.loads(r["data_json"]) for r in rows]

    def get_strategic_opportunity_by_id(self, opportunity_id: str) -> dict | None:
        """Get a single strategic opportunity by ID, or None if not found."""
        row = self._conn.execute(
            "SELECT data_json FROM strategic_opportunities WHERE opportunity_id = ?",
            (opportunity_id,),
        ).fetchone()
        return json.loads(row["data_json"]) if row else None

    # ── Listing History ────────────────────────────────────────────────────────

    def save_listing_history(self, listing: Listing, run_id: str | None = None) -> None:
        """Save a listing snapshot to history. Does NOT dedupe — every call adds a row."""
        now = datetime.now(timezone.utc).isoformat()
        fingerprint = _history_fingerprint(listing)
        self._conn.execute(
            """INSERT OR IGNORE INTO listing_history
               (run_id, snapshot_fingerprint, listing_key, snapshot_status, list_price, cdom, dom,
                original_list_price, previous_list_price, parcel_number,
                subdivision_name, seller_name, owner_name_raw, listing_agent_name,
                listing_office_name, address_raw, private_remarks,
                showing_instructions, list_date, close_date, expiration_date,
                off_market_date, withdrawal_date, back_on_market_date,
                latitude, longitude, lot_size_acres, data_json, ingested_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                run_id,
                fingerprint,
                listing.listing_key,
                listing.standard_status.value if listing.standard_status else "unknown",
                listing.list_price,
                listing.cdom,
                listing.dom,
                listing.original_list_price,
                listing.previous_list_price,
                listing.parcel_number_raw,
                listing.subdivision_name_raw,
                listing.seller_name_raw,
                getattr(listing, "owner_name_raw", None),
                listing.listing_agent_name,
                listing.listing_office_name,
                listing.address_raw,
                listing.private_remarks,
                listing.showing_instructions,
                str(listing.list_date) if listing.list_date else None,
                str(listing.close_date) if listing.close_date else None,
                str(listing.expiration_date) if listing.expiration_date else None,
                str(listing.off_market_date) if listing.off_market_date else None,
                str(listing.withdrawal_date) if listing.withdrawal_date else None,
                str(listing.back_on_market_date) if listing.back_on_market_date else None,
                listing.latitude,
                listing.longitude,
                listing.lot_size_acres,
                listing.model_dump_json(),
                now,
            ),
        )

    def save_listing_history_batch(self, listings: list[Listing], run_id: str | None = None) -> None:
        for listing in listings:
            self.save_listing_history(listing, run_id=run_id)
        self._conn.commit()

    def get_listing_history_by_key(self, listing_key: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT data_json, ingested_at, snapshot_status, run_id FROM listing_history WHERE listing_key = ? ORDER BY ingested_at DESC",
            (listing_key,),
        ).fetchall()
        results = []
        for r in rows:
            data = json.loads(r["data_json"])
            data["_ingested_at"] = r["ingested_at"]
            data["_snapshot_status"] = r["snapshot_status"]
            data["_run_id"] = r["run_id"]
            results.append(data)
        return results

    def get_listing_history_by_parcel(self, parcel_number: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT data_json, ingested_at, snapshot_status, run_id FROM listing_history WHERE parcel_number = ? ORDER BY ingested_at DESC",
            (parcel_number,),
        ).fetchall()
        results = []
        for r in rows:
            data = json.loads(r["data_json"])
            data["_ingested_at"] = r["ingested_at"]
            data["_snapshot_status"] = r["snapshot_status"]
            data["_run_id"] = r["run_id"]
            results.append(data)
        return results

    def get_listing_history_by_subdivision(self, subdivision_name: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT data_json, ingested_at, snapshot_status, run_id FROM listing_history WHERE subdivision_name = ? ORDER BY ingested_at DESC",
            (subdivision_name,),
        ).fetchall()
        results = []
        for r in rows:
            data = json.loads(r["data_json"])
            data["_ingested_at"] = r["ingested_at"]
            data["_snapshot_status"] = r["snapshot_status"]
            data["_run_id"] = r["run_id"]
            results.append(data)
        return results

    def get_listing_history_stats(self) -> dict:
        """Return counts by status, plus total unique listing_keys."""
        rows = self._conn.execute(
            "SELECT snapshot_status, COUNT(*) as cnt FROM listing_history GROUP BY snapshot_status"
        ).fetchall()
        by_status = {r["snapshot_status"]: r["cnt"] for r in rows}

        unique_row = self._conn.execute(
            "SELECT COUNT(DISTINCT listing_key) as cnt FROM listing_history"
        ).fetchone()
        unique_keys = unique_row["cnt"] if unique_row else 0

        total_row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM listing_history"
        ).fetchone()
        total_snapshots = total_row["cnt"] if total_row else 0

        return {
            "by_status": by_status,
            "unique_listing_keys": unique_keys,
            "total_snapshots": total_snapshots,
        }

    # ── Strategic Opportunity Count ──────────────────────────────────────────

    def get_strategic_opportunity_count(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as c FROM strategic_opportunities"
        ).fetchone()
        return row["c"]

    # ── Listing Genealogy ─────────────────────────────────────────────────────

    def save_genealogy_batch(self, entries: list[dict]) -> None:
        """Save a batch of genealogy entries. Each entry is a dict with keys
        matching the listing_genealogy columns."""
        now = datetime.now(timezone.utc).isoformat()
        for entry in entries:
            self._conn.execute(
                """INSERT INTO listing_genealogy
                   (listing_key, related_listing_key, relationship, event_type,
                    event_date, list_price, status, agent_name, office_name,
                    days_on_market, source_data_json, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    entry.get("listing_key"),
                    entry.get("related_listing_key"),
                    entry.get("relationship"),
                    entry.get("event_type"),
                    entry.get("event_date"),
                    entry.get("list_price"),
                    entry.get("status"),
                    entry.get("agent_name"),
                    entry.get("office_name"),
                    entry.get("days_on_market"),
                    json.dumps(entry.get("source_data", {}), default=str),
                    now,
                ),
            )
        self._conn.commit()

    def get_genealogy_by_listing(self, listing_key: str) -> list[dict]:
        """Get full genealogy chain for a listing."""
        rows = self._conn.execute(
            "SELECT * FROM listing_genealogy WHERE listing_key = ? ORDER BY event_date",
            (listing_key,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_genealogy_for_listings(self, listing_keys: list[str]) -> list[dict]:
        """Get genealogy for multiple listings."""
        if not listing_keys:
            return []
        placeholders = ",".join("?" * len(listing_keys))
        rows = self._conn.execute(
            f"SELECT * FROM listing_genealogy WHERE listing_key IN ({placeholders}) ORDER BY listing_key, event_date",
            listing_keys,
        ).fetchall()
        return [dict(r) for r in rows]

    def clear_genealogy(self) -> None:
        """Clear all genealogy data (for re-fetch)."""
        self._conn.execute("DELETE FROM listing_genealogy")
        self._conn.commit()

    # ── Market Statistics ────────────────────────────────────────────────────

    def save_market_stats_batch(self, entries: list[dict]) -> None:
        """Save market statistics. Uses INSERT OR REPLACE on the unique index."""
        now = datetime.now(timezone.utc).isoformat()
        for entry in entries:
            self._conn.execute(
                """INSERT OR REPLACE INTO market_statistics
                   (stat_type, county, property_type, period, value,
                    year, month, source_data_json, fetched_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    entry["stat_type"],
                    entry["county"],
                    entry["property_type"],
                    entry["period"],
                    entry.get("value"),
                    entry.get("year"),
                    entry.get("month"),
                    json.dumps(entry.get("source_data", {}), default=str),
                    now,
                ),
            )
        self._conn.commit()

    def get_market_stats(
        self,
        stat_type: str | None = None,
        county: str = "Washtenaw",
        limit: int = 200,
    ) -> list[dict]:
        """Get market stats, optionally filtered by type."""
        if stat_type:
            rows = self._conn.execute(
                "SELECT * FROM market_statistics WHERE stat_type = ? AND county = ? ORDER BY period DESC LIMIT ?",
                (stat_type, county, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM market_statistics WHERE county = ? ORDER BY stat_type, period DESC LIMIT ?",
                (county, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_market_stats_summary(self, county: str = "Washtenaw") -> dict:
        """Get latest value + trend for each stat type."""
        stat_types = self._conn.execute(
            "SELECT DISTINCT stat_type FROM market_statistics WHERE county = ?",
            (county,),
        ).fetchall()
        summary = {}
        for row in stat_types:
            st = row["stat_type"]
            latest_rows = self._conn.execute(
                "SELECT * FROM market_statistics WHERE stat_type = ? AND county = ? ORDER BY period DESC LIMIT 2",
                (st, county),
            ).fetchall()
            if not latest_rows:
                continue
            latest = dict(latest_rows[0])
            prev = dict(latest_rows[1]) if len(latest_rows) > 1 else None
            change_pct = None
            trend = "flat"
            if prev and prev["value"] and latest["value"]:
                change_pct = round(
                    (latest["value"] - prev["value"]) / abs(prev["value"]) * 100, 1
                ) if prev["value"] != 0 else None
                if change_pct is not None:
                    trend = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
            summary[st] = {
                "latest": latest["value"],
                "period": latest["period"],
                "trend": trend,
                "change_pct": change_pct,
            }
        return summary

    # ── Pipeline Reset ───────────────────────────────────────────────────────

    def reset_current_state(self) -> None:
        """Clear all current-state and derived tables for a fresh pipeline run.

        Does NOT wipe listing_history, listing_genealogy, or market_statistics —
        those tables accumulate over time and are fetched separately.
        """
        tables_to_clear = [
            "listings",
            "parcels",
            "clusters",
            "subdivisions",
            "opportunities",
            "strategic_opportunities",
            "municipal_events",
            "owners",
            "pipeline_signals",
            "pipeline_stats",
        ]
        for table in tables_to_clear:
            self._conn.execute(f"DELETE FROM {table}")
        self._conn.commit()

    # ── Utility ───────────────────────────────────────────────────────────────

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.commit()
        self._conn.close()
