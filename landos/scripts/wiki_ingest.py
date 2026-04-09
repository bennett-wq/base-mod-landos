#!/usr/bin/env python3
"""wiki_ingest.py — Karpathy-style LLM Wiki ingestor for LandOS.

Reads the SQLite database and generates/updates Obsidian-compatible markdown
pages in the wiki folder. No LLM calls — pure template rendering from SQL data.

Usage:
    python3 landos/scripts/wiki_ingest.py              # full run
    python3 landos/scripts/wiki_ingest.py --dry-run     # show what would be written
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

# ── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SCHEMA = PROJECT_ROOT / "landos" / "config" / "wiki_schema.yaml"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _safe_filename(name: str) -> str:
    """Sanitize a name for use in a filename (Obsidian-safe)."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.strip(". ")
    return name[:120] if name else "unnamed"


def _preserve_human_notes(existing_path: Path, new_content: str) -> str:
    """If the file already exists and has a Human Notes section, preserve it."""
    if not existing_path.exists():
        return new_content

    old = existing_path.read_text(encoding="utf-8")
    marker = "## Human Notes"
    old_idx = old.find(marker)
    if old_idx == -1:
        return new_content

    # Extract everything from ## Human Notes onward in the old file
    old_human_section = old[old_idx:]

    # Replace the Human Notes section in new content
    new_idx = new_content.find(marker)
    if new_idx == -1:
        return new_content + "\n\n" + old_human_section

    return new_content[:new_idx] + old_human_section


