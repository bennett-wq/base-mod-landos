"""Spark MLS ingestion adapter — public API."""

from src.adapters.spark.ingestion import InMemoryListingStore, SparkIngestionAdapter
from src.adapters.spark.normalizer import SkipRecord

__all__ = [
    "SparkIngestionAdapter",
    "InMemoryListingStore",
    "SkipRecord",
]
