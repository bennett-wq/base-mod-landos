"""Canonical enums for the LandOS event envelope.

Values match LANDOS_EVENT_LIBRARY.md exactly. Do not add values
without updating the architecture doc first.
"""

from enum import Enum


class EventFamily(str, Enum):
    """Which family an event belongs to (13 families)."""

    LISTING = "listing"
    CLUSTER_OWNER = "cluster_owner"
    MUNICIPAL_PROCESS = "municipal_process"
    HISTORICAL_STALL = "historical_stall"
    DEVELOPER_EXIT = "developer_exit"
    INCENTIVE = "incentive"
    PACKAGING = "packaging"
    DISTRIBUTION_DEMAND = "distribution_demand"
    TRANSACTION_EXECUTION = "transaction_execution"
    OPPORTUNITY_LIFECYCLE = "opportunity_lifecycle"
    PARCEL_STATE = "parcel_state"
    HUMAN_OPERATOR = "human_operator"
    SYSTEM_OPERATIONAL = "system_operational"


class EventClass(str, Enum):
    """Classification that determines trust level, recursion rules, and processing."""

    RAW = "raw"
    DERIVED = "derived"
    COMPOUND = "compound"


class EventStatus(str, Enum):
    """Processing state of an event."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"
    FAILED = "failed"


class RoutingClass(str, Enum):
    """Controls processing urgency and queue assignment."""

    IMMEDIATE = "immediate"
    STANDARD = "standard"
    BATCH = "batch"
    BACKGROUND = "background"
