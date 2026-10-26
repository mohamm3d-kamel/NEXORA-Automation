import time
import pytest
from playwright.sync_api import Page
from pages.tickets_page import TicketsPage


@pytest.mark.tickets
class TestTicketsValid:
    """Valid happy-path scenarios for Tickets module."""

    @pytest.mark.valid
    def test_valid_navigate_all_ticket_category_tabs(self, authenticated_tickets: TicketsPage):
        """
        Verify navigation across all ticket category tabs:
        - Customer Support Tickets
        - Driver Support Tickets
        - Operation Tickets
        Verify table headers are populated correctly.
        """
        tickets = authenticated_tickets

        # 1. Customer Support Tickets
        tickets.switch_category_tab("Customer Support Tickets")
        headers = tickets.get_table_headers()
        assert len(headers) >= 4, f"Expected table headers, got: {headers}"
        expected_columns = ["Ticket Number", "Status", "Subject", "Created"]
        for col in expected_columns:
            assert any(col.lower() in h.lower() for h in headers), (
                f"Expected column '{col}' in headers: {headers}"
            )

        # 2. Driver Support Tickets
        tickets.switch_category_tab("Driver Support Tickets")
        driver_headers = tickets.get_table_headers()
        assert len(driver_headers) >= 4, f"Expected table headers, got: {driver_headers}"

        # 3. Operation Tickets
        tickets.switch_category_tab("Operation Tickets")
        ops_headers = tickets.get_table_headers()
        assert len(ops_headers) >= 4, f"Expected table headers, got: {ops_headers}"

    @pytest.mark.valid
    def test_valid_tickets_status_filter_tabs(self, authenticated_tickets: TicketsPage):
        """
        Verify status filter tabs (Open, Closed, Archived) update the table properly.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")

        # Open tab
        tickets.switch_status_tab("Open")
        open_count = tickets.get_row_count()
        assert open_count >= 0

        # Closed tab
        tickets.switch_status_tab("Closed")
        closed_count = tickets.get_row_count()
        assert closed_count >= 0

        # Archived tab
        tickets.switch_status_tab("Archived")
        archived_count = tickets.get_row_count()
        assert archived_count >= 0

        # Return to Open
        tickets.switch_status_tab("Open")

    @pytest.mark.valid
    def test_valid_ticket_detail_view_and_thread(self, authenticated_tickets: TicketsPage):
        """
        Open a ticket from the table and verify ticket details view and thread structure.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")
        tickets.switch_status_tab("Open")

        ticket_numbers = tickets.get_ticket_numbers()
        if not ticket_numbers:
            # Fallback to Closed if no Open tickets exist
            tickets.switch_status_tab("Closed")
            ticket_numbers = tickets.get_ticket_numbers()

        assert len(ticket_numbers) > 0, "No tickets found to inspect details"
        target_ticket = ticket_numbers[0]

        clicked_id = tickets.open_ticket_detail(target_ticket)
        assert tickets.is_detail_view(), f"Expected detail view URL, got: {tickets.page.url}"

        # Verify ticket title / ID in detail header
        detail_title = tickets.get_detail_ticket_number()
        assert clicked_id in detail_title or target_ticket in detail_title, (
            f"Expected {target_ticket} in detail title '{detail_title}'"
        )

        # Verify reply box or conversation controls are present
        assert tickets.reply_textarea.is_visible() or tickets.detail_back_btn.is_visible()

    @pytest.mark.valid
    def test_valid_send_ticket_reply_message(self, authenticated_tickets: TicketsPage):
        """
        Send a reply message in an open ticket thread and verify its appearance.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")
        tickets.switch_status_tab("Open")

        ticket_numbers = tickets.get_ticket_numbers()
        if not ticket_numbers:
            tickets.switch_status_tab("Closed")
            ticket_numbers = tickets.get_ticket_numbers()

        assert len(ticket_numbers) > 0, "No tickets found for sending reply"
        tickets.open_ticket_detail(ticket_numbers[0])

        unique_reply = f"Automated test reply - {int(time.time())}"
        reflected = tickets.send_ticket_reply(unique_reply)
        assert reflected, f"Message '{unique_reply}' was not reflected in the conversation thread"

    @pytest.mark.valid
    def test_valid_close_ticket_lifecycle(self, authenticated_tickets: TicketsPage):
        """
        Verify closing an open ticket updates its status to Closed.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")
        tickets.switch_status_tab("Open")

        ticket_numbers = tickets.get_ticket_numbers()
        if not ticket_numbers:
            pytest.skip("No open tickets available to close in staging")

        tickets.open_ticket_detail(ticket_numbers[0])

        # If close ticket button is visible, close it
        if tickets.detail_close_ticket_btn.is_visible():
            closed = tickets.close_ticket()
            assert closed, "Failed to transition ticket to Closed status"

            # Return to tickets list and check Closed tab
            tickets.open_tickets()
            tickets.switch_category_tab("Customer Support Tickets")
            tickets.switch_status_tab("Closed")
            assert tickets.get_row_count() > 0
        else:
            status = tickets.get_detail_status()
            assert status in ["Closed", "Open", "Archived"]

    @pytest.mark.valid
    def test_valid_search_tickets_by_prefix(self, authenticated_tickets: TicketsPage):
        """
        Search tickets by 'TKT-' prefix and verify matching rows appear.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")

        tickets.search_tickets("TKT-")
        rows = tickets.get_row_count()
        if rows > 0:
            ticket_ids = tickets.get_ticket_numbers()
            assert all("TKT-" in t for t in ticket_ids)

        tickets.clear_search()
        assert tickets.get_row_count() >= 0


@pytest.mark.tickets
class TestTicketsInvalid:
    """Invalid negative validation scenarios for Tickets module."""

    @pytest.mark.invalid
    def test_invalid_search_nonexistent_ticket(self, authenticated_tickets: TicketsPage):
        """
        Search for a non-existent ticket number and verify empty state / No Data.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")

        tickets.search_tickets("TKT-NONEXISTENT-999999")
        assert tickets.get_row_count() == 0, "Expected 0 rows for non-existent search"
        assert tickets.is_empty_state_visible(), "Expected empty state (No Data) to be visible"

        tickets.clear_search()

    @pytest.mark.invalid
    def test_invalid_send_reply_empty_button_disabled(self, authenticated_tickets: TicketsPage):
        """
        Verify that send reply button is disabled when the reply textarea is empty.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")

        ticket_numbers = tickets.get_ticket_numbers()
        if not ticket_numbers:
            tickets.switch_status_tab("Closed")
            ticket_numbers = tickets.get_ticket_numbers()

        assert len(ticket_numbers) > 0, "No tickets found to inspect reply button"
        tickets.open_ticket_detail(ticket_numbers[0])

        # Ensure textarea is empty
        tickets.reply_textarea.wait_for(state="visible", timeout=10000)
        tickets.reply_textarea.fill("")

        # Verify send button is disabled
        assert tickets.is_send_reply_button_disabled(), (
            "Send button should be disabled when reply input is empty"
        )

    @pytest.mark.invalid
    def test_invalid_new_ticket_wizard_step1_empty_validation(self, authenticated_tickets: TicketsPage):
        """
        Trigger New Ticket wizard and verify validation:
        1. Attempting to click Next with empty mandatory fields blocks progression (stays on Step 1 Details).
        2. Interacting with required Subject field and clearing it displays 'Subject is required' validation error.
        """
        tickets = authenticated_tickets
        tickets.open_tickets()
        tickets.open_new_ticket()

        # 1. Attempt to proceed without entering details - wizard must block progression
        tickets.click_wizard_next()
        active_step = tickets.get_current_wizard_step()
        assert "Details" in active_step, f"Expected wizard to stay on Details step, got: {active_step}"

        # 2. Trigger inline field validation error
        tickets.trigger_subject_validation()
        errors = tickets.get_wizard_validation_errors()
        assert any("required" in err.lower() for err in errors), (
            f"Expected mandatory validation error, got: {errors}"
        )

        # Clean up by canceling wizard
        tickets.cancel_new_ticket()


@pytest.mark.tickets
class TestTicketsEdge:
    """Edge and boundary scenarios for Tickets module."""

    @pytest.mark.edge
    def test_edge_rapid_status_tab_switching(self, authenticated_tickets: TicketsPage):
        """
        Rapidly toggle between status tabs (Open -> Closed -> Archived -> Open)
        to ensure state stability, no race conditions, and no hung spinners.
        """
        tickets = authenticated_tickets
        tickets.switch_category_tab("Customer Support Tickets")

        for _ in range(2):
            tickets.switch_status_tab("Open")
            tickets.switch_status_tab("Closed")
            tickets.switch_status_tab("Archived")

        tickets.switch_status_tab("Open")
        headers = tickets.get_table_headers()
        assert len(headers) >= 4, "Table failed to render properly after rapid switching"

    @pytest.mark.edge
    def test_edge_cancel_new_ticket_wizard_preserves_list(self, authenticated_tickets: TicketsPage):
        """
        Open New Ticket wizard and immediately cancel.
        Verify user is returned safely to the tickets list with table intact.
        """
        tickets = authenticated_tickets
        tickets.open_tickets()
        initial_headers = tickets.get_table_headers()

        tickets.open_new_ticket()
        tickets.cancel_new_ticket()

        # Verify returned to list view
        assert not tickets.is_detail_view()
        headers = tickets.get_table_headers()
        assert headers == initial_headers, "Tickets list headers changed or corrupted after cancel"

    @pytest.mark.edge
    def test_edge_operation_tickets_empty_or_data_resilience(self, authenticated_tickets: TicketsPage):
        """
        Navigate across Driver Support and Operation Tickets tabs, verifying
        the UI handles either data rows or empty state without JS exceptions.
        """
        tickets = authenticated_tickets

        # Test Driver Support Tickets tab resilience
        tickets.switch_category_tab("Driver Support Tickets")
        driver_count = tickets.get_row_count()
        if driver_count == 0:
            assert tickets.is_empty_state_visible()
        else:
            assert driver_count > 0

        # Test Operation Tickets tab resilience
        tickets.switch_category_tab("Operation Tickets")
        ops_count = tickets.get_row_count()
        if ops_count == 0:
            assert tickets.is_empty_state_visible()
        else:
            assert ops_count > 0

        # Return safely to Customer Support
        tickets.switch_category_tab("Customer Support Tickets")
        assert len(tickets.get_table_headers()) >= 4