class WikiIngestor:
    """Reads SQLite + schema → renders wiki pages into the Obsidian vault."""

    def __init__(self, schema_path: Path | None = None, dry_run: bool = False):
        self.schema_path = schema_path or DEFAULT_SCHEMA
        with open(self.schema_path, encoding="utf-8") as f:
            self.schema = yaml.safe_load(f)

        self.wiki_root = Path(self.schema["wiki_root"])
        db_path = PROJECT_ROOT / self.schema["db_path"]
        self.db = sqlite3.connect(str(db_path))
        self.db.row_factory = sqlite3.Row
        self.dry_run = dry_run
        self.generated_at = _now_iso()
        self.today = _today()

        templates_dir = PROJECT_ROOT / self.schema["templates_dir"]
        self.jinja = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            keep_trailing_newline=True,
        )
        self.pages_written: list[str] = []

    def run(self) -> list[str]:
        """Run full ingest cycle. Returns list of pages written."""
        print(f"[wiki-ingest] Starting ingest at {self.generated_at}")
        print(f"[wiki-ingest] Wiki root: {self.wiki_root}")
        print(f"[wiki-ingest] DB: {self.schema['db_path']}")

        self._ingest_market_snapshot()
        self._ingest_opportunities()
        self._ingest_subdivisions()
        self._ingest_pipeline_health()
        self._ingest_pipeline_run()
        self._ingest_genealogy_timelines()
        self._ingest_market_trends()
        self._ingest_wiki_index()

        print(f"[wiki-ingest] Done. {len(self.pages_written)} pages written.")
        return self.pages_written

    def _write_page(self, rel_path: str, content: str) -> None:
        full_path = self.wiki_root / rel_path
        content = _preserve_human_notes(full_path, content)
        if self.dry_run:
            print(f"  [dry-run] Would write: {rel_path}")
        else:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
        self.pages_written.append(rel_path)

    # ── Market Snapshot ──────────────────────────────────────────────────────

    def _ingest_market_snapshot(self) -> None:
        print("[wiki-ingest] Generating market snapshot...")

        tiers = [
            dict(row)
            for row in self.db.execute("""
                SELECT precedence_tier,
                       COUNT(*) as count,
                       COALESCE(SUM(lot_count), 0) as total_lots,
                       ROUND(AVG(composite_score), 3) as avg_score,
                       ROUND(AVG(total_acreage), 1) as avg_acreage
                FROM strategic_opportunities
                GROUP BY precedence_tier
                ORDER BY precedence_tier
            """).fetchall()
        ]

        totals = self.db.execute("""
            SELECT COUNT(*) as total,
                   COALESCE(SUM(lot_count), 0) as lots,
                   COALESCE(SUM(total_acreage), 0) as acreage,
                   SUM(CASE WHEN has_active_listings THEN 1 ELSE 0 END) as active,
                   COALESCE(SUM(listing_count), 0) as listing_count,
                   SUM(CASE WHEN infrastructure_invested THEN 1 ELSE 0 END) as infra
            FROM strategic_opportunities
        """).fetchone()

        top_10 = [
            dict(row)
            for row in self.db.execute("""
                SELECT name, precedence_tier, composite_score, lot_count,
                       total_acreage, has_active_listings
                FROM strategic_opportunities
                ORDER BY precedence_tier ASC, composite_score DESC
                LIMIT 10
            """).fetchall()
        ]

        sub_stats = self.db.execute("""
            SELECT COUNT(*) as count,
                   SUM(CASE WHEN stall_flag THEN 1 ELSE 0 END) as stalled,
                   ROUND(AVG(vacancy_ratio), 2) as avg_vr
            FROM subdivisions
        """).fetchone()

        recent_signals = [
            dict(row)
            for row in self.db.execute("""
                SELECT event_type, COUNT(*) as count
                FROM pipeline_signals
                WHERE created_at >= date('now', '-7 days')
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 15
            """).fetchall()
        ]

        tmpl = self.jinja.get_template("market_snapshot.md.j2")
        content = tmpl.render(
            generated_at=self.generated_at,
            tiers=tiers,
            total_opportunities=totals["total"],
            total_lots=totals["lots"],
            total_acreage=totals["acreage"],
            active_listing_opps=totals["active"],
            total_listing_count=totals["listing_count"],
            infra_invested_count=totals["infra"],
            top_10=top_10,
            subdivision_count=sub_stats["count"],
            stalled_count=sub_stats["stalled"],
            avg_vacancy_ratio=sub_stats["avg_vr"] or 0,
            recent_signals=recent_signals,
        )
        self._write_page("Market/Market Snapshot — Washtenaw.md", content)

    # ── Opportunity Detail Pages ─────────────────────────────────────────────

    def _ingest_opportunities(self) -> None:
        print("[wiki-ingest] Generating opportunity pages...")

        rows = self.db.execute("""
            SELECT name, data_json
            FROM strategic_opportunities
            WHERE precedence_tier <= 2
            ORDER BY precedence_tier ASC, composite_score DESC
            LIMIT 30
        """).fetchall()

        for row in rows:
            opp = json.loads(row["data_json"])
            safe_name = _safe_filename(opp.get("name", "unnamed"))
            tmpl = self.jinja.get_template("opportunity_detail.md.j2")
            content = tmpl.render(generated_at=self.generated_at, opp=opp)
            self._write_page(f"Opportunities/Opportunity — {safe_name}.md", content)

        print(f"  {len(rows)} opportunity pages")

    # ── Subdivision Profiles ─────────────────────────────────────────────────

    def _ingest_subdivisions(self) -> None:
        print("[wiki-ingest] Generating subdivision pages...")

        rows = self.db.execute("""
            SELECT subdivision_id, name, municipality_id, county,
                   total_lots, vacant_lots, vacancy_ratio, stall_flag,
                   stall_score, infrastructure_status, plat_date, data_json
            FROM subdivisions
            ORDER BY vacancy_ratio DESC
        """).fetchall()

        for row in rows:
            sub = dict(row)
            sub_name = sub.get("name") or "unnamed"
            safe_name = _safe_filename(sub_name)

            # Find linked opportunities
            linked = [
                dict(r)
                for r in self.db.execute("""
                    SELECT name, precedence_tier, composite_score, lot_count,
                           has_active_listings
                    FROM strategic_opportunities
                    WHERE data_json LIKE ?
                    ORDER BY composite_score DESC
                    LIMIT 10
                """, (f'%"subdivision_name": "{sub_name}"%',)).fetchall()
            ]

            # Listing summary for this subdivision
            listing_summary = [
                dict(r)
                for r in self.db.execute("""
                    SELECT standard_status as status,
                           COUNT(*) as count,
                           ROUND(AVG(list_price)) as avg_price
                    FROM listings
                    WHERE subdivision_name_raw = ?
                    GROUP BY standard_status
                """, (sub_name,)).fetchall()
            ]

            tmpl = self.jinja.get_template("subdivision_profile.md.j2")
            content = tmpl.render(
                generated_at=self.generated_at,
                sub=sub,
                linked_opportunities=linked,
                listing_summary=listing_summary,
            )
            self._write_page(f"Subdivisions/Subdivision — {safe_name}.md", content)

        print(f"  {len(rows)} subdivision pages")

    # ── Pipeline Health ──────────────────────────────────────────────────────

    def _ingest_pipeline_health(self) -> None:
        print("[wiki-ingest] Generating pipeline health...")

        stats = [
            dict(row)
            for row in self.db.execute(
                "SELECT stat_key, stat_value, updated_at FROM pipeline_stats ORDER BY stat_key"
            ).fetchall()
        ]

        tables = [
            "strategic_opportunities", "subdivisions", "listings", "clusters",
            "parcels", "owners", "pipeline_signals", "listing_history", "municipal_events",
        ]
        table_counts = []
        for t in tables:
            try:
                count = self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                table_counts.append({"name": t, "count": count})
            except sqlite3.OperationalError:
                pass

        recent_signals = [
            dict(row)
            for row in self.db.execute("""
                SELECT event_type, COUNT(*) as count
                FROM pipeline_signals
                WHERE created_at >= date('now', '-7 days')
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 15
            """).fetchall()
        ]

        total_signals = self.db.execute(
            "SELECT COUNT(*) FROM pipeline_signals"
        ).fetchone()[0]

        tmpl = self.jinja.get_template("pipeline_health.md.j2")
        content = tmpl.render(
            generated_at=self.generated_at,
            stats=stats,
            table_counts=table_counts,
            recent_signals=recent_signals,
            total_signals=total_signals,
        )
        self._write_page("Pipeline/Pipeline Health.md", content)

    # ── Pipeline Run (daily snapshot) ────────────────────────────────────────

    def _ingest_pipeline_run(self) -> None:
        print("[wiki-ingest] Generating pipeline run snapshot...")

        stats = [
            dict(row)
            for row in self.db.execute(
                "SELECT stat_key, stat_value FROM pipeline_stats ORDER BY stat_key"
            ).fetchall()
        ]

        tables = [
            "strategic_opportunities", "subdivisions", "listings", "clusters",
            "parcels", "pipeline_signals",
        ]
        table_counts = []
        for t in tables:
            try:
                count = self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                table_counts.append({"name": t, "count": count})
            except sqlite3.OperationalError:
                pass

        tiers = [
            dict(row)
            for row in self.db.execute("""
                SELECT precedence_tier,
                       COUNT(*) as count,
                       COALESCE(SUM(lot_count), 0) as total_lots,
                       ROUND(AVG(composite_score), 3) as avg_score
                FROM strategic_opportunities
                GROUP BY precedence_tier
                ORDER BY precedence_tier
            """).fetchall()
        ]

        # Score movers: compare with previous run file if it exists
        movers = self._detect_score_movers()

        tmpl = self.jinja.get_template("pipeline_run.md.j2")
        content = tmpl.render(
            generated_at=self.generated_at,
            run_date=self.today,
            stats=stats,
            table_counts=table_counts,
            tiers=tiers,
            movers=movers,
        )
        self._write_page(f"Pipeline/Run — {self.today}.md", content)

    def _detect_score_movers(self) -> list[dict]:
        """Compare current scores with the most recent previous run file."""
        pipeline_dir = self.wiki_root / "Pipeline"
        if not pipeline_dir.exists():
            return []

        # Find the most recent Run file that isn't today
        run_files = sorted(pipeline_dir.glob("Run — *.md"), reverse=True)
        prev_file = None
        for f in run_files:
            if self.today not in f.name:
                prev_file = f
                break

        if not prev_file:
            return []

        # Parse previous scores from the file (look for opportunity names + scores)
        # This is a best-effort heuristic — not critical if it misses some
        prev_scores: dict[str, float] = {}
        try:
            content = prev_file.read_text(encoding="utf-8")
            # Look for lines in the tier table that have score values
            for line in content.split("\n"):
                if "| Opportunity —" in line or "[[Opportunity —" in line:
                    # Try to extract name and score
                    parts = line.split("|")
                    if len(parts) >= 4:
                        name_part = parts[1].strip()
                        name_match = re.search(r"Opportunity — (.+?)[\]|]", name_part)
                        try:
                            score = float(parts[3].strip())
                            if name_match:
                                prev_scores[name_match.group(1)] = score
                        except (ValueError, IndexError):
                            pass
        except Exception:
            return []

        if not prev_scores:
            return []

        # Compare with current
        movers = []
        rows = self.db.execute("""
            SELECT name, composite_score
            FROM strategic_opportunities
            WHERE precedence_tier <= 2
        """).fetchall()

        for row in rows:
            name = row["name"]
            current = row["composite_score"]
            if name in prev_scores and prev_scores[name] > 0:
                prev = prev_scores[name]
                pct = ((current - prev) / prev) * 100
                if abs(pct) > 20:
                    movers.append({
                        "name": name,
                        "previous": prev,
                        "current": current,
                        "pct_change": pct,
                    })

        return sorted(movers, key=lambda m: abs(m["pct_change"]), reverse=True)[:10]

    # ── Genealogy Timelines ───────────────────────────────────────────────────

    def _ingest_genealogy_timelines(self) -> None:
        """Generate genealogy timeline pages for top opportunities."""
        print("[wiki-ingest] Generating genealogy timelines...")

        # Check if genealogy table has data
        try:
            total = self.db.execute("SELECT COUNT(*) FROM listing_genealogy").fetchone()[0]
        except Exception:
            print("  No listing_genealogy table — skipping")
            return

        if total == 0:
            print("  No genealogy data — skipping")
            return

        # Get top opportunities that have genealogy data
        opp_rows = self.db.execute("""
            SELECT name, data_json
            FROM strategic_opportunities
            WHERE precedence_tier <= 2
            ORDER BY precedence_tier ASC, composite_score DESC
            LIMIT 30
        """).fetchall()

        count = 0
        for opp_row in opp_rows:
            opp = json.loads(opp_row["data_json"])
            opp_name = opp.get("name") or opp_row["name"] or "unnamed"
            listing_keys = opp.get("listing_keys", []) + opp.get("owner_linked_listing_keys", [])
            listing_keys = list(set(listing_keys))

            if not listing_keys:
                continue

            # Get genealogy entries for these listing keys
            placeholders = ",".join("?" * len(listing_keys))
            entries = [
                dict(r)
                for r in self.db.execute(
                    f"SELECT * FROM listing_genealogy WHERE listing_key IN ({placeholders}) ORDER BY event_date",
                    listing_keys,
                ).fetchall()
            ]

            if not entries:
                continue

            # Compute aggregates
            all_agents = [e["agent_name"] for e in entries if e["agent_name"]]
            all_offices = [e["office_name"] for e in entries if e["office_name"]]
            all_prices = [e["list_price"] for e in entries if e["list_price"] and e["list_price"] > 0]
            all_doms = [e["days_on_market"] for e in entries if e["days_on_market"] is not None]

            # Agent counts
            agent_counts: dict[str, int] = {}
            for a in all_agents:
                agent_counts[a] = agent_counts.get(a, 0) + 1

            # Status counts
            status_counts: dict[str, int] = {}
            for e in entries:
                s = e.get("event_type") or e.get("status") or "unknown"
                status_counts[s] = status_counts.get(s, 0) + 1

            failed_statuses = {"expired", "withdrawn", "canceled"}
            failed_attempts = sum(
                1 for e in entries if (e.get("event_type") or "").lower() in failed_statuses
            )

            unique_related = len({
                e["related_listing_key"]
                for e in entries
                if e.get("related_listing_key") and e.get("relationship") != "self"
            })

            # Price changes (between consecutive entries with different prices)
            price_changes = []
            sorted_entries = sorted(
                [e for e in entries if e["list_price"] and e["list_price"] > 0],
                key=lambda x: x.get("event_date") or "",
            )
            for i in range(1, len(sorted_entries)):
                prev_p = sorted_entries[i - 1]["list_price"]
                curr_p = sorted_entries[i]["list_price"]
                if prev_p != curr_p:
                    diff = curr_p - prev_p
                    price_changes.append({
                        "direction": "+" if diff > 0 else "-",
                        "amount": abs(diff),
                        "from_listing": sorted_entries[i - 1].get("related_listing_key", "?")[:12],
                        "to_listing": sorted_entries[i].get("related_listing_key", "?")[:12],
                    })

            safe_name = _safe_filename(opp_name)
            tmpl = self.jinja.get_template("genealogy_timeline.md.j2")
            content = tmpl.render(
                generated_at=self.generated_at,
                opportunity_name=opp_name,
                listing_keys=listing_keys,
                entries=entries,
                unique_related=unique_related,
                unique_agents=len(set(all_agents)),
                unique_offices=len(set(all_offices)),
                min_price=min(all_prices) if all_prices else 0,
                max_price=max(all_prices) if all_prices else 0,
                max_dom=max(all_doms) if all_doms else None,
                agent_counts=agent_counts,
                status_counts=status_counts,
                failed_attempts=failed_attempts,
                price_changes=price_changes[:20],
            )
            self._write_page(f"Genealogy/Genealogy — {safe_name}.md", content)
            count += 1

        print(f"  {count} genealogy pages")

    # ── Market Trends ────────────────────────────────────────────────────────

    def _ingest_market_trends(self) -> None:
        """Generate market trends page from market_statistics table."""
        print("[wiki-ingest] Generating market trends...")

        # Check if market_statistics table has data
        try:
            total = self.db.execute("SELECT COUNT(*) FROM market_statistics").fetchone()[0]
        except Exception:
            print("  No market_statistics table — skipping")
            return

        if total == 0:
            print("  No market statistics data — skipping")
            return

        county = "Washtenaw"
        property_type = "Land"

        # Get all stats
        all_stats = [
            dict(r)
            for r in self.db.execute(
                "SELECT * FROM market_statistics WHERE county = ? ORDER BY stat_type, period DESC",
                (county,),
            ).fetchall()
        ]

        # Group by stat_type
        by_type: dict[str, list[dict]] = {}
        for row in all_stats:
            st = row["stat_type"]
            if st not in by_type:
                by_type[st] = []
            by_type[st].append(row)

        # Build summary
        stat_labels = {
            "absorption": "Absorption Rate",
            "inventory": "Active Inventory",
            "price": "Avg List Price",
            "ratio": "Sale-to-List Ratio",
            "dom": "Avg Days on Market",
            "volume": "Sales Volume",
        }

        summary: dict[str, dict] = {}
        for st, rows in by_type.items():
            if not rows:
                continue
            latest = rows[0]  # already sorted DESC
            prev = rows[1] if len(rows) > 1 else None

            change_pct = None
            trend = "flat"
            if prev and prev["value"] and latest["value"]:
                if prev["value"] != 0:
                    change_pct = (latest["value"] - prev["value"]) / abs(prev["value"]) * 100
                    trend = "up" if change_pct > 1 else "down" if change_pct < -1 else "flat"

            trend_arrows = {"up": "^", "down": "v", "flat": "="}

            # Format value based on stat type
            val = latest["value"]
            if st == "price":
                formatted = f"${val:,.0f}"
            elif st == "volume":
                formatted = f"${val:,.0f}"
            elif st == "absorption":
                formatted = f"{val:.1%}"
            elif st == "ratio":
                formatted = f"{val:.2%}"
            elif st == "inventory":
                formatted = f"{val:.0f}"
            elif st == "dom":
                formatted = f"{val:.0f}"
            else:
                formatted = f"{val:.2f}"

            change_str = f"{change_pct:+.1f}%" if change_pct is not None else "—"

            summary[st] = {
                "latest": val,
                "period": latest["period"],
                "trend": trend,
                "trend_arrow": trend_arrows.get(trend, "?"),
                "change_pct": change_pct,
                "formatted": formatted,
                "change_str": change_str,
            }

        # Check if data is derived
        is_derived = any(
            "derived_from_listing_history" in (r.get("source_data_json") or "")
            for r in all_stats[:5]
        )

        # Convert stat type rows to simple objects for template
        def _to_rows(st: str) -> list:
            return [{"period": r["period"], "value": r["value"]} for r in by_type.get(st, [])]

        safe_county = _safe_filename(county)
        tmpl = self.jinja.get_template("market_trends.md.j2")
        content = tmpl.render(
            generated_at=self.generated_at,
            county=county,
            property_type=property_type,
            stat_types=list(by_type.keys()),
            total_data_points=total,
            summary=summary,
            stat_labels=stat_labels,
            is_derived=is_derived,
            inventory_data=_to_rows("inventory"),
            price_data=_to_rows("price"),
            dom_data=_to_rows("dom"),
            absorption_data=_to_rows("absorption"),
            volume_data=_to_rows("volume"),
            ratio_data=_to_rows("ratio"),
        )
        self._write_page(f"Market/Market Trends — {safe_county}.md", content)

    # ── Wiki Index ───────────────────────────────────────────────────────────

    def _ingest_wiki_index(self) -> None:
        print("[wiki-ingest] Generating wiki index...")

        now = datetime.now(timezone.utc)

        def _page_info(path: Path, staleness_days: int = 2) -> dict:
            info = {"title": path.stem, "generated_at": "unknown", "freshness": "unknown"}
            try:
                text = path.read_text(encoding="utf-8")
                match = re.search(r"generated_at:\s*(.+)", text)
                if match:
                    gen_str = match.group(1).strip()
                    info["generated_at"] = gen_str
                    gen_dt = datetime.fromisoformat(gen_str.replace("Z", "+00:00"))
                    age_days = (now - gen_dt).days
                    info["freshness"] = "Fresh" if age_days <= staleness_days else f"STALE ({age_days}d)"
            except Exception:
                pass
            return info

        def _opp_info(path: Path) -> dict:
            info = _page_info(path, staleness_days=2)
            info["tier"] = "?"
            info["score"] = 0.0
            try:
                text = path.read_text(encoding="utf-8")
                tier_match = re.search(r"precedence_tier:\s*(\d+)", text)
                score_match = re.search(r"composite_score:\s*([\d.]+)", text)
                if tier_match:
                    info["tier"] = tier_match.group(1)
                if score_match:
                    info["score"] = float(score_match.group(1))
            except Exception:
                pass
            return info

        def _sub_info(path: Path) -> dict:
            info = _page_info(path, staleness_days=7)
            info["vacancy"] = 0.0
            info["stalled"] = "No"
            try:
                text = path.read_text(encoding="utf-8")
                vr_match = re.search(r"vacancy_ratio:\s*([\d.]+)", text)
                if vr_match:
                    info["vacancy"] = float(vr_match.group(1))
                if "- stalled" in text:
                    info["stalled"] = "Yes"
            except Exception:
                pass
            return info

        market_pages = [_page_info(p) for p in sorted((self.wiki_root / "Market").glob("*.md"))]
        opportunity_pages = [_opp_info(p) for p in sorted((self.wiki_root / "Opportunities").glob("*.md"))]
        subdivision_pages = [_sub_info(p) for p in sorted((self.wiki_root / "Subdivisions").glob("*.md"))]
        pipeline_pages = [_page_info(p) for p in sorted((self.wiki_root / "Pipeline").glob("*.md"))]
        lint_pages = [_page_info(p) for p in sorted((self.wiki_root / "Lint").glob("*.md"))]
        genealogy_dir = self.wiki_root / "Genealogy"
        genealogy_pages = [_page_info(p, staleness_days=7) for p in sorted(genealogy_dir.glob("*.md"))] if genealogy_dir.exists() else []

        all_pages = market_pages + opportunity_pages + subdivision_pages + pipeline_pages + lint_pages + genealogy_pages
        stale_count = sum(1 for p in all_pages if "STALE" in str(p.get("freshness", "")))

        tmpl = self.jinja.get_template("wiki_index.md.j2")
        content = tmpl.render(
            generated_at=self.generated_at,
            total_pages=len(all_pages),
            stale_count=stale_count,
            market_pages=market_pages,
            opportunity_pages=opportunity_pages,
            subdivision_pages=subdivision_pages,
            pipeline_pages=pipeline_pages,
            lint_pages=lint_pages,
            genealogy_pages=genealogy_pages,
        )
        self._write_page("Wiki Index.md", content)


def main() -> None:
    parser = argparse.ArgumentParser(description="LandOS Wiki Ingestor")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written")
    parser.add_argument("--schema", type=Path, default=None, help="Path to wiki_schema.yaml")
    args = parser.parse_args()

    ingestor = WikiIngestor(schema_path=args.schema, dry_run=args.dry_run)
    pages = ingestor.run()

    if args.dry_run:
        print(f"\n[dry-run] Would write {len(pages)} pages")
    else:
        print(f"\n[wiki-ingest] Wrote {len(pages)} pages to {ingestor.wiki_root}")


if __name__ == "__main__":
    main()
