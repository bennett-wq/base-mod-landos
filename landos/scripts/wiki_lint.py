#!/usr/bin/env python3
"""wiki_lint.py — Health-check the LandOS Wiki for contradictions and staleness.

Runs 6 checks against wiki pages + SQLite database, then writes a lint report
into the wiki folder. No LLM calls — pure file/SQL comparison.

Usage:
    python3 landos/scripts/wiki_lint.py              # full lint
    python3 landos/scripts/wiki_lint.py --dry-run     # print findings without writing
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SCHEMA = PROJECT_ROOT / "landos" / "config" / "wiki_schema.yaml"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Finding:
    """A single lint finding."""

    def __init__(self, check: str, severity: str, detail: str):
        self.check = check
        self.severity = severity
        self.detail = detail

    def to_dict(self) -> dict:
        return {"check": self.check, "severity": self.severity, "detail": self.detail}


class WikiLinter:
    """Runs health checks on the LandOS wiki."""

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
        self.findings: list[Finding] = []

        templates_dir = PROJECT_ROOT / self.schema["templates_dir"]
        self.jinja = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            keep_trailing_newline=True,
        )

    def run(self) -> list[Finding]:
        """Run all lint checks and write the report."""
        print(f"[wiki-lint] Starting lint at {self.generated_at}")

        self._check_stale_pages()
        self._check_score_drift()
        self._check_missing_pages()
        self._check_orphaned_pages()
        self._check_vacancy_contradictions()
        self._check_dead_references()

        self._write_report()

        errors = sum(1 for f in self.findings if f.severity == "error")
        warnings = sum(1 for f in self.findings if f.severity == "warning")
        infos = sum(1 for f in self.findings if f.severity == "info")
        print(f"[wiki-lint] Done. {errors} errors, {warnings} warnings, {infos} info")

        return self.findings

    def _parse_frontmatter(self, path: Path) -> dict:
        """Parse YAML frontmatter from a wiki page."""
        try:
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                return {}
            end = text.index("---", 3)
            return yaml.safe_load(text[3:end]) or {}
        except Exception:
            return {}

    # ── Check 1: Stale Pages ─────────────────────────────────────────────────

    def _check_stale_pages(self) -> None:
        now = datetime.now(timezone.utc)
        stale_pages = []

        for md in self.wiki_root.rglob("*.md"):
            fm = self._parse_frontmatter(md)
            if fm.get("source") != "llm-wiki":
                continue

            gen_str = fm.get("generated_at")
            staleness_days = fm.get("staleness_days", 7)
            if not gen_str:
                continue

            try:
                gen_dt = datetime.fromisoformat(str(gen_str).replace("Z", "+00:00"))
                age_days = (now - gen_dt).days
                if age_days > staleness_days:
                    overdue = age_days - staleness_days
                    rel = md.relative_to(self.wiki_root)
                    self.findings.append(Finding(
                        "stale_pages", "warning",
                        f"{rel} — {age_days}d old (limit {staleness_days}d, {overdue}d overdue)"
                    ))
                    stale_pages.append({
                        "path": str(rel),
                        "generated_at": gen_str,
                        "staleness_days": staleness_days,
                        "days_overdue": overdue,
                    })
            except Exception:
                pass

        self._stale_pages = stale_pages

    # ── Check 2: Score Drift ─────────────────────────────────────────────────

    def _check_score_drift(self) -> None:
        opp_dir = self.wiki_root / "Opportunities"
        if not opp_dir.exists():
            return

        for md in opp_dir.glob("*.md"):
            fm = self._parse_frontmatter(md)
            opp_id = fm.get("opportunity_id")
            wiki_score = fm.get("composite_score")
            if not opp_id or wiki_score is None:
                continue

            try:
                wiki_score = float(wiki_score)
            except (ValueError, TypeError):
                continue

            row = self.db.execute(
                "SELECT composite_score FROM strategic_opportunities WHERE opportunity_id = ?",
                (opp_id,)
            ).fetchone()

            if row and wiki_score > 0:
                db_score = row["composite_score"]
                pct = abs((db_score - wiki_score) / wiki_score) * 100
                if pct > 20:
                    rel = md.relative_to(self.wiki_root)
                    self.findings.append(Finding(
                        "score_drift", "info",
                        f"{rel} — wiki={wiki_score:.3f}, db={db_score:.3f} ({pct:+.1f}%)"
                    ))

    # ── Check 3: Missing Pages ───────────────────────────────────────────────

    def _check_missing_pages(self) -> None:
        # Only check the top N that ingest actually generates (matches schema max_pages)
        max_pages = 30
        for page_def in self.schema.get("pages", []):
            if page_def.get("id") == "opportunity_detail":
                max_pages = page_def.get("max_pages", 30)
                break

        rows = self.db.execute("""
            SELECT name, precedence_tier, composite_score, lot_count
            FROM strategic_opportunities
            WHERE precedence_tier <= 2
            ORDER BY precedence_tier ASC, composite_score DESC
            LIMIT ?
        """, (max_pages,)).fetchall()

        opp_dir = self.wiki_root / "Opportunities"
        existing = {p.stem for p in opp_dir.glob("*.md")} if opp_dir.exists() else set()

        self._missing_opportunities = []
        for row in rows:
            expected_stem = f"Opportunity — {row['name']}"
            # Check with some flexibility for sanitized names
            found = any(expected_stem[:40] in e for e in existing)
            if not found:
                self.findings.append(Finding(
                    "missing_pages", "error",
                    f"Tier {row['precedence_tier']} opportunity '{row['name']}' "
                    f"(score={row['composite_score']:.3f}, lots={row['lot_count']}) has no wiki page"
                ))
                self._missing_opportunities.append(dict(row))

    # ── Check 4: Orphaned Pages ──────────────────────────────────────────────

    def _check_orphaned_pages(self) -> None:
        # Collect all wiki page stems
        all_pages = {p.stem: p for p in self.wiki_root.rglob("*.md")
                     if self._parse_frontmatter(p).get("source") == "llm-wiki"}

        # Collect all [[wikilinks]] across the entire vault
        vault_root = Path(self.schema["vault_root"])
        linked_stems: set[str] = set()

        for md in vault_root.rglob("*.md"):
            try:
                text = md.read_text(encoding="utf-8")
                for match in re.finditer(r"\[\[(.+?)(?:\|.+?)?\]\]", text):
                    linked_stems.add(match.group(1))
            except Exception:
                pass

        # Also check within wiki itself
        for md in self.wiki_root.rglob("*.md"):
            try:
                text = md.read_text(encoding="utf-8")
                for match in re.finditer(r"\[\[(.+?)(?:\|.+?)?\]\]", text):
                    linked_stems.add(match.group(1))
            except Exception:
                pass

        # Wiki Index and Lint Report are structural — skip them
        skip = {"Wiki Index", "Latest Lint Report"}
        for stem, path in all_pages.items():
            if stem in skip:
                continue
            if stem not in linked_stems:
                rel = path.relative_to(self.wiki_root)
                self.findings.append(Finding(
                    "orphaned_pages", "warning",
                    f"{rel} — no inbound [[wikilinks]]"
                ))

    # ── Check 5: Vacancy Contradictions ──────────────────────────────────────

    def _check_vacancy_contradictions(self) -> None:
        sub_dir = self.wiki_root / "Subdivisions"
        if not sub_dir.exists():
            return

        for md in sub_dir.glob("*.md"):
            fm = self._parse_frontmatter(md)
            sub_id = fm.get("subdivision_id")
            wiki_vr = fm.get("vacancy_ratio")
            if not sub_id or wiki_vr is None:
                continue

            try:
                wiki_vr = float(wiki_vr)
            except (ValueError, TypeError):
                continue

            row = self.db.execute(
                "SELECT vacancy_ratio FROM subdivisions WHERE subdivision_id = ?",
                (sub_id,)
            ).fetchone()

            if row and row["vacancy_ratio"] is not None:
                db_vr = row["vacancy_ratio"]
                if abs(db_vr - wiki_vr) > 0.01:
                    rel = md.relative_to(self.wiki_root)
                    self.findings.append(Finding(
                        "vacancy_contradictions", "error",
                        f"{rel} — wiki={wiki_vr:.2f}, db={db_vr:.2f}"
                    ))

    # ── Check 6: Dead References ─────────────────────────────────────────────

    def _check_dead_references(self) -> None:
        listing_keys_in_db = {
            row[0]
            for row in self.db.execute("SELECT listing_key FROM listings").fetchall()
        }

        for md in self.wiki_root.rglob("*.md"):
            try:
                text = md.read_text(encoding="utf-8")
                for match in re.finditer(r"listing[_\s]key[:\s]+['\"]?(\w{20,})", text, re.IGNORECASE):
                    key = match.group(1)
                    if key not in listing_keys_in_db:
                        rel = md.relative_to(self.wiki_root)
                        self.findings.append(Finding(
                            "dead_references", "warning",
                            f"{rel} references listing {key[:20]}... not in DB"
                        ))
            except Exception:
                pass

    # ── Report ───────────────────────────────────────────────────────────────

    def _write_report(self) -> None:
        error_count = sum(1 for f in self.findings if f.severity == "error")
        warning_count = sum(1 for f in self.findings if f.severity == "warning")
        info_count = sum(1 for f in self.findings if f.severity == "info")

        tmpl = self.jinja.get_template("lint_report.md.j2")
        content = tmpl.render(
            generated_at=self.generated_at,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            findings=[f.to_dict() for f in self.findings],
            stale_pages=getattr(self, "_stale_pages", []),
            missing_opportunities=getattr(self, "_missing_opportunities", []),
        )

        report_path = self.wiki_root / "Lint" / "Latest Lint Report.md"
        if self.dry_run:
            print(f"  [dry-run] Would write lint report to {report_path}")
            for f in self.findings:
                print(f"  [{f.severity}] {f.check}: {f.detail}")
        else:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(content, encoding="utf-8")
            print(f"  Report written to {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LandOS Wiki Linter")
    parser.add_argument("--dry-run", action="store_true", help="Print findings without writing")
    parser.add_argument("--schema", type=Path, default=None, help="Path to wiki_schema.yaml")
    args = parser.parse_args()

    linter = WikiLinter(schema_path=args.schema, dry_run=args.dry_run)
    linter.run()


if __name__ == "__main__":
    main()
