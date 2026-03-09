"""Canonical enums for LandOS Phase 1 object models.

Values match LANDOS_OBJECT_MODEL.md exactly. Do not add values
without updating the architecture doc first.
"""

from enum import Enum


# ── Parcel ───────────────────────────────────────────────────────────

class VacancyStatus(str, Enum):
    VACANT = "vacant"
    IMPROVED = "improved"
    PARTIALLY_IMPROVED = "partially_improved"
    UNKNOWN = "unknown"


# ── Listing ──────────────────────────────────────────────────────────

class StandardStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    CANCELED = "canceled"


# ── Municipality ─────────────────────────────────────────────────────

class MunicipalityType(str, Enum):
    CITY = "city"
    TOWNSHIP = "township"
    VILLAGE = "village"
    CHARTER_TOWNSHIP = "charter_township"


class ApprovalAuthorityType(str, Enum):
    PLANNING_COMMISSION = "planning_commission"
    ZONING_BOARD = "zoning_board"
    BOARD_OF_TRUSTEES = "board_of_trustees"
    CITY_COUNCIL = "city_council"
    OTHER = "other"


class LandDivisionPosture(str, Enum):
    PERMISSIVE = "permissive"
    MODERATE = "moderate"
    RESTRICTIVE = "restrictive"
    UNKNOWN = "unknown"


class SB23Posture(str, Enum):
    ADOPTED = "adopted"
    PARTIAL = "partial"
    NOT_ADOPTED = "not_adopted"
    UNKNOWN = "unknown"


class Section108_6Posture(str, Enum):
    AUTHORIZED = "authorized"
    CONSIDERING = "considering"
    NOT_AUTHORIZED = "not_authorized"
    UNKNOWN = "unknown"


class SewerServiceType(str, Enum):
    MUNICIPAL_SEWER = "municipal_sewer"
    SEPTIC_ALLOWED = "septic_allowed"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class WaterServiceType(str, Enum):
    MUNICIPAL_WATER = "municipal_water"
    WELL_ALLOWED = "well_allowed"
    MIXED = "mixed"
    UNKNOWN = "unknown"


# ── MunicipalEvent ───────────────────────────────────────────────────

class MunicipalEventType(str, Enum):
    PLAT_RECORDED = "plat_recorded"
    SITE_PLAN_APPROVED = "site_plan_approved"
    ENGINEERING_APPROVED = "engineering_approved"
    PERMIT_PULLED = "permit_pulled"
    BOND_POSTED = "bond_posted"
    BOND_EXTENDED = "bond_extended"
    BOND_RELEASED = "bond_released"
    ROADS_INSTALLED = "roads_installed"
    ROADS_ACCEPTED = "roads_accepted"
    SEWER_EXTENDED = "sewer_extended"
    WATER_EXTENDED = "water_extended"
    MASTER_DEED_RECORDED = "master_deed_recorded"
    HOA_CREATED = "hoa_created"
    RULE_CHANGE = "rule_change"
    INCENTIVE_CREATED = "incentive_created"


class OccurredAtPrecision(str, Enum):
    EXACT = "exact"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ESTIMATED = "estimated"


# ── Owner ────────────────────────────────────────────────────────────

class OwnerEntityType(str, Enum):
    INDIVIDUAL = "individual"
    MARRIED_COUPLE = "married_couple"
    LLC = "llc"
    TRUST = "trust"
    ESTATE = "estate"
    CORPORATION = "corporation"
    LAND_CONTRACT = "land_contract"
    GOVERNMENT = "government"
    UNKNOWN = "unknown"


# ── OwnerCluster ─────────────────────────────────────────────────────

class ClusterType(str, Enum):
    SAME_OWNER = "same_owner"
    SAME_AGENT = "same_agent"
    SAME_OFFICE = "same_office"
    SAME_SUBDIVISION = "same_subdivision"
    GEOGRAPHIC_PROXIMITY = "geographic_proximity"
    MIXED = "mixed"


# ── Subdivision / SiteCondoProject (shared) ──────────────────────────

class InfrastructureStatus(str, Enum):
    ROADS_INSTALLED = "roads_installed"
    ROADS_ACCEPTED = "roads_accepted"
    ROADS_PARTIAL = "roads_partial"
    NO_ROADS = "no_roads"
    UNKNOWN = "unknown"


