from __future__ import annotations

from scripts.ingest_spark_live import select_current_records


class TestCurrentStateSelection:
    def test_active_beats_expired_for_same_listing_key(self):
        records = [
            {
                "ListingKey": "L1",
                "StandardStatus": "Expired",
                "StatusChangeTimestamp": "2026-03-01T10:00:00Z",
            },
            {
                "ListingKey": "L1",
                "StandardStatus": "Active",
                "StatusChangeTimestamp": "2026-02-01T10:00:00Z",
            },
        ]
        current = select_current_records(records)
        assert len(current) == 1
        assert current[0]["StandardStatus"] == "Active"

    def test_more_recent_same_status_wins(self):
        records = [
            {
                "ListingKey": "L1",
                "StandardStatus": "Expired",
                "StatusChangeTimestamp": "2026-01-01T10:00:00Z",
            },
            {
                "ListingKey": "L1",
                "StandardStatus": "Expired",
                "StatusChangeTimestamp": "2026-02-01T10:00:00Z",
            },
        ]
        current = select_current_records(records)
        assert len(current) == 1
        assert current[0]["StatusChangeTimestamp"] == "2026-02-01T10:00:00Z"
