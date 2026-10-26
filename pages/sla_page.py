import time
from typing import Optional, List, Dict
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from config.settings import settings


class SlaPage(BasePage):
    """
    Page Object Model for the SLA (Service Level Agreement) module.
    Covers:
    - SLA Rules: Order, FDR, Ticket (multi-step creation wizards, list, search, delete)
    - SLA Tracking: Order, FDR, Ticket (table inspection, status badges, rematching rules)
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = f"{settings.BASE_URL}/tenant/ttenant/admin/slas"

        # Navigation locators (scoped via accessible roles to avoid clashes)
        self.rules_tab: Locator = page.get_by_role("tab", name="Rules")
        self.tracking_tab: Locator = page.get_by_role("tab", name="Tracking")
        self.order_subtab: Locator = page.get_by_role("button", name="Order", exact=True)
        self.fdr_subtab: Locator = page.get_by_role("button", name="FDR", exact=True)
        self.ticket_subtab: Locator = page.get_by_role("button", name="Ticket", exact=True)

        # Table & View locators
        self.table: Locator = page.locator(".ant-table")
        self.table_headers: Locator = page.locator(".ant-table-thead th")
        self.table_rows: Locator = page.locator(".ant-table-tbody tr.ant-table-row")
        self.empty_table: Locator = page.locator(".ant-empty")
        self.search_input: Locator = page.locator("input[placeholder='Search']").first

        # Wizard action buttons
        self.create_btn: Locator = page.locator("button:has-text('Create'), button:has-text('Add Rule')").first
        self.wizard_next_btn: Locator = page.locator("button:has-text('Next')").first
        self.wizard_back_btn: Locator = page.locator("button:has-text('Back')").first
        self.wizard_cancel_btn: Locator = page.locator("button:has-text('Cancel')").first
        self.wizard_save_btn: Locator = page.locator("button:has-text('Save'), button:has-text('Create')").last

        # Wizard fields - Order SLA
        self.order_name_input: Locator = page.locator("input#name, input[name='name']").first
        self.order_service_select: Locator = page.locator(".ant-form-item:has-text('Service') .ant-select").first
        self.order_merchant_select: Locator = page.locator(".ant-form-item:has-text('Merchant') .ant-select").first
        self.order_from_type_select: Locator = page.locator(".ant-form-item:has-text('From Location Type') .ant-select").first
        self.order_from_loc_select: Locator = page.locator(".ant-form-item:has-text('From Location')").filter(has_not_text='Type').locator(".ant-select").first
        self.order_to_type_select: Locator = page.locator(".ant-form-item:has-text('To Location Type') .ant-select").first
        self.order_to_loc_select: Locator = page.locator(".ant-form-item:has-text('To Location')").filter(has_not_text='Type').locator(".ant-select").first
        self.order_min_days_input: Locator = page.locator("#minTransitDaysDays").first
        self.order_min_hours_input: Locator = page.locator("#minTransitDaysHours").first
        self.order_max_days_input: Locator = page.locator("#maxTransitDaysDays").first
        self.order_max_hours_input: Locator = page.locator("#maxTransitDaysHours").first
        self.order_priority_input: Locator = page.locator("#priority").first

        # Wizard fields - FDR SLA
        self.fdr_role_select: Locator = page.locator(".ant-form-item:has-text('Role') .ant-select").first
        self.fdr_audit_reason_select: Locator = page.locator(".ant-form-item:has-text('Audit Reason') .ant-select").first
        self.fdr_max_response_time_input: Locator = page.locator("input#maxResponseTime, input[placeholder='00:00']").first
        self.fdr_is_active_switch: Locator = page.locator("button#isActive, .ant-switch#isActive").first

        # Wizard fields - Ticket SLA
        self.ticket_reason_select: Locator = page.locator(".ant-form-item:has-text('Reason') .ant-select").first
        self.ticket_max_response_time_input: Locator = page.locator("input#maxResponseTime, input[placeholder='00:00']").first
        self.ticket_max_closure_time_input: Locator = page.locator("input#maxClosureTime").first
        self.ticket_is_active_switch: Locator = page.locator("button#isActive, .ant-switch#isActive").first

        # Order Tracking locators
        self.rematch_rules_btn: Locator = page.locator("button:has-text('Rematch Rules'), button:has-text('Rematch')").first

        # Modal / Confirm locators
        self.modal: Locator = page.locator(".ant-modal:not([style*='display: none'])").first
        self.modal_confirm_btn: Locator = page.locator(".ant-modal button:has-text('Yes'), .ant-modal button.ant-btn-primary, .ant-modal button:has-text('OK'), .ant-modal button:has-text('Confirm')").last
        self.modal_cancel_btn: Locator = page.locator(".ant-modal button:has-text('No'), .ant-modal button:has-text('Cancel')").first

        # Validation errors
        self.form_errors: Locator = page.locator(".ant-form-item-explain-error")

    # =========================================================================
    # Navigation Methods
    # =========================================================================
    def open(self) -> "SlaPage":
        """Navigate to default SLA rules page."""
        return self.open_rules("order")

    def wait_for_table_loaded(self, timeout: int = 10000) -> None:
        """Wait for table headers and data rows to be rendered."""
        try:
            self.table_headers.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            pass
        try:
            self.table_rows.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            pass

    def open_rules(self, section: str = "order") -> "SlaPage":
        """
        Navigate to SLA Rules tab and specific section ('order', 'fdr', 'ticket').
        """
        valid_sections = ["order", "fdr", "ticket"]
        if section not in valid_sections:
            raise ValueError(f"Invalid section: {section}. Must be one of {valid_sections}")
        self.navigate(f"{self.base_url}/rules/{section}")
        self.wait_for_table_loaded()
        return self

    def open_tracking(self, section: str = "order") -> "SlaPage":
        """
        Navigate to SLA Tracking tab and specific section ('order', 'fdr', 'ticket').
        """
        valid_sections = ["order", "fdr", "ticket"]
        if section not in valid_sections:
            raise ValueError(f"Invalid section: {section}. Must be one of {valid_sections}")
        self.navigate(f"{self.base_url}/tracking/{section}")
        self.wait_for_table_loaded()
        return self

    def switch_via_ui(self, tab: str = "Rules", section: str = "Order") -> "SlaPage":
        """Switch tab and sub-section using the exact UI controls."""
        if tab.lower() == "rules":
            self.rules_tab.click()
        elif tab.lower() == "tracking":
            self.tracking_tab.click()
        self.page.wait_for_timeout(600)

        if section.lower() == "order":
            self.order_subtab.click()
        elif section.lower() == "fdr":
            self.fdr_subtab.click()
        elif section.lower() == "ticket":
            self.ticket_subtab.click()
        self.wait_for_table_loaded()
        return self

    # =========================================================================
    # Table & Inspection Helpers
    # =========================================================================
    def get_table_header_titles(self) -> List[str]:
        """Return list of text for all table headers."""
        self.wait_for_table_loaded()
        headers = self.table_headers.all_text_contents()
        return [h.strip() for h in headers if h.strip()]

    def get_row_count(self, wait_for_rows: bool = True) -> int:
        """Return number of data rows in current table."""
        if wait_for_rows:
            try:
                self.table_rows.first.wait_for(state="visible", timeout=6000)
            except Exception:
                pass
        return self.table_rows.count()

    def get_all_rows_text(self, wait_for_rows: bool = True) -> List[str]:
        """Return text content of each row in the current table."""
        if wait_for_rows:
            try:
                self.table_rows.first.wait_for(state="visible", timeout=6000)
            except Exception:
                pass
        rows = self.table_rows.all_text_contents()
        return [r.strip() for r in rows if r.strip()]

    def search_rule(self, query: str) -> "SlaPage":
        """Search table using search input."""
        if self.search_input.is_visible():
            self.search_input.fill(query)
            self.page.wait_for_timeout(1000)
        return self

    def clear_search(self) -> "SlaPage":
        """Clear search input."""
        if self.search_input.is_visible():
            self.search_input.fill("")
            self.page.wait_for_timeout(1000)
        return self

    def get_validation_errors(self) -> List[str]:
        """Return all active validation error messages in the form."""
        return [err.strip() for err in self.form_errors.all_text_contents() if err.strip()]

    def _select_ant_option(self, container: Locator, option_text: Optional[str] = None) -> None:
        """Click an ant-select container and pick an option from dropdown."""
        container.click()
        self.page.wait_for_timeout(400)
        dropdown = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
        if option_text:
            dropdown.locator(f".ant-select-item-option:has-text('{option_text}')").first.click()
        else:
            dropdown.locator(".ant-select-item-option").first.click()
        self.page.wait_for_timeout(400)

    # =========================================================================
    # Order SLA Rule Creation & Management
    # =========================================================================
    def create_order_rule(
        self,
        name: str,
        service: Optional[str] = None,
        merchant: Optional[str] = None,
        from_type: str = "Country",
        from_loc: Optional[str] = None,
        to_type: str = "Country",
        to_loc: Optional[str] = None,
        min_days: str = "1",
        min_hours: str = "0",
        max_days: str = "3",
        max_hours: str = "0",
        priority: str = "50",
    ) -> "SlaPage":
        """Create a complete Order SLA Rule across the 3-step wizard."""
        self.open_rules("order")
        self.create_btn.click()
        self.page.wait_for_timeout(800)

        # Step 1: Basic Data
        self.order_name_input.fill(name)
        if service:
            self._select_ant_option(self.order_service_select, service)
        if merchant:
            self._select_ant_option(self.order_merchant_select, merchant)
        self.wizard_next_btn.click()
        self.page.wait_for_timeout(800)

        # Step 2: Route
        self._select_ant_option(self.order_from_type_select, from_type)
        self._select_ant_option(self.order_from_loc_select, from_loc)
        self._select_ant_option(self.order_to_type_select, to_type)
        self._select_ant_option(self.order_to_loc_select, to_loc)
        self.wizard_next_btn.click()
        self.page.wait_for_timeout(800)

        # Step 3: Timings & Status
        self.order_min_days_input.fill(min_days)
        self.order_min_hours_input.fill(min_hours)
        self.order_max_days_input.fill(max_days)
        self.order_max_hours_input.fill(max_hours)
        if priority:
            self.order_priority_input.fill(priority)

        self.wizard_save_btn.click()
        self.page.wait_for_timeout(2000)
        self.wait_for_table_loaded()
        return self

    def delete_rule(self, rule_name: str) -> "SlaPage":
        """Delete a rule by name from the table."""
        row = self.page.locator(f"tr:has-text('{rule_name}')").first
        if not row.is_visible():
            self.search_rule(rule_name)
            row = self.page.locator(f"tr:has-text('{rule_name}')").first

        row.locator("button.ant-btn-dangerous").click()
        self.modal.wait_for(state="visible", timeout=5000)
        self.modal_confirm_btn.click()
        self.modal.wait_for(state="hidden", timeout=5000)
        self.page.wait_for_timeout(1000)
        self.wait_for_table_loaded()
        return self

    def cancel_delete_rule(self, rule_name: str) -> "SlaPage":
        """Click delete icon and then cancel (No) in confirmation modal."""
        row = self.page.locator(f"tr:has-text('{rule_name}')").first
        if not row.is_visible():
            row = self.table_rows.first
        row.locator("button.ant-btn-dangerous").click()
        self.modal.wait_for(state="visible", timeout=5000)
        self.modal_cancel_btn.click()
        self.modal.wait_for(state="hidden", timeout=5000)
        self.page.wait_for_timeout(600)
        return self

    # =========================================================================
    # FDR SLA Rule Creation & Management
    # =========================================================================
    def create_fdr_rule(
        self,
        role: str = "CS",
        reason: Optional[str] = None,
        max_response_time: str = "08:00",
        is_active: bool = True,
    ) -> "SlaPage":
        """Create an FDR SLA Rule across the 2-step wizard."""
        self.open_rules("fdr")
        self.create_btn.click()
        self.page.wait_for_timeout(800)

        # Step 1: Role & Reason
        self._select_ant_option(self.fdr_role_select, role)
        if reason:
            self._select_ant_option(self.fdr_audit_reason_select, reason)
        self.wizard_next_btn.click()
        self.page.wait_for_timeout(800)

        # Step 2: Response Time & Status
        if max_response_time:
            self.fdr_max_response_time_input.fill(max_response_time)
        if not is_active and "ant-switch-checked" in (self.fdr_is_active_switch.get_attribute("class") or ""):
            self.fdr_is_active_switch.click()

        self.wizard_save_btn.click()
        self.page.wait_for_timeout(2000)
        self.wait_for_table_loaded()
        return self

    # =========================================================================
    # Ticket SLA Rule Creation & Management
    # =========================================================================
    def create_ticket_rule(
        self,
        reason: Optional[str] = None,
        max_response_time: str = "04:00",
        max_closure_time: Optional[str] = None,
        is_active: bool = True,
    ) -> "SlaPage":
        """Create a Ticket SLA Rule across the 2-step wizard."""
        self.open_rules("ticket")
        self.create_btn.click()
        self.page.wait_for_timeout(800)

        # Step 1: Reason
        self._select_ant_option(self.ticket_reason_select, reason)
        self.wizard_next_btn.click()
        self.page.wait_for_timeout(800)

        # Step 2: Timings & Status
        if max_response_time:
            self.ticket_max_response_time_input.fill(max_response_time)
        if max_closure_time:
            self.ticket_max_closure_time_input.fill(max_closure_time)
        if not is_active and "ant-switch-checked" in (self.ticket_is_active_switch.get_attribute("class") or ""):
            self.ticket_is_active_switch.click()

        self.wizard_save_btn.click()
        self.page.wait_for_timeout(2000)
        self.wait_for_table_loaded()
        return self

    # =========================================================================
    # SLA Tracking Actions
    # =========================================================================
    def trigger_rematch_rules(self) -> bool:
        """
        Click 'Rematch Rules' on Order SLA Tracking and wait for the rematch API call.
        Returns True if successful.
        """
        self.open_tracking("order")
        with self.page.expect_response(lambda r: "sla-rules/rematch" in r.url or "slas/tenant" in r.url, timeout=15000) as resp_info:
            self.rematch_rules_btn.click()
        resp = resp_info.value
        return resp.status in [200, 202]

    def get_tracking_badges(self) -> List[str]:
        """Return list of badge status texts from current tracking table."""
        badges = self.page.locator(".ant-tag, .ant-badge").all_text_contents()
        return [b.strip() for b in badges if b.strip()]
