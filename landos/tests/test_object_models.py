"""Tests for Phase 1 object models — Step 2 acceptance criteria.

Proves:
1. Each of the 14 objects can be instantiated with minimum required fields.
2. Missing required fields fail validation.
3. Invalid enum values fail validation.
4. Serialization works for representative objects.
5. Confidence field range is enforced where validated.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.parcel import Parcel
from src.models.listing import Listing
from src.models.municipality import Municipality, MunicipalEvent
from src.models.owner import Owner, OwnerCluster
from src.models.development import Subdivision, SiteCondoProject, DeveloperEntity
from src.models.opportunity import Opportunity
from src.models.product import HomeProduct, SiteFit
from src.models.system import AgentRun, Action
from src.models.enums import (
    VacancyStatus,
    StandardStatus,
    MunicipalityType,
    MunicipalEventType,
    OwnerEntityType,
    ClusterType,
    DeveloperEntityType,
    OpportunityType,
    OpportunityStatus,
    FitResult,
    AgentRunStatus,
    ActionStatus,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── 1. Parcel ────────────────────────────────────────────────────────

class TestParcel:
    def test_create_minimal(self):
        p = Parcel(
            source_system_ids={"regrid_id": "R123"},
            jurisdiction_state="MI",
            county="Washtenaw",
            municipality_id=uuid4(),
            apn_or_parcel_number="12-34-567-890",
            acreage=0.45,
            vacancy_status=VacancyStatus.VACANT,
        )
        assert p.parcel_id is not None
        assert p.vacancy_status == VacancyStatus.VACANT
        assert p.current_owner_id is None

    def test_missing_required_fails(self):
        with pytest.raises(ValidationError):
            Parcel(
                source_system_ids={"regrid_id": "R123"},
                jurisdiction_state="MI",
                # missing county, municipality_id, apn, acreage, vacancy_status
            )

    def test_invalid_vacancy_status(self):
        with pytest.raises(ValidationError, match="vacancy_status"):
            Parcel(
                source_system_ids={"regrid_id": "R123"},
                jurisdiction_state="MI",
                county="Washtenaw",
                municipality_id=uuid4(),
                apn_or_parcel_number="12-34-567-890",
                acreage=0.45,
                vacancy_status="demolished",
            )

    def test_serialization(self):
        p = Parcel(
            source_system_ids={"regrid_id": "R123"},
            jurisdiction_state="MI",
            county="Washtenaw",
            municipality_id=uuid4(),
            apn_or_parcel_number="12-34-567-890",
            acreage=0.45,
            vacancy_status=VacancyStatus.VACANT,
        )
        d = p.model_dump()
        assert d["jurisdiction_state"] == "MI"
        assert d["vacancy_status"] == "vacant"


# ── 2. Listing ───────────────────────────────────────────────────────

class TestListing:
    def test_create_minimal(self):
        l = Listing(
            source_system="spark_rets",
            listing_key="MLS-99999",
            standard_status=StandardStatus.ACTIVE,
            list_price=85000,
            property_type="vacant_land",
        )
        assert l.listing_id is not None
        assert l.standard_status == StandardStatus.ACTIVE
        assert l.parcel_id is None

    def test_missing_required_fails(self):
        with pytest.raises(ValidationError):
            Listing(source_system="spark_rets")

    def test_invalid_standard_status(self):
        with pytest.raises(ValidationError, match="standard_status"):
            Listing(
                source_system="spark_rets",
                listing_key="MLS-99999",
                standard_status="sold",
                list_price=85000,
                property_type="vacant_land",
            )


# ── 3. Municipality ──────────────────────────────────────────────────

class TestMunicipality:
    def test_create_minimal(self):
        m = Municipality(
            name="Ypsilanti Charter Township",
            municipality_type=MunicipalityType.CHARTER_TOWNSHIP,
            state="MI",
            county="Washtenaw",
        )
        assert m.municipality_id is not None
        assert m.land_division_posture is None

    def test_invalid_municipality_type(self):
        with pytest.raises(ValidationError, match="municipality_type"):
            Municipality(
                name="Test",
                municipality_type="borough",
                state="MI",
                county="Washtenaw",
            )


# ── 4. MunicipalEvent ───────────────────────────────────────────────

class TestMunicipalEvent:
    def test_create_minimal(self):
        me = MunicipalEvent(
            municipality_id=uuid4(),
            event_type=MunicipalEventType.PLAT_RECORDED,
            occurred_at=_now(),
            source_system="register_of_deeds",
        )
        assert me.municipal_event_id is not None
        assert me.details is None

    def test_with_details(self):
        me = MunicipalEvent(
            municipality_id=uuid4(),
            event_type=MunicipalEventType.PLAT_RECORDED,
            occurred_at=_now(),
            source_system="register_of_deeds",
            details={
                "plat_name": "Sunrise Meadows",
                "total_lots": 42,
                "recording_date": "2015-06-15",
            },
        )
        assert me.details["plat_name"] == "Sunrise Meadows"

    def test_invalid_event_type(self):
        with pytest.raises(ValidationError, match="event_type"):
            MunicipalEvent(
                municipality_id=uuid4(),
                event_type="demolition_ordered",
                occurred_at=_now(),
                source_system="register_of_deeds",
            )


# ── 5. Owner ─────────────────────────────────────────────────────────

class TestOwner:
    def test_create_minimal(self):
        o = Owner(
            owner_name_normalized="SMITH JOHN A",
            entity_type=OwnerEntityType.INDIVIDUAL,
        )
        assert o.owner_id is not None
        assert o.parcel_count is None

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError, match="entity_type"):
            Owner(
                owner_name_normalized="TEST",
                entity_type="partnership",
            )


# ── 6. OwnerCluster ──────────────────────────────────────────────────

class TestOwnerCluster:
    def test_create_minimal(self):
        c = OwnerCluster(
            cluster_type=ClusterType.SAME_OWNER,
            detection_method="owner_name_match",
            member_count=4,
        )
        assert c.cluster_id is not None
        assert c.fatigue_score is None

    def test_missing_member_count(self):
        with pytest.raises(ValidationError):
            OwnerCluster(
                cluster_type=ClusterType.SAME_OWNER,
                detection_method="owner_name_match",
            )


# ── 7. Subdivision ───────────────────────────────────────────────────

class TestSubdivision:
    def test_create_minimal(self):
        s = Subdivision(
            name="Sunrise Meadows",
            municipality_id=uuid4(),
            county="Washtenaw",
            state="MI",
        )
        assert s.subdivision_id is not None
        assert s.stall_flag is None

    def test_serialization_with_optionals(self):
        s = Subdivision(
            name="Sunrise Meadows",
            municipality_id=uuid4(),
            county="Washtenaw",
            state="MI",
            total_lots=42,
            vacant_lots=28,
            vacancy_ratio=0.667,
            stall_flag=True,
        )
        d = s.model_dump()
        assert d["total_lots"] == 42
        assert d["stall_flag"] is True


# ── 8. SiteCondoProject ─────────────────────────────────────────────

class TestSiteCondoProject:
    def test_create_minimal(self):
        sc = SiteCondoProject(
            name="Lakewood Site Condos",
            municipality_id=uuid4(),
            county="Washtenaw",
            state="MI",
        )
        assert sc.site_condo_project_id is not None
        assert sc.vacancy_ratio is None

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            SiteCondoProject(
                municipality_id=uuid4(),
                county="Washtenaw",
                state="MI",
            )


# ── 9. DeveloperEntity ──────────────────────────────────────────────

class TestDeveloperEntity:
    def test_create_minimal(self):
        de = DeveloperEntity(
            name="Acme Land Co",
            entity_type=DeveloperEntityType.LAND_COMPANY,
        )
        assert de.developer_entity_id is not None
        assert de.exit_window_flag is None

    def test_invalid_entity_type(self):
        with pytest.raises(ValidationError, match="entity_type"):
            DeveloperEntity(
                name="Test",
                entity_type="nonprofit",
            )


# ── 10. Opportunity ──────────────────────────────────────────────────

class TestOpportunity:
    def test_create_minimal(self):
        o = Opportunity(
            opportunity_type=OpportunityType.STALLED_SUBDIVISION,
            parcel_ids=[uuid4(), uuid4()],
            municipality_id=uuid4(),
            status=OpportunityStatus.DETECTED,
        )
        assert o.opportunity_id is not None
        assert len(o.parcel_ids) == 2
        assert o.opportunity_score is None

    def test_invalid_opportunity_type(self):
        with pytest.raises(ValidationError, match="opportunity_type"):
            Opportunity(
                opportunity_type="foreclosure",
                parcel_ids=[uuid4()],
                municipality_id=uuid4(),
                status=OpportunityStatus.DETECTED,
            )

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status"):
            Opportunity(
                opportunity_type=OpportunityType.STRANDED_LOT,
                parcel_ids=[uuid4()],
                municipality_id=uuid4(),
                status="approved",
            )

    def test_serialization(self):
        o = Opportunity(
            opportunity_type=OpportunityType.DEVELOPER_EXIT,
            parcel_ids=[uuid4()],
            municipality_id=uuid4(),
            status=OpportunityStatus.SCORED,
            opportunity_score=0.82,
        )
        d = o.model_dump()
        assert d["opportunity_type"] == "developer_exit"
        assert d["status"] == "scored"
        assert d["opportunity_score"] == 0.82


# ── 11. HomeProduct ──────────────────────────────────────────────────

class TestHomeProduct:
    def test_create_minimal(self):
        hp = HomeProduct(
            model_name="BM-1200",
            footprint_width_feet=28.0,
            footprint_depth_feet=44.0,
            stories=1,
            square_footage=1200,
            base_price=165000,
        )
        assert hp.home_product_id is not None
        assert hp.garage_type is None

    def test_missing_required_fails(self):
        with pytest.raises(ValidationError):
            HomeProduct(
                model_name="BM-1200",
                # missing footprint, stories, sq ft, price
            )

    def test_serialization(self):
        hp = HomeProduct(
            model_name="BM-1200",
            footprint_width_feet=28.0,
            footprint_depth_feet=44.0,
            stories=1,
            square_footage=1200,
            base_price=165000,
            bedrooms=3,
            bathrooms=2.0,
        )
        j = hp.model_dump_json()
        assert '"BM-1200"' in j


# ── 12. SiteFit ──────────────────────────────────────────────────────

class TestSiteFit:
    def test_create_minimal(self):
        sf = SiteFit(
            parcel_id=uuid4(),
            home_product_id=uuid4(),
            fit_result=FitResult.FITS,
            fit_confidence=0.92,
        )
        assert sf.site_fit_id is not None
        assert sf.setback_fit_result is None

    def test_invalid_fit_result(self):
        with pytest.raises(ValidationError, match="fit_result"):
            SiteFit(
                parcel_id=uuid4(),
                home_product_id=uuid4(),
                fit_result="maybe",
                fit_confidence=0.5,
            )

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError, match="fit_confidence"):
            SiteFit(
                parcel_id=uuid4(),
                home_product_id=uuid4(),
                fit_result=FitResult.FITS,
                fit_confidence=1.5,
            )

    def test_confidence_at_bounds(self):
        sf_lo = SiteFit(
            parcel_id=uuid4(), home_product_id=uuid4(),
            fit_result=FitResult.INSUFFICIENT_DATA, fit_confidence=0.0,
        )
        sf_hi = SiteFit(
            parcel_id=uuid4(), home_product_id=uuid4(),
            fit_result=FitResult.FITS, fit_confidence=1.0,
        )
        assert sf_lo.fit_confidence == 0.0
        assert sf_hi.fit_confidence == 1.0

    def test_with_setback_and_utility_fields(self):
        sf = SiteFit(
            parcel_id=uuid4(),
            home_product_id=uuid4(),
            fit_result=FitResult.MARGINAL,
            fit_confidence=0.65,
            front_setback_required_feet=25.0,
            front_setback_available_feet=27.0,
            setback_fit_result="tight",
            sewer_available="municipal_at_lot",
            utility_overall_status="all_available",
        )
        assert sf.setback_fit_result.value == "tight"
        assert sf.sewer_available.value == "municipal_at_lot"


# ── 13. AgentRun ─────────────────────────────────────────────────────

class TestAgentRun:
    def test_create_minimal(self):
        ar = AgentRun(
            agent_type="listing_ingestion",
            started_at=_now(),
            status=AgentRunStatus.RUNNING,
        )
        assert ar.agent_run_id is not None
        assert ar.completed_at is None

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status"):
            AgentRun(
                agent_type="test",
                started_at=_now(),
                status="paused",
            )


# ── 14. Action ───────────────────────────────────────────────────────

class TestAction:
    def test_create_minimal(self):
        a = Action(
            action_type="outreach",
            status=ActionStatus.PENDING,
        )
        assert a.action_id is not None
        assert a.assigned_to is None

    def test_invalid_status(self):
        with pytest.raises(ValidationError, match="status"):
            Action(
                action_type="review",
                status="deferred",
            )

    def test_serialization(self):
        a = Action(
            action_type="follow_up",
            status=ActionStatus.IN_PROGRESS,
            assigned_to="operator@basemod.com",
            notes="Check zoning variance status",
        )
        d = a.model_dump()
        assert d["status"] == "in_progress"
        assert d["assigned_to"] == "operator@basemod.com"


# ── Cross-model: __init__.py re-exports ──────────────────────────────

class TestModelsInit:
    def test_all_14_importable(self):
        """Confirm all 14 objects are importable from src.models."""
        from src.models import (
            Parcel, Listing, Municipality, MunicipalEvent,
            Owner, OwnerCluster, Subdivision, SiteCondoProject,
            DeveloperEntity, Opportunity, HomeProduct, SiteFit,
            AgentRun, Action,
        )
        assert all([
            Parcel, Listing, Municipality, MunicipalEvent,
            Owner, OwnerCluster, Subdivision, SiteCondoProject,
            DeveloperEntity, Opportunity, HomeProduct, SiteFit,
            AgentRun, Action,
        ])
