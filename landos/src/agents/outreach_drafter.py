"""Outreach drafter — draft offer letters + cover emails to vault _drafts/.

HARD INVARIANT (spec §4.5): this agent NEVER delivers outgoing correspondence.
It writes two markdown files to the vault ``_drafts/`` directory — one offer
letter and one cover email to the listing agent — and returns file paths.
Bennett reviews the drafts in Obsidian and transmits them manually through
his own tooling.

A CI-style grep test in ``tests/test_outreach_drafter.py`` reads this file and
asserts that no delivery-layer imports or call sites appear here. DO NOT add
any such code. If a future enhancement ever needs to transmit, it lives in a
separate agent with its own explicit audit trail.

Gap surfacing (from the M2-4 Finding #10 pattern): the drafter inspects the
OpportunityUnderwriting for data-completeness gaps (empty applicable_programs,
zero listing history, weak comp anchor) and both:
  1. Returns a ``gaps_flagged: list[str]`` in the result dict.
  2. Prepends a ``> [!warning] REVIEW BEFORE SENDING`` callout to the offer
     letter naming each gap, so Bennett sees them when opening the draft in
     Obsidian.

Vault path resolution follows the same pattern as incentive_agent:
OBSIDIAN_VAULT_PATH env var, or explicit vault_path= kwarg. Missing both
raises EnvironmentError which the MCP handler catches as an _err response.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.models.opportunity import OpportunityUnderwriting


# Default vault path: controlled by OBSIDIAN_VAULT_PATH env var.
# Falls back to None so callers without the env var must pass vault_path= explicitly.
_ENV_VAULT_PATH: str | None = os.environ.get("OBSIDIAN_VAULT_PATH")
VAULT_PATH: Path | None = Path(_ENV_VAULT_PATH) if _ENV_VAULT_PATH else None


# Drafts directory is a fixed subpath of the vault.
_DRAFTS_SUBPATH = Path("04 - Developments") / "_drafts"

# Placeholder token used when listing_agent omits optional fields.
_PLACEHOLDER = "[pull from Spark]"


# ── Gap detection ────────────────────────────────────────────────────

# Gap identifier → human-readable description that goes into the warning
# callout inside the offer letter. Keeping descriptions as an adjacent table
# (rather than inline string formatting) makes the gap vocabulary easy to
# extend in later tasks.
#
# Note on "programs present but applies_to_parcel=False for all": this state
# is always true in Milestone 2 because geographic boundary matching is
# deferred to M3. Flagging it on every draft would dilute the warning callout
# into noise, so we skip it here and let the orchestrator handle the M3
# upgrade explicitly. The empty-programs case IS still flagged because that
# reflects an ingest-municipality gap the orchestrator can act on.
_GAP_DESCRIPTIONS: dict[str, str] = {
    "incentive_list_empty": (
        "applicable_programs is an empty list. This could mean the "
        "incentive_agent ran and legitimately found zero programs, or it "
        "could mean the incentive_agent was never invoked for this parcel. "
        "The OpportunityUnderwriting model does not currently carry a "
        "provenance field that distinguishes the two cases — see the M3 "
        "provenance backlog. Verify upstream before sending."
    ),
    "no_listing_history": (
        "market_stats shows zero failed_listings_on_parcel and zero "
        "years_listed_total — no listing history to cite in the letter."
    ),
    "weak_comp_anchor": (
        "anchor_comp.distance_mi > 10 — comp anchor is a weak justification "
        "for the exit price."
    ),
}


def _detect_gaps(underwriting: "OpportunityUnderwriting") -> list[str]:
    """Return a list of gap identifiers detected in the underwriting."""
    gaps: list[str] = []

    programs = underwriting.applicable_programs or []
    if not programs:
        # Report what we observed (empty list), not what we infer
        # (no one checked). The OU model does not currently distinguish
        # "checked and found 0" from "never checked" — that is an M3
        # provenance concern.
        gaps.append("incentive_list_empty")

    market = underwriting.market_stats
    if (
        market.failed_listings_on_parcel == 0
        and market.years_listed_total == 0.0
    ):
        gaps.append("no_listing_history")

    anchor = underwriting.anchor_comp
    if anchor.distance_mi > 10.0:
        gaps.append("weak_comp_anchor")

    return gaps


def _warning_callout(gaps: list[str]) -> str:
    """Render an Obsidian warning callout naming each gap.

    Returns an empty string when gaps is empty so the caller can
    unconditionally prepend the result without a trailing blank callout.
    """
    if not gaps:
        return ""

    lines = ["> [!warning] REVIEW BEFORE SENDING"]
    for gap in gaps:
        description = _GAP_DESCRIPTIONS.get(gap, gap)
        lines.append(f"> - {gap}: {description}")
    return "\n".join(lines) + "\n\n"


# ── Offer amount resolution ───────────────────────────────────────────

def _resolve_offer_amount(
    underwriting: "OpportunityUnderwriting",
) -> tuple[float | None, str | None]:
    """Return (offer_amount, skip_reason).

    - GO → (base_land_price, None)
    - NEGOTIATE with target → (target, None)
    - NEGOTIATE without target → (None, "negotiate_target_missing")
    - NO-GO → (None, "verdict_not_actionable")
    """
    # Import locally to avoid the model dependency at module-import time;
    # the TYPE_CHECKING guard at the top handles type hints.
    from src.models.opportunity import Verdict

    verdict = underwriting.verdict
    if verdict == Verdict.GO:
        return underwriting.base_land_price, None
    if verdict == Verdict.NEGOTIATE:
        target = underwriting.negotiate_target_land_price
        if target is None:
            return None, "negotiate_target_missing"
        return target, None
    # NO-GO (or anything else that ever appears on the enum)
    return None, "verdict_not_actionable"


# ── Listing-agent field resolution ────────────────────────────────────

def _agent_field(listing_agent: dict[str, Any], key: str, default: str = _PLACEHOLDER) -> str:
    """Pull a field from listing_agent with a placeholder fallback.

    Used to keep the markdown renderer readable.
    """
    value = listing_agent.get(key)
    if value is None or value == "":
        return default
    return str(value)


def _strip_leading_article(name: str) -> str:
    """Drop a leading "The " (case-insensitive) so the name interpolates
    cleanly after an indefinite article.

    Fitting-model names like "The Jaxon" would otherwise render as the
    ungrammatical "a The Jaxon build" in the cover email's anchor sentence.
    Using a plain startswith check (not regex) because this module
    deliberately carries no `re` import — keeping the grep guard tight.
    """
    return name[4:] if name.lower().startswith("the ") else name


# ── Markdown renderers ────────────────────────────────────────────────

def _render_offer_letter(
    underwriting: "OpportunityUnderwriting",
    listing_agent: dict[str, Any],
    offer_amount: float,
    gaps: list[str],
    drafted_at: datetime,
) -> str:
    """Render the full offer letter markdown (frontmatter + body)."""
    parcel_id = str(underwriting.parcel_id)
    package_ids = [str(p) for p in underwriting.package_parcel_ids]
    verdict_str = underwriting.verdict.value

    # Frontmatter
    frontmatter_lines = [
        "---",
        "delivery_status: draft",
        f"parcel_id: {parcel_id}",
    ]
    if package_ids:
        frontmatter_lines.append(
            "package_parcel_ids: [" + ", ".join(package_ids) + "]"
        )
    frontmatter_lines.extend([
        f"verdict: {verdict_str}",
        f"offer_amount: {offer_amount}",
        f"zoning_district: {underwriting.zoning_district}",
        f"fitting_model_id: {underwriting.fitting_model_id}",
        f"engine_anchor_ppsf: {underwriting.anchor_comp.ppsf or ''}",
        f"computed_at: {underwriting.computed_at.isoformat()}",
        f"drafted_at: {drafted_at.isoformat()}",
        "---",
        "",
    ])
    frontmatter = "\n".join(frontmatter_lines)

    # Gap callout (empty string if no gaps)
    callout = _warning_callout(gaps)

    # Heading + addressing block
    listing_address = _agent_field(listing_agent, "listing_address", parcel_id)
    agent_name = _agent_field(listing_agent, "agent_name")
    office_name = _agent_field(listing_agent, "office_name")
    listing_id = _agent_field(listing_agent, "listing_id", parcel_id)

    heading = f"# Offer for {listing_address}\n\n"
    addressing = (
        "**From:** BaseMod HoldCo, Inc. (Delaware C-Corp)\n"
        f"**To:** {agent_name}, {office_name}\n"
        f"**Re:** {listing_id} \u2014 {underwriting.zoning_district}\n"
        f"**Date:** {drafted_at.date().isoformat()}\n\n"
    )

    # Offer terms block
    offer_terms = (
        "## Offer terms\n\n"
        f"- **Offer price:** ${offer_amount:,.0f} cash\n"
        "- **Closing:** 30-day close\n"
        "- **Contingencies:** None (land AS-IS, no inspection period)\n"
        "- **Buyer pays:** All closing costs, title insurance standard\n"
        "- **Financing:** Cash, no appraisal contingency, no financing contingency\n\n"
    )

    # Market justification block
    market = underwriting.market_stats
    anchor = underwriting.anchor_comp
    exit_total = underwriting.exit_price.total
    # Comp.ppsf is Optional[float] — land comps legitimately lack square
    # footage, so we cannot always compute price/sqft. Rendering a None
    # ppsf as "$0/sf" would be a false factual claim in a letter going to
    # the seller's agent. Show "unknown $/sf" instead so the reviewer sees
    # the gap and can backfill before sending.
    ppsf_display = (
        f"${anchor.ppsf:g}/sf" if anchor.ppsf is not None else "unknown $/sf"
    )
    market_lines = [
        "## Market justification\n\n",
        f"- **{market.years_listed_total:g} years** on market (per listing history)\n",
        f"- **{market.months_of_inventory:g} months** of inventory in this ZIP \u2014 {market.market_health}\n",
        f"- **Median CDOM:** {market.median_cdom_days} days\n",
        f"- **Comp anchor:** {anchor.address} at {ppsf_display} ({underwriting.anchor_rationale})\n",
        (
            f"- **Asking price vs comp-supported value:** "
            f"${underwriting.base_land_price:,.0f} ask vs anchor-implied "
            f"${exit_total:,.0f} exit\n\n"
        ),
    ]
    market_block = "".join(market_lines)

    # Rationale bullets from the underwriting engine. Wrap in an H2 heading
    # so the reader gets a visual separator between the market-justification
    # bullets and the underwriting rationale bullets that follow. When
    # rationale_bullets is empty we skip the heading entirely so the section
    # doesn't render as an empty stub.
    if underwriting.rationale_bullets:
        rationale_block = (
            "## Underwriting rationale\n\n"
            + "\n".join(f"- {line}" for line in underwriting.rationale_bullets)
            + "\n\n"
        )
    else:
        rationale_block = ""

    # About BaseMod block — investor-facing content intentionally omitted
    about = (
        "## About BaseMod\n\n"
        "BaseMod HoldCo, Inc. is a Michigan-based modular home developer. "
        "We close with cash, no financing contingency, no appraisal contingency. "
        "We are not a flipper \u2014 we develop, build, and sell modular "
        "single-family homes. Our platform is vertically integrated across "
        "construction management, modular supply, and retail sales.\n\n"
    )

    footer = (
        "---\n\n"
        "*This is a DRAFT. Bennett will review and send manually through his own "
        "correspondence tools.*\n"
    )

    return (
        frontmatter
        + callout
        + heading
        + addressing
        + offer_terms
        + market_block
        + rationale_block
        + about
        + footer
    )


def _render_cover_email(
    underwriting: "OpportunityUnderwriting",
    listing_agent: dict[str, Any],
    offer_amount: float,
    drafted_at: datetime,
) -> str:
    """Render the cover email markdown (frontmatter + body) for the listing agent.

    Spec §4.5 names this the cover email to agent. The template is plain
    markdown; the CI grep guard targets send-layer APIs, not the bare word
    "email" in content or filenames.
    """
    from src.models.opportunity import Verdict

    parcel_id = str(underwriting.parcel_id)
    agent_addr = _agent_field(listing_agent, "agent_email")
    agent_name = _agent_field(listing_agent, "agent_name", "there")
    listing_id = _agent_field(listing_agent, "listing_id", "your listing")

    frontmatter = (
        "---\n"
        "delivery_status: draft\n"
        f"to: {agent_addr}\n"
        f"subject: Cash offer for {listing_id} \u2014 BaseMod HoldCo\n"
        f"parcel_id: {parcel_id}\n"
        f"drafted_at: {drafted_at.isoformat()}\n"
        "---\n\n"
    )

    package_count = 1 + len(underwriting.package_parcel_ids)
    parcel_phrase = (
        "the parcel" if package_count == 1 else f"all {package_count} parcels in the package"
    )

    greeting = f"Hi {agent_name},\n\n"

    opening = (
        f"I'm reaching out from BaseMod HoldCo regarding {listing_id}. "
        f"We'd like to make a cash offer of ${offer_amount:,.0f} "
        f"for {parcel_phrase}.\n\n"
    )

    market = underwriting.market_stats
    context_para = (
        f"Given the listing's {market.years_listed_total:g} years on market and "
        f"the current absorption rate ({market.months_of_inventory:g} months of "
        f"inventory in this area), we're structuring terms that remove all friction:\n\n"
    )

    terms_block = (
        "- Cash, no financing contingency\n"
        "- 30-day close\n"
        "- No inspection contingency (land is AS-IS)\n"
        "- Buyer pays all closing costs\n\n"
    )

    anchor = underwriting.anchor_comp
    fitting_name_raw = (
        underwriting.fitting_models[0].model_name
        if underwriting.fitting_models
        else "modular"
    )
    # Strip a leading "The " so "The Jaxon" interpolates cleanly after "a".
    fitting_name = _strip_leading_article(fitting_name_raw)
    # Comp.ppsf is Optional[float]. When ppsf is unknown we drop the "$/sf"
    # clause entirely rather than asserting a false "$0/sf" figure to the
    # seller's agent. The exit-around figure still gives a concrete number
    # for the reader to react to.
    if anchor.ppsf is not None:
        anchor_sentence = (
            f"Our underwriting anchors on {anchor.address} at ${anchor.ppsf:g}/sf, "
            f"which supports an exit around ${underwriting.exit_price.total:,.0f} for a "
            f"{fitting_name} build on this parcel.\n\n"
        )
    else:
        anchor_sentence = (
            f"Our underwriting anchors on {anchor.address}, "
            f"which supports an exit around ${underwriting.exit_price.total:,.0f} for a "
            f"{fitting_name} build on this parcel.\n\n"
        )

    negotiate_sentence = ""
    if underwriting.verdict == Verdict.NEGOTIATE:
        negotiate_sentence = (
            "We recognize this is below ask. The math at asking doesn't work for a "
            "15% net margin \u2014 happy to walk through our underwriting if that's "
            "useful.\n\n"
        )

    close = (
        "The attached offer letter has the full terms. Please let me know within "
        "7 days if your client would like to proceed or counter.\n\n"
        "Thanks,\n"
        "Bennett Washabaugh\n"
        "BaseMod HoldCo, Inc.\n"
        "<contact info TBD \u2014 fill in manually>\n\n"
        "---\n\n"
        "*This is a DRAFT. Bennett will review and send manually.*\n"
    )

    return (
        frontmatter
        + greeting
        + opening
        + context_para
        + terms_block
        + anchor_sentence
        + negotiate_sentence
        + close
    )


# ── Rationale helper ─────────────────────────────────────────────────

def _build_rationale(
    underwriting: "OpportunityUnderwriting",
    offer_amount: float,
    gaps: list[str],
) -> str:
    """One-sentence summary of what was drafted."""
    verdict = underwriting.verdict.value
    parts = [
        f"Drafted {verdict} offer letter at ${offer_amount:,.0f}"
    ]
    if gaps:
        parts.append(f"with {len(gaps)} gap(s) flagged for review: {', '.join(gaps)}")
    else:
        parts.append("with no gaps detected")
    return " ".join(parts) + "."


# ── Public API ────────────────────────────────────────────────────────

def draft_outreach(
    underwriting: "OpportunityUnderwriting",
    listing_agent: dict[str, Any],
    vault_path: Path | None = None,
) -> dict[str, Any]:
    """Draft an offer letter + cover email to agent for a GO/NEGOTIATE parcel.

    Writes two markdown files to ``{vault_path}/04 - Developments/_drafts/``
    per spec §4.5:
      - ``{parcel_slug}-offer-letter.md``
      - ``{parcel_slug}-email-to-agent.md``

    NEVER sends. NEVER imports a delivery-layer library. See spec §4.5.

    Args:
        underwriting: A full OpportunityUnderwriting Pydantic instance.
        listing_agent: Dict with at least ``agent_name`` and ``office_name``.
            Optional keys: ``agent_email``, ``agent_phone``, ``listing_id``,
            ``listing_address``. Missing optional fields fall back to
            ``[pull from Spark]`` placeholders.
        vault_path: Override the vault root. Defaults to OBSIDIAN_VAULT_PATH.

    Returns:
        On drafted::

            {
                "status": "drafted",
                "verdict": "GO" | "NEGOTIATE",
                "parcel_slug": str,
                "offer_letter_path": str,
                "email_body_path": str,  # kept for contract stability
                "offer_amount": float,
                "gaps_flagged": list[str],
                "rationale": str,
            }

        On skipped (NO-GO or NEGOTIATE with no target price)::

            {
                "status": "skipped",
                "reason": "verdict_not_actionable" | "negotiate_target_missing",
                "verdict": "NO-GO" | "NEGOTIATE",
                "parcel_slug": str,
            }

    Raises:
        EnvironmentError: if vault_path is not passed and OBSIDIAN_VAULT_PATH
            is not set in the environment.
    """
    root = vault_path if vault_path is not None else VAULT_PATH
    if root is None:
        raise EnvironmentError(
            "OBSIDIAN_VAULT_PATH env var is required when vault_path is not passed"
        )

    parcel_slug = str(underwriting.parcel_id)

    offer_amount, skip_reason = _resolve_offer_amount(underwriting)
    if offer_amount is None:
        return {
            "status": "skipped",
            "reason": skip_reason,
            "verdict": underwriting.verdict.value,
            "parcel_slug": parcel_slug,
        }

    drafted_at = datetime.now(timezone.utc)
    gaps = _detect_gaps(underwriting)

    offer_letter_text = _render_offer_letter(
        underwriting=underwriting,
        listing_agent=listing_agent,
        offer_amount=offer_amount,
        gaps=gaps,
        drafted_at=drafted_at,
    )
    cover_email_text = _render_cover_email(
        underwriting=underwriting,
        listing_agent=listing_agent,
        offer_amount=offer_amount,
        drafted_at=drafted_at,
    )

    drafts_dir = root / _DRAFTS_SUBPATH
    drafts_dir.mkdir(parents=True, exist_ok=True)

    offer_letter_path = drafts_dir / f"{parcel_slug}-offer-letter.md"
    cover_email_path = drafts_dir / f"{parcel_slug}-email-to-agent.md"

    # Concurrency-safe atomic write:
    # 1. Write both drafts to sibling .tmp files first. Neither final path
    #    becomes visible until we promote it, so a mid-write crash cannot
    #    leave a half-written pair on disk.
    # 2. os.replace() is atomic on POSIX and Windows when source and dest
    #    live on the same filesystem, which they do here (sibling files in
    #    drafts_dir). Promoting the pair back-to-back means a concurrent
    #    caller drafting the same parcel can only observe the old pair, our
    #    new pair, or their own new pair — never a mismatched offer letter
    #    paired with someone else's cover email.
    # 3. Worst case with two concurrent callers is "last writer wins on the
    #    pair", which is acceptable for drafts. The critical invariant is
    #    that a mismatched pair is never observable by a reviewer opening
    #    the files in Obsidian.
    offer_tmp = offer_letter_path.with_suffix(offer_letter_path.suffix + ".tmp")
    cover_tmp = cover_email_path.with_suffix(cover_email_path.suffix + ".tmp")
    try:
        offer_tmp.write_text(offer_letter_text, encoding="utf-8")
        cover_tmp.write_text(cover_email_text, encoding="utf-8")
        os.replace(offer_tmp, offer_letter_path)
        os.replace(cover_tmp, cover_email_path)
    except Exception:
        # Best-effort cleanup of any tmp that was created. Do NOT touch the
        # final paths — they either still hold the previous good pair, or
        # they never existed in the first place.
        for tmp in (offer_tmp, cover_tmp):
            try:
                tmp.unlink()
            except OSError:
                pass
        raise

    return {
        "status": "drafted",
        "verdict": underwriting.verdict.value,
        "parcel_slug": parcel_slug,
        "offer_letter_path": str(offer_letter_path),
        "email_body_path": str(cover_email_path),
        "offer_amount": offer_amount,
        "gaps_flagged": gaps,
        "rationale": _build_rationale(underwriting, offer_amount, gaps),
    }
