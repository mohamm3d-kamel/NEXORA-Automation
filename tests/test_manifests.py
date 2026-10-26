import re
import pytest
from playwright.sync_api import Page, expect
from pages.manifests_page import ManifestsPage


@pytest.mark.manifests
class TestManifestsModule:
    """Comprehensive test suite for Delivery and Pickup Manifests management."""

    # =========================================================================
    # VALID SCENARIOS
    # =========================================================================

    @pytest.mark.smoke
    @pytest.mark.valid
    def test_valid_navigate_all_manifest_tabs(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        Verify navigation to all 4 manifest sub-sections:
        - Delivery Manifests
        - Ready for Delivery Manifests
        - IntraHub Manifests
        - Return Manifests
        and assert correct URLs and non-empty table headers.
        """
        manifests = authenticated_manifests

        # 1. Delivery Manifests
        manifests.open_delivery_manifests()
        assert "delivery-manifests" in manifests.page.url
        dm_headers = manifests.get_table_headers()
        assert "Manifest ID" in dm_headers
        assert "Driver" in dm_headers
        assert "Status" in dm_headers

        # 2. Ready for Delivery Manifests
        manifests.open_ready_for_delivery_manifests()
        assert "ready-for-delivery-manifests" in manifests.page.url
        rfd_headers = manifests.get_table_headers()
        assert "Manifest ID" in rfd_headers
        assert "Driver" in rfd_headers
        assert "Status" in rfd_headers

        # 3. Intra-Hub Manifests
        manifests.open_intra_hub_manifests()
        assert "intra-hub-manifests" in manifests.page.url
        intra_headers = manifests.get_table_headers()
        assert "Manifest ID" in intra_headers
        assert "Source Branch" in intra_headers

        # 4. Return Manifests
        manifests.open_return_manifests()
        assert "return-manifests" in manifests.page.url
        return_headers = manifests.get_table_headers()
        assert "Manifest ID" in return_headers
        assert "Branch" in return_headers

    @pytest.mark.smoke
    @pytest.mark.valid
    def test_valid_delivery_manifests_table_data(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        Assert Delivery Manifests list contains real manifest rows with DM- identifiers and status labels.
        """
        manifests = authenticated_manifests.open_delivery_manifests()
        row_count = manifests.get_row_count()
        assert row_count > 0, "Expected at least one delivery manifest row"

        rows_text = manifests.get_all_rows_text()
        has_dm = any("DM-" in row for row in rows_text)
        assert has_dm, f"Expected rows to contain 'DM-' identifier, got: {rows_text[:3]}"

    @pytest.mark.smoke
    @pytest.mark.valid
    def test_valid_delivery_manifest_detail_view_and_shipments(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        Click on a delivery manifest link, verify navigation to detail page (/delivery-manifests/{id}),
        manifest header title card, and shipments table with shipment items.
        """
        manifests = authenticated_manifests.open_delivery_manifests()
        manifests.open_delivery_manifest_detail()

        assert "delivery-manifests/" in manifests.page.url
        detail_text = manifests.get_detail_page_text()

        # Check detail card labels
        assert "Manifest DM-" in detail_text
        assert "Shipments" in detail_text
        assert "Status" in detail_text

        # Verify shipments table headers
        headers = manifests.get_table_headers()
        assert any("Shipment Number" in h for h in headers)
        assert any("Recipient" in h for h in headers)

    @pytest.mark.regression
    @pytest.mark.valid
    def test_valid_delivery_manifest_export_excel(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        From delivery manifest detail view, click 'Export to Excel' and verify browser file download.
        """
        manifests = authenticated_manifests.open_delivery_manifests()
        manifests.open_delivery_manifest_detail()

        download = manifests.export_to_excel()
        filename = download.suggested_filename
        assert filename.endswith(".xlsx"), f"Expected .xlsx extension, got: {filename}"
        assert "delivery-manifest-DM-" in filename, f"Expected manifest ID in filename, got: {filename}"

    @pytest.mark.regression
    @pytest.mark.valid
    def test_valid_ready_for_delivery_manifest_detail_and_back(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        Open Ready for Delivery Manifests, verify RFD table data, navigate to detail view,
        and click Back to return safely to the RFD list view.
        """
        manifests = authenticated_manifests.open_ready_for_delivery_manifests()
        assert manifests.get_row_count() > 0, "Expected at least one RFD row"

        manifests.open_ready_manifest_detail()
        assert "ready-for-delivery-manifests/" in manifests.page.url

        # Click Back
        manifests.click_detail_back()
        assert "ready-for-delivery-manifests" in manifests.page.url
        assert manifests.get_row_count() > 0

    @pytest.mark.regression
    @pytest.mark.valid
    def test_valid_admin_pickups_table_headers_and_search(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        Navigate to Admin Pickups view, verify table headers, and execute search by PICK- prefix.
        """
        manifests = authenticated_manifests.open_admin_pickups()
        headers = manifests.get_table_headers()

        expected = ["Pickup Number", "Type", "Pickup Status", "Driver", "Branch", "Merchant Name"]
        for exp in expected:
            assert any(exp in h for h in headers), f"Expected header '{exp}' in {headers}"

        # Search by PICK-
        manifests.search_pickup("PICK-")
        rows = manifests.get_pickup_rows_text()
        assert len(rows) > 0, "Expected pickup rows matching 'PICK-'"

    @pytest.mark.regression
    @pytest.mark.valid
    def test_valid_pickup_detail_view_inspection(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        Click on a pickup number link from Admin Pickups and verify details view/parameter loaded.
        """
        manifests = authenticated_manifests.open_admin_pickups()
        manifests.open_pickup_detail()

        assert "pickupId=" in manifests.page.url or "pickups/" in manifests.page.url
        page_text = manifests.page.inner_text("body")
        assert "Pickup" in page_text

    @pytest.mark.regression
    @pytest.mark.valid
    def test_valid_pickup_driver_assigned_reflection(self, authenticated_manifests: ManifestsPage):
        """
        Valid Scenario:
        Verify that in Admin Pickups table, pickups with driver assigned display driver information.
        """
        manifests = authenticated_manifests.open_admin_pickups()
        rows = manifests.get_pickup_rows_text()

        # Check for accepted or assigned driver status
        has_driver_status = any("Driver Accepted" in r or "Driver Assigned" in r or "Pending" in r for r in rows)
        assert has_driver_status, f"Expected recognizable pickup lifecycle status, got: {rows[:2]}"

    # =========================================================================
    # INVALID / NEGATIVE SCENARIOS
    # =========================================================================

    @pytest.mark.regression
    @pytest.mark.invalid
    def test_invalid_intra_hub_manifest_missing_required_fields(self, authenticated_manifests: ManifestsPage):
        """
        Invalid Scenario:
        On Intra-Hub Manifest creation form, click Next without selecting required fields
        and verify mandatory field validation errors.
        """
        manifests = authenticated_manifests.open_create_intra_hub()
        manifests.click_create_next()

        errors = manifests.get_validation_errors()
        assert "Branch is required" in errors
        assert "Destination branch is required" in errors
        assert "Loading type is required" in errors

        # Cleanup: Cancel back to list
        manifests.click_create_cancel()
        assert "intra-hub-manifests" in manifests.page.url

    @pytest.mark.regression
    @pytest.mark.invalid
    def test_invalid_return_manifest_missing_required_fields(self, authenticated_manifests: ManifestsPage):
        """
        Invalid Scenario:
        On Return Manifest creation form, click Next without selecting required fields
        and verify mandatory field validation errors.
        """
        manifests = authenticated_manifests.open_create_return_manifest()
        manifests.click_create_next()

        errors = manifests.get_validation_errors()
        assert "Branch is required" in errors
        assert "Merchant is required" in errors
        assert "Destination address is required" in errors
        assert "Loading type is required" in errors

        # Cleanup: Cancel back to list
        manifests.click_create_cancel()
        assert "return-manifests" in manifests.page.url

    @pytest.mark.regression
    @pytest.mark.invalid
    def test_invalid_search_nonexistent_manifest(self, authenticated_manifests: ManifestsPage):
        """
        Invalid Scenario:
        Search for a nonexistent manifest ID on Delivery Manifests and verify empty state 'No Data' is shown.
        """
        manifests = authenticated_manifests.open_delivery_manifests()
        manifests.search_manifest("DM-NONEXISTENT-999999")

        assert manifests.is_empty_state_visible(), "Expected 'No Data' empty state for nonexistent manifest search"
        assert manifests.get_row_count() == 0

    # =========================================================================
    # EDGE SCENARIOS
    # =========================================================================

    @pytest.mark.regression
    @pytest.mark.edge
    def test_edge_rapid_tab_switching_preserves_stability(self, authenticated_manifests: ManifestsPage):
        """
        Edge Scenario:
        Rapidly switch across all manifest tabs (Delivery, Ready for Delivery, IntraHub, Return Manifests)
        and verify UI maintains state and final tab table renders cleanly without hanging spinners.
        """
        manifests = authenticated_manifests.open_delivery_manifests()

        manifests.switch_tab("Ready for Delivery Manifests")
        assert "ready-for-delivery-manifests" in manifests.page.url

        manifests.switch_tab("IntraHub Manifests")
        assert "intra-hub-manifests" in manifests.page.url

        manifests.switch_tab("Return Manifests")
        assert "return-manifests" in manifests.page.url

        manifests.switch_tab("Delivery Manifests")
        assert "delivery-manifests" in manifests.page.url
        assert manifests.get_row_count() > 0

    @pytest.mark.regression
    @pytest.mark.edge
    def test_edge_delivery_manifest_print_button_interaction(self, authenticated_manifests: ManifestsPage):
        """
        Edge Scenario:
        On Delivery Manifest details view, verify Print button is rendered, enabled, and can be clicked safely.
        """
        manifests = authenticated_manifests.open_delivery_manifests()
        manifests.open_delivery_manifest_detail()

        assert manifests.is_print_button_enabled(), "Expected Print button to be enabled on manifest details view"
        manifests.click_print()

    @pytest.mark.regression
    @pytest.mark.edge
    def test_edge_pickups_search_nonexistent_handles_empty_state(self, authenticated_manifests: ManifestsPage):
        """
        Edge Scenario:
        Search for nonexistent pickup identifier in Admin Pickups and assert clean empty state handling.
        """
        manifests = authenticated_manifests.open_admin_pickups()
        manifests.search_pickup("PICK-NONEXISTENT-999999")

        assert manifests.is_empty_state_visible() or len(manifests.get_pickup_rows_text()) == 0