class ConnectionStatus(str, Enum):
    """Sewer/water connection status for subdivisions and site condo projects."""
    MUNICIPAL_CONNECTED = "municipal_connected"
    SEPTIC = "septic"
    WELL = "well"
    PLANNED = "planned"
    UNKNOWN = "unknown"


class BondStatus(str, Enum):
    ACTIVE = "active"
    EXTENDED = "extended"
    RELEASED = "released"
    DEFAULTED = "defaulted"
    UNKNOWN = "unknown"


# ── DeveloperEntity ──────────────────────────────────────────────────

class DeveloperEntityType(str, Enum):
    BUILDER = "builder"
    DEVELOPER = "developer"
    LAND_COMPANY = "land_company"
    INVESTMENT_GROUP = "investment_group"
    INDIVIDUAL = "individual"
    UNKNOWN = "unknown"


# ── Opportunity ──────────────────────────────────────────────────────

class OpportunityType(str, Enum):
    STRANDED_LOT = "stranded_lot"
    STALLED_SUBDIVISION = "stalled_subdivision"
    STALLED_SITE_CONDO = "stalled_site_condo"
    LAND_DIVISION_CANDIDATE = "land_division_candidate"
    DEVELOPER_EXIT = "developer_exit"
    INFILL = "infill"
    OTHER = "other"


class OpportunityStatus(str, Enum):
    DETECTED = "detected"
    SCORED = "scored"
    FIT_CHECKED = "fit_checked"
    PACKAGED = "packaged"
    DISTRIBUTED = "distributed"
    ENGAGED = "engaged"
    CONVERTED = "converted"
    REJECTED = "rejected"
    STALE = "stale"


class PackagingReadiness(str, Enum):
    NOT_STARTED = "not_started"
    FIT_IN_PROGRESS = "fit_in_progress"
    FIT_COMPLETE = "fit_complete"
    ESTIMATE_IN_PROGRESS = "estimate_in_progress"
    PACKAGED = "packaged"
    NEEDS_REVIEW = "needs_review"


# ── HomeProduct ──────────────────────────────────────────────────────

class GarageType(str, Enum):
    ATTACHED = "attached"
    DETACHED = "detached"
    NONE = "none"


class FoundationType(str, Enum):
    SLAB = "slab"
    CRAWL = "crawl"
    BASEMENT = "basement"
    FLEXIBLE = "flexible"


# ── SiteFit ──────────────────────────────────────────────────────────

class FitResult(str, Enum):
    FITS = "fits"
    MARGINAL = "marginal"
    DOES_NOT_FIT = "does_not_fit"
    INSUFFICIENT_DATA = "insufficient_data"


class SetbackFitResult(str, Enum):
    CLEAR = "clear"
    TIGHT = "tight"
    VIOLATION = "violation"
    UNKNOWN = "unknown"


class SewerAvailable(str, Enum):
    MUNICIPAL_AT_LOT = "municipal_at_lot"
    MUNICIPAL_NEARBY = "municipal_nearby"
    SEPTIC_REQUIRED = "septic_required"
    UNKNOWN = "unknown"


class WaterAvailable(str, Enum):
    MUNICIPAL_AT_LOT = "municipal_at_lot"
    MUNICIPAL_NEARBY = "municipal_nearby"
    WELL_REQUIRED = "well_required"
    UNKNOWN = "unknown"


class UtilityOverallStatus(str, Enum):
    ALL_AVAILABLE = "all_available"
    PARTIAL = "partial"
    MAJOR_WORK_NEEDED = "major_work_needed"
    UNKNOWN = "unknown"


class AccessType(str, Enum):
    PAVED_ROAD = "paved_road"
    GRAVEL_ROAD = "gravel_road"
    PRIVATE_ROAD = "private_road"
    NO_ACCESS = "no_access"
    UNKNOWN = "unknown"


# ── AgentRun ─────────────────────────────────────────────────────────

class AgentRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CIRCUIT_BROKEN = "circuit_broken"


# ── Action ───────────────────────────────────────────────────────────

class ActionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"
    BLOCKED = "blocked"
