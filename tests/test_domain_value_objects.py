"""Tests for Domain Value Objects."""
import pytest
from app.domain.value_objects import (
    CorrelationId,
    ApplicationStatus,
    ApplicationStatusType,
    JobPortal,
    PortalType,
    NATIVE_PROVIDER_PORTALS,
)


class TestCorrelationId:
    """Tests for CorrelationId value object."""

    def test_generate_creates_valid_uuid(self):
        """Test that generate() creates a valid UUID correlation ID."""
        cid = CorrelationId.generate()
        assert cid.value is not None
        assert len(cid.value) == 36  # UUID format

    def test_from_string_creates_correlation_id(self):
        """Test creating CorrelationId from a valid UUID string."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        cid = CorrelationId.from_string(valid_uuid)
        assert cid.value == valid_uuid

    def test_invalid_uuid_raises_error(self):
        """Test that invalid UUID format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid CorrelationId format"):
            CorrelationId.from_string("not-a-uuid")

    def test_empty_value_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="CorrelationId cannot be empty"):
            CorrelationId.from_string("")

    def test_str_returns_value(self):
        """Test that str() returns the UUID value."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        cid = CorrelationId.from_string(valid_uuid)
        assert str(cid) == valid_uuid

    def test_equality(self):
        """Test CorrelationId equality comparison."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        cid1 = CorrelationId.from_string(uuid)
        cid2 = CorrelationId.from_string(uuid)
        assert cid1 == cid2

    def test_hash(self):
        """Test CorrelationId can be hashed for use in sets/dicts."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        cid = CorrelationId.from_string(uuid)
        s = {cid}
        assert cid in s


class TestApplicationStatus:
    """Tests for ApplicationStatus value object."""

    def test_pending_status(self):
        """Test creating a pending status."""
        status = ApplicationStatus.pending()
        assert status.status == ApplicationStatusType.PENDING
        assert status.is_pending is True
        assert status.is_terminal is False
        assert status.can_be_modified is True
        assert status.can_be_submitted is True

    def test_sent_status(self):
        """Test creating a sent status."""
        status = ApplicationStatus.sent()
        assert status.status == ApplicationStatusType.SENT
        assert status.is_sent is True
        assert status.is_pending is False
        assert status.is_terminal is False

    def test_applied_status(self):
        """Test creating an applied status."""
        status = ApplicationStatus.applied()
        assert status.status == ApplicationStatusType.APPLIED
        assert status.is_terminal is True

    def test_failed_status_with_reason(self):
        """Test creating a failed status with reason."""
        status = ApplicationStatus.failed("Network timeout")
        assert status.status == ApplicationStatusType.FAILED
        assert status.reason == "Network timeout"
        assert status.is_terminal is True

    def test_rejected_status_with_reason(self):
        """Test creating a rejected status with reason."""
        status = ApplicationStatus.rejected("Position filled")
        assert status.status == ApplicationStatusType.REJECTED
        assert status.reason == "Position filled"
        assert status.is_terminal is True

    def test_str_without_reason(self):
        """Test string representation without reason."""
        status = ApplicationStatus.pending()
        assert str(status) == "pending"

    def test_str_with_reason(self):
        """Test string representation with reason."""
        status = ApplicationStatus.failed("Error occurred")
        assert str(status) == "failed: Error occurred"


class TestJobPortal:
    """Tests for JobPortal value object."""

    def test_from_string_normalizes_case(self):
        """Test that from_string normalizes to lowercase."""
        portal = JobPortal.from_string("WORKDAY")
        assert portal.name == "workday"

    def test_from_string_strips_whitespace(self):
        """Test that from_string strips whitespace."""
        portal = JobPortal.from_string("  greenhouse  ")
        assert portal.name == "greenhouse"

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Portal name cannot be empty"):
            JobPortal.from_string("")

    def test_native_provider_detection(self):
        """Test native provider detection for known portals."""
        for portal_name in ["workday", "greenhouse", "smartrecruiters", "dice", "lever"]:
            portal = JobPortal.from_string(portal_name)
            assert portal.has_native_provider is True
            assert portal.requires_browser_automation is False
            assert portal.get_applier_queue() == "providers_queue"

    def test_browser_automation_for_unknown_portal(self):
        """Test that unknown portals require browser automation."""
        portal = JobPortal.from_string("some_unknown_portal")
        assert portal.has_native_provider is False
        assert portal.requires_browser_automation is True
        assert portal.get_applier_queue() == "skyvern_queue"

    def test_portal_type_for_known_portal(self):
        """Test portal_type returns correct enum for known portals."""
        portal = JobPortal.from_string("workday")
        assert portal.portal_type == PortalType.WORKDAY

    def test_portal_type_for_unknown_portal(self):
        """Test portal_type returns UNKNOWN for unknown portals."""
        portal = JobPortal.from_string("some_custom_ats")
        assert portal.portal_type == PortalType.UNKNOWN

    def test_all_native_providers_in_enum(self):
        """Test that all native providers have corresponding enum values."""
        for portal_name in NATIVE_PROVIDER_PORTALS:
            portal = JobPortal.from_string(portal_name)
            assert portal.portal_type != PortalType.UNKNOWN

    def test_equality(self):
        """Test JobPortal equality comparison."""
        portal1 = JobPortal.from_string("workday")
        portal2 = JobPortal.from_string("WORKDAY")
        assert portal1 == portal2

    def test_hash(self):
        """Test JobPortal can be hashed."""
        portal = JobPortal.from_string("greenhouse")
        s = {portal}
        assert portal in s

    def test_str(self):
        """Test string representation."""
        portal = JobPortal.from_string("Dice")
        assert str(portal) == "dice"
