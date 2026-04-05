from __future__ import annotations

from src.models.enums import StandardStatus
from src.models.listing import Listing
from src.scoring.owner_link_evidence import analyze_owner_cluster_evidence
from src.utils.party_name_match import entity_party_key, match_party_names, person_party_key, strict_party_key


def _listing(**kwargs) -> Listing:
    base = dict(
        source_system="spark_rets",
        listing_key="TEST-001",
        standard_status=StandardStatus.ACTIVE,
        list_price=100000,
        property_type="Land",
    )
    base.update(kwargs)
    return Listing(**base)


class TestPartyNameMatch:
    def test_strict_key_basic_cleanup(self):
        assert strict_party_key("Smith Land Holdings, LLC") == "smith land holdings llc"

    def test_entity_key_collapses_suffix_variants(self):
        assert entity_party_key("Smith Land Holdings Company") == entity_party_key("Smith Land Holdings Co.")

    def test_person_key_reorders_simple_names(self):
        assert person_party_key("John A Smith") == person_party_key("Smith John A")

    def test_match_party_names_high_precision(self):
        match = match_party_names("Lincoln Realty Co.'s Horseshoe Lake", "Lincoln Realty Co Horseshoe Lake")
        assert match.matched is True
        assert match.confidence >= 0.98

    def test_match_party_names_rejects_weak_match(self):
        match = match_party_names("Devonshire Estates LLC", "Devonshire Development Group")
        assert match.matched is False


class TestOwnerLinkEvidence:
    def test_owner_name_fallback_works_when_seller_is_blank(self):
        evidence = analyze_owner_cluster_evidence(
            owner_names=["Cook Jennifer L"],
            listings=[
                _listing(
                    listing_key="OWN-1",
                    standard_status=StandardStatus.EXPIRED,
                    owner_name_raw="Cook Jennifer L",
                    seller_name_raw=None,
                )
            ],
            total_cluster_lots=7,
        )
        assert evidence.owner_linked_historical_count == 1
        assert evidence.owner_linked_failed_exit_count == 1

    def test_parcel_exact_match_works_without_party_names(self):
        evidence = analyze_owner_cluster_evidence(
            owner_names=["Unmatched Owner LLC"],
            parcel_numbers=["K-11-10-481-029", "K-11-10-481-030"],
            listings=[
                _listing(
                    listing_key="PAR-1",
                    standard_status=StandardStatus.CANCELED,
                    parcel_number_raw="K1110481029",
                    owner_name_raw=None,
                    seller_name_raw=None,
                )
            ],
            total_cluster_lots=9,
        )
        assert evidence.owner_linked_historical_count == 1
        assert evidence.owner_linked_failed_exit_count == 1
        assert evidence.owner_link_match_methods == ["parcel_exact"]
        assert evidence.owner_link_confidence == 1.0

    def test_failed_exit_counts_without_active_listing(self):
        evidence = analyze_owner_cluster_evidence(
            owner_names=["Smith Land Holdings, LLC"],
            listings=[
                _listing(
                    listing_key="HIST-1",
                    standard_status=StandardStatus.EXPIRED,
                    seller_name_raw="Smith Land Holdings LLC",
                )
            ],
            total_cluster_lots=12,
        )
        assert evidence.owner_linked_active_count == 0
        assert evidence.owner_linked_historical_count == 1
        assert evidence.owner_linked_failed_exit_count == 1
        assert evidence.owner_linked_expired_count == 1

    def test_partial_release_test_water_detected(self):
        evidence = analyze_owner_cluster_evidence(
            owner_names=["RK Investment LLC"],
            listings=[
                _listing(listing_key="L1", standard_status=StandardStatus.EXPIRED, seller_name_raw="RK Investment LLC"),
                _listing(listing_key="L2", standard_status=StandardStatus.WITHDRAWN, seller_name_raw="RK Investment LLC"),
            ],
            total_cluster_lots=20,
        )
        assert evidence.partial_release_test_water is True

    def test_repeat_agent_and_documents_and_notes(self):
        evidence = analyze_owner_cluster_evidence(
            owner_names=["Watsonia Park LLC"],
            listings=[
                _listing(
                    listing_key="L1",
                    standard_status=StandardStatus.EXPIRED,
                    seller_name_raw="Watsonia Park LLC",
                    listing_agent_name="Agent A",
                    private_remarks="all offers considered",
                    documents_count=2,
                ),
                _listing(
                    listing_key="L2",
                    standard_status=StandardStatus.CANCELED,
                    seller_name_raw="Watsonia Park LLC",
                    listing_agent_name="Agent A",
                    agent_only_remarks="survey attached",
                ),
            ],
            total_cluster_lots=9,
        )
        assert evidence.repeat_agent_on_owner_inventory is True
        assert evidence.historical_notes_present is True
        assert evidence.historical_documents_present is True
        assert evidence.historical_notes_count >= 2
        assert evidence.historical_document_count == 1
