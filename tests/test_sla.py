import time
import pytest
from playwright.sync_api import Page, expect
from pages.sla_page import SlaPage


@pytest.mark.sla
class TestSlaModule:
    """
    Comprehensive test suite for SLA (Service Level Agreement) module:
    - Valid Scenarios: Full 6-view navigation, 3-step Order SLA Rule creation and deletion,
      Order Tracking rule rematching, and UI tab/subtab switching.
    - Invalid Scenarios: Multi-step wizard validation enforcement (Step 1 Name, Step 2 Route,
      Step 3 Hours, FDR Role, Ticket Reason).
    - Edge Scenarios: Search filtering, non-existent search empty state, wizard cancellation,
      and delete modal cancellation.
    """

    # =========================================================================
    # Valid Scenarios
    # =========================================================================

    @pytest.mark.valid
    def test_valid_navigate_all_sla_rules_views(self, authenticated_sla: SlaPage):
        """
        [Valid] Verify that all 3 SLA Rules sections (Order, FDR, Ticket)
        load properly with their expected table header schemas.
        """
        sla = authenticated_sla

        # 1. Order SLA Rules
        sla.open_rules("order")
        order_headers = sla.get_table_header_titles()
        assert "Rule Name" in order_headers, f"Expected 'Rule Name' in Order SLA Rules headers, got: {order_headers}"
        assert "Route" in order_headers, f"Expected 'Route' in Order SLA Rules headers, got: {order_headers}"
        assert "Status" in order_headers, f"Expected 'Status' in Order SLA Rules headers, got: {order_headers}"

        # 2. FDR SLA Rules
        sla.open_rules("fdr")
        fdr_headers = sla.get_table_header_titles()
        assert "Audit Reason" in fdr_headers, f"Expected 'Audit Reason' in FDR SLA Rules headers, got: {fdr_headers}"
        assert "Role" in fdr_headers, f"Expected 'Role' in FDR SLA Rules headers, got: {fdr_headers}"
        assert "Max Response Time (hh:mm)" in fdr_headers, f"Expected 'Max Response Time (hh:mm)' in FDR SLA Rules headers, got: {fdr_headers}"

        # 3. Ticket SLA Rules
        sla.open_rules("ticket")
        ticket_headers = sla.get_table_header_titles()
        assert "User Role" in ticket_headers, f"Expected 'User Role' in Ticket SLA Rules headers, got: {ticket_headers}"
        assert "Reason" in ticket_headers, f"Expected 'Reason' in Ticket SLA Rules headers, got: {ticket_headers}"
        assert "Max Response Time" in ticket_headers, f"Expected 'Max Response Time' in Ticket SLA Rules headers, got: {ticket_headers}"

    @pytest.mark.valid
    def test_valid_navigate_all_sla_tracking_views(self, authenticated_sla: SlaPage):
        """
        [Valid] Verify that all 3 SLA Tracking sections (Order, FDR, Ticket)
        load properly with their expected tracking table columns.
        """
        sla = authenticated_sla

        # 1. Order SLA Tracking
        sla.open_tracking("order")
        order_tracking_headers = sla.get_table_header_titles()
        assert "Shipment Number" in order_tracking_headers, f"Expected 'Shipment Number' in Order Tracking headers, got: {order_tracking_headers}"
        assert "Route" in order_tracking_headers, f"Expected 'Route' in Order Tracking headers, got: {order_tracking_headers}"
        assert "Status" in order_tracking_headers, f"Expected 'Status' in Order Tracking headers, got: {order_tracking_headers}"
        assert sla.rematch_rules_btn.is_visible(), "Expected 'Rematch Rules' button to be visible on Order SLA Tracking"

        # 2. FDR SLA Tracking
        sla.open_tracking("fdr")
        fdr_tracking_headers = sla.get_table_header_titles()
        assert "Request Number" in fdr_tracking_headers, f"Expected 'Request Number' in FDR Tracking headers, got: {fdr_tracking_headers}"
        assert "Role" in fdr_tracking_headers, f"Expected 'Role' in FDR Tracking headers, got: {fdr_tracking_headers}"
        assert "Expected Time" in fdr_tracking_headers, f"Expected 'Expected Time' in FDR Tracking headers, got: {fdr_tracking_headers}"

        # 3. Ticket SLA Tracking
        sla.open_tracking("ticket")
        ticket_tracking_headers = sla.get_table_header_titles()
        assert "Ticket Number" in ticket_tracking_headers, f"Expected 'Ticket Number' in Ticket Tracking headers, got: {ticket_tracking_headers}"
        assert "Category" in ticket_tracking_headers, f"Expected 'Category' in Ticket Tracking headers, got: {ticket_tracking_headers}"
        assert "First Response Due" in ticket_tracking_headers, f"Expected 'First Response Due' in Ticket Tracking headers, got: {ticket_tracking_headers}"

    @pytest.mark.valid
    def test_valid_sla_tab_switching_via_ui(self, authenticated_sla: SlaPage):
        """
        [Valid] Verify switching between Rules and Tracking tabs and between
        Order, FDR, and Ticket subtabs strictly through UI buttons.
        """
        sla = authenticated_sla
        sla.open_rules("order")

        # Switch to Tracking -> FDR via UI
        sla.switch_via_ui(tab="Tracking", section="FDR")
        assert "slas/tracking/fdr" in sla.current_url, f"Expected URL to contain 'slas/tracking/fdr', got: {sla.current_url}"

        # Switch to Tracking -> Ticket via UI
        sla.switch_via_ui(tab="Tracking", section="Ticket")
        assert "slas/tracking/ticket" in sla.current_url, f"Expected URL to contain 'slas/tracking/ticket', got: {sla.current_url}"

        # Switch to Rules -> Order via UI
        sla.switch_via_ui(tab="Rules", section="Order")
        assert "slas/rules/order" in sla.current_url, f"Expected URL to contain 'slas/rules/order', got: {sla.current_url}"

    @pytest.mark.valid
    def test_valid_create_order_sla_rule(self, authenticated_sla: SlaPage):
        """
        [Valid] Create a complete Order SLA Rule across all 3 wizard steps,
        verify it appears in the table with ACTIVE status, and clean it up.
        """
        sla = authenticated_sla
        rule_name = f"Auto E2E SLA {int(time.time())}"

        sla.create_order_rule(
            name=rule_name,
            from_type="Country",
            from_loc="Saudi Arabia",
            to_type="Country",
            to_loc="Saudi Arabia",
            min_days="1",
            min_hours="0",
            max_days="3",
            max_hours="0",
            priority="50",
        )

        # Verify rule is present in the table
        sla.open_rules("order")
        sla.search_rule(rule_name)
        row = sla.page.locator(f"tr:has-text('{rule_name}')").first
        expect(row).to_be_visible(timeout=10000)
        assert "ACTIVE" in row.inner_text(), f"Expected ACTIVE status badge in row, got: {row.inner_text()}"

        # Cleanup: delete the created rule
        sla.delete_rule(rule_name)
        sla.clear_search()
        deleted_row = sla.page.locator(f"tr:has-text('{rule_name}')")
        assert deleted_row.count() == 0, f"Expected rule '{rule_name}' to be deleted from table"

    @pytest.mark.valid
    def test_valid_order_sla_tracking_rematch(self, authenticated_sla: SlaPage):
        """
        [Valid] Trigger 'Rematch Rules' on Order SLA Tracking and verify
        that the system successfully dispatches rematch API call and refreshes tracking data.
        """
        sla = authenticated_sla
        success = sla.trigger_rematch_rules()
        assert success, "Expected Rematch Rules API call to return 200 or 202 status"

    # =========================================================================
    # Invalid Scenarios
    # =========================================================================

    @pytest.mark.invalid
    def test_invalid_order_sla_empty_step1_validation(self, authenticated_sla: SlaPage):
        """
        [Invalid] Attempt to advance to Step 2 without entering a Rule Name.
        Verify that inline validation error 'This field is required' is displayed
        and the wizard remains on Step 1.
        """
        sla = authenticated_sla
        sla.open_rules("order")
        sla.create_btn.click()
        sla.page.wait_for_timeout(800)

        # Ensure name input is empty and click Next
        sla.order_name_input.fill("")
        sla.wizard_next_btn.click()
        sla.page.wait_for_timeout(500)

        errors = sla.get_validation_errors()
        assert any("This field is required" in err for err in errors), (
            f"Expected 'This field is required' error on empty rule name, got: {errors}"
        )
        assert sla.wizard_back_btn.is_hidden(), "Back button should not be visible on Step 1"

        # Cancel wizard
        sla.wizard_cancel_btn.click()

    @pytest.mark.invalid
    def test_invalid_order_sla_empty_step2_route_validation(self, authenticated_sla: SlaPage):
        """
        [Invalid] Fill Step 1 but attempt to advance past Step 2 without selecting
        required Route details (From/To Location Types & Locations).
        Verify that 4 inline validation errors appear on Step 2.
        """
        sla = authenticated_sla
        sla.open_rules("order")
        sla.create_btn.click()
        sla.page.wait_for_timeout(800)

        # Step 1: fill name and advance
        sla.order_name_input.fill("Invalid Step 2 Test")
        sla.wizard_next_btn.click()
        sla.page.wait_for_timeout(800)

        # Step 2: attempt to advance without selecting route
        sla.wizard_next_btn.click()
        sla.page.wait_for_timeout(500)

        errors = sla.get_validation_errors()
        required_errors = [e for e in errors if "This field is required" in e]
        assert len(required_errors) >= 4, (
            f"Expected at least 4 required field errors on Step 2 route, got {len(required_errors)}: {errors}"
        )

        # Cancel wizard
        sla.wizard_cancel_btn.click()

    @pytest.mark.invalid
    def test_invalid_order_sla_empty_step3_hours_validation(self, authenticated_sla: SlaPage):
        """
        [Invalid] Complete Step 1 & 2, then on Step 3 clear required Hours fields.
        Attempt to Save and assert that validation errors 'This field is required' appear.
        """
        sla = authenticated_sla
        sla.open_rules("order")
        sla.create_btn.click()
        sla.page.wait_for_timeout(800)

        # Step 1
        sla.order_name_input.fill("Invalid Step 3 Test")
        sla.wizard_next_btn.click()
        sla.page.wait_for_timeout(800)

        # Step 2: fill valid route
        sla._select_ant_option(sla.order_from_type_select, "Country")
        sla._select_ant_option(sla.order_from_loc_select, "Saudi Arabia")
        sla._select_ant_option(sla.order_to_type_select, "Country")
        sla._select_ant_option(sla.order_to_loc_select, "Saudi Arabia")
        sla.wizard_next_btn.click()
        sla.page.wait_for_timeout(800)

        # Step 3: leave hours empty and click Save
        sla.order_min_days_input.fill("1")
        sla.order_min_hours_input.fill("")
        sla.order_max_days_input.fill("2")
        sla.order_max_hours_input.fill("")
        sla.wizard_save_btn.click()
        sla.page.wait_for_timeout(500)

        errors = sla.get_validation_errors()
        assert any("This field is required" in err for err in errors), (
            f"Expected 'This field is required' error on empty Hours, got: {errors}"
        )

        # Cancel wizard
        sla.wizard_cancel_btn.click()

    @pytest.mark.invalid
    def test_invalid_fdr_sla_empty_role_validation(self, authenticated_sla: SlaPage):
        """
        [Invalid] Attempt to advance FDR SLA Rule wizard without selecting a Role.
        Verify that inline validation error 'This field is required' appears.
        """
        sla = authenticated_sla
        sla.open_rules("fdr")
        sla.create_btn.click()
        sla.page.wait_for_timeout(800)

        # Click Next without selecting Role
        sla.wizard_next_btn.click()
        sla.page.wait_for_timeout(500)

        errors = sla.get_validation_errors()
        assert any("This field is required" in err for err in errors), (
            f"Expected 'This field is required' error for FDR Role, got: {errors}"
        )

        # Cancel wizard
        sla.wizard_cancel_btn.click()

    @pytest.mark.invalid
    def test_invalid_ticket_sla_empty_reason_validation(self, authenticated_sla: SlaPage):
        """
        [Invalid] Attempt to advance Ticket SLA Rule wizard without selecting Reason.
        Verify that inline validation error 'Reason is required' appears.
        """
        sla = authenticated_sla
        sla.open_rules("ticket")
        sla.create_btn.click()
        sla.page.wait_for_timeout(800)

        # Click Next without selecting Reason
        sla.wizard_next_btn.click()
        sla.page.wait_for_timeout(500)

        errors = sla.get_validation_errors()
        assert any("Reason is required" in err for err in errors), (
            f"Expected 'Reason is required' error for Ticket Reason, got: {errors}"
        )

        # Cancel wizard
        sla.wizard_cancel_btn.click()

    # =========================================================================
    # Edge Scenarios
    # =========================================================================

    @pytest.mark.edge
    def test_edge_order_sla_search_filtering(self, authenticated_sla: SlaPage):
        """
        [Edge] Verify search filter responsiveness:
        1. Searching for an existing baseline rule filters table to matching rows.
        2. Searching for a non-existent query yields zero rows / empty state.
        3. Clearing the search restores the full rule listing.
        """
        sla = authenticated_sla
        sla.open_rules("order")
        initial_count = sla.get_row_count()
        assert initial_count >= 1, "Expected at least 1 baseline rule in Order SLA Rules table"

        # 1. Search existing
        sla.search_rule("general SLA")
        filtered_count = sla.get_row_count()
        assert 0 < filtered_count <= initial_count, (
            f"Expected filtered count to be between 1 and {initial_count}, got: {filtered_count}"
        )
        assert any("general SLA" in r for r in sla.get_all_rows_text()), "Expected search result to match 'general SLA'"

        # 2. Search non-existent
        sla.search_rule("NON_EXISTENT_SLA_XYZ_99999")
        empty_count = sla.get_row_count(wait_for_rows=False)
        assert empty_count == 0, f"Expected 0 rows for non-existent search, got: {empty_count}"

        # 3. Clear search restores table
        sla.clear_search()
        restored_count = sla.get_row_count()
        assert restored_count == initial_count, (
            f"Expected restored count {initial_count}, got: {restored_count}"
        )

    @pytest.mark.edge
    def test_edge_order_sla_cancel_wizard_preserves_state(self, authenticated_sla: SlaPage):
        """
        [Edge] Open Order SLA wizard, enter preliminary details on Step 1,
        and click Cancel. Verify the wizard unmounts cleanly and table row count is unchanged.
        """
        sla = authenticated_sla
        sla.open_rules("order")
        initial_count = sla.get_row_count()

        sla.create_btn.click()
        sla.page.wait_for_timeout(800)
        sla.order_name_input.fill("Canceled Rule Test")
        sla.wizard_cancel_btn.click()
        sla.page.wait_for_timeout(800)

        # Verify wizard closed and row count unchanged
        assert sla.order_name_input.is_hidden(), "Expected wizard to be closed after Cancel"
        current_count = sla.get_row_count()
        assert current_count == initial_count, (
            f"Expected count to remain {initial_count}, got: {current_count}"
        )

    @pytest.mark.edge
    def test_edge_order_sla_cancel_delete_modal(self, authenticated_sla: SlaPage):
        """
        [Edge] Click delete icon on an existing rule, but click Cancel (No) in confirmation modal.
        Verify that the rule is NOT deleted and remains in the table.
        """
        sla = authenticated_sla
        sla.open_rules("order")
        initial_count = sla.get_row_count()
        assert initial_count >= 1, "Expected at least 1 rule in table"

        # Attempt delete and cancel (click 'No')
        sla.cancel_delete_rule("general SLA Rule")

        # Verify row count is unchanged
        count_after = sla.get_row_count()
        assert count_after == initial_count, (
            f"Expected row count to remain {initial_count} after delete cancel, got: {count_after}"
        )
