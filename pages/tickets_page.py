import re
import time
from typing import List, Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from config.settings import settings


class TicketsPage(BasePage):
    """
    Page Object Model for the Tickets Management module:
    - Ticket Category Tabs (Customer Support, Driver Support, Operation Tickets)
    - Ticket Status Tabs (Open, Closed, Archived)
    - Ticket List & Search Filtering
    - Ticket Detail View & Conversation Thread (/admin/tickets/:id)
    - Reply sending & message reflection
    - Ticket Status Transitions (Close Ticket)
    - New Ticket Creation Wizard & Validation
    """

    def __init__(self, page: Page):
        super().__init__(page)

        # Base URLs
        self.tickets_url = f"{settings.BASE_URL}/tenant/ttenant/admin/tickets"

        # Category Tabs
        self.tab_customer_support: Locator = page.locator(
            "button:has-text('Customer Support Tickets'), [role='tab']:has-text('Customer Support Tickets')"
        ).first
        self.tab_driver_support: Locator = page.locator(
            "button:has-text('Driver Support Tickets'), [role='tab']:has-text('Driver Support Tickets')"
        ).first
        self.tab_operation_tickets: Locator = page.locator(
            "button:has-text('Operation Tickets'), [role='tab']:has-text('Operation Tickets')"
        ).first

        # Status Tabs
        self.tab_status_open: Locator = page.locator(
            "button:has-text('Open'), [role='tab']:has-text('Open')"
        ).first
        self.tab_status_closed: Locator = page.locator(
            "button:has-text('Closed'), [role='tab']:has-text('Closed')"
        ).first
        self.tab_status_archived: Locator = page.locator(
            "button:has-text('Archived'), [role='tab']:has-text('Archived')"
        ).first

        # Tables & Lists
        self.table_headers: Locator = page.locator("th")
        self.table_rows: Locator = page.locator(".ant-table-tbody tr")
        self.empty_state: Locator = page.locator(".ant-empty, .ant-table-placeholder")

        # Search Input
        self.search_input: Locator = page.locator("input[placeholder='Search']").first

        # Ticket Links (buttons with TKT- prefix or links)
        self.ticket_links: Locator = page.locator(
            "button:has-text('TKT-'), a:has-text('TKT-'), a[href*='/admin/tickets/'], [class*='ant-btn-link']:has-text('TKT-')"
        )

        # Ticket Detail View Elements
        self.detail_back_btn: Locator = page.locator("button:has-text('Back')").first
        self.detail_close_ticket_btn: Locator = page.locator("button:has-text('Close Ticket')").first
        self.detail_title: Locator = page.locator(
            "text=/TKT-[A-Z0-9]+/, h1, h2, h3, h4, h5, .ant-page-header-heading-title, [class*='title']"
        ).first
        self.detail_status_badge: Locator = page.locator(
            ".ant-badge, .ant-tag, [class*='status'], [class*='badge']"
        )
        self.reply_textarea: Locator = page.locator(
            "textarea[placeholder*='reply'], input[placeholder*='message'], textarea[placeholder*='message']"
        ).first
        self.reply_send_btn: Locator = page.locator("button:has(.anticon-send), button:has-text('Send')").first
        self.conversation_messages: Locator = page.locator(
            "[class*='message'], [class*='chat'], [class*='bubble'], [class*='comment'], .ant-comment-content-detail"
        )

        # New Ticket Wizard Elements
        self.new_ticket_btn: Locator = page.locator("button:has-text('New Ticket')").first
        self.wizard_next_btn: Locator = page.locator("button:has-text('Next')").first
        self.wizard_cancel_btn: Locator = page.locator("button:has-text('Cancel')").first
        self.wizard_active_step: Locator = page.locator(".ant-steps-item-active, .ant-steps-item-process").first
        self.validation_errors: Locator = page.locator(
            ".ant-form-item-explain-error, .ant-form-item-explain, [role='alert']"
        )

    # =========================================================================
    # Navigation & Initial Loading
    # =========================================================================

    def open_tickets(self) -> None:
        """Navigates to the Tickets list page and waits for content stabilization."""
        self.page.goto(self.tickets_url, wait_until="domcontentloaded")
        self.apply_zoom()
        self.wait_for_spinner()
        self.page.wait_for_timeout(1000)

    def wait_for_spinner(self, timeout_ms: int = 10000) -> None:
        """Waits for loading indicators to detach."""
        try:
            self.page.locator(".ant-spin, .ant-spin-spinning").first.wait_for(
                state="hidden", timeout=timeout_ms
            )
        except Exception:
            pass

    # =========================================================================
    # Category and Status Tab Switching
    # =========================================================================

    def switch_category_tab(self, tab_name: str) -> None:
        """
        Switches ticket category tab.
        tab_name: 'Customer Support Tickets', 'Driver Support Tickets', or 'Operation Tickets'
        """
        target = self.page.locator(f"button:has-text('{tab_name}'), [role='tab']:has-text('{tab_name}')").first
        target.wait_for(state="visible", timeout=10000)
        target.click()
        self.wait_for_spinner()
        self.page.wait_for_timeout(800)

    def switch_status_tab(self, status: str) -> None:
        """
        Switches status filter tab.
        status: 'Open', 'Closed', or 'Archived'
        """
        target = self.page.locator(f"button:has-text('{status}'), [role='tab']:has-text('{status}')").first
        target.wait_for(state="visible", timeout=10000)
        target.click()
        self.wait_for_spinner()
        self.page.wait_for_timeout(800)

    # =========================================================================
    # Table Inspections & Empty State
    # =========================================================================

    def get_table_headers(self) -> List[str]:
        """Returns non-empty header column names."""
        self.table_headers.first.wait_for(state="visible", timeout=10000)
        texts = self.table_headers.all_inner_texts()
        return [t.strip() for t in texts if t.strip()]

    def is_empty_state_visible(self) -> bool:
        """Returns True if the Ant Design empty state or table placeholder is visible."""
        try:
            return (
                self.empty_state.first.is_visible(timeout=1500)
                or self.page.locator("text='No Data'").first.is_visible(timeout=1500)
            )
        except Exception:
            return False

    def get_row_count(self) -> int:
        """Returns the number of genuine data rows in the tickets table."""
        self.wait_for_spinner()
        if self.is_empty_state_visible():
            return 0
        all_rows = self.table_rows.all()
        valid_rows = 0
        for r in all_rows:
            class_attr = r.get_attribute("class") or ""
            text = r.inner_text().strip()
            if "ant-table-placeholder" in class_attr or "No Data" in text:
                continue
            if text:
                valid_rows += 1
        return valid_rows

    def get_ticket_numbers(self) -> List[str]:
        """Returns list of visible ticket IDs (e.g. TKT-F19E721BE1)."""
        self.wait_for_spinner()
        if self.is_empty_state_visible():
            return []
        links = self.ticket_links.all()
        numbers = []
        for l in links:
            txt = l.inner_text().strip()
            if "TKT-" in txt:
                # Extract clean TKT-XXXXXXXXXX code
                m = re.search(r"TKT-[A-Z0-9]+", txt)
                ticket_code = m.group(0) if m else txt
                if ticket_code not in numbers:
                    numbers.append(ticket_code)
        return numbers

    # =========================================================================
    # Search Functionality
    # =========================================================================

    def search_tickets(self, keyword: str) -> None:
        """Types search term into search input and triggers search."""
        self.search_input.wait_for(state="visible", timeout=10000)
        self.search_input.fill("")
        self.search_input.fill(keyword)
        self.search_input.press("Enter")
        self.wait_for_spinner()
        self.page.wait_for_timeout(1000)

    def clear_search(self) -> None:
        """Clears search input and refreshes table."""
        self.search_input.wait_for(state="visible", timeout=10000)
        self.search_input.fill("")
        self.search_input.press("Enter")
        self.wait_for_spinner()
        self.page.wait_for_timeout(1000)

    # =========================================================================
    # Ticket Details & Conversation
    # =========================================================================

    def open_ticket_detail(self, ticket_number: Optional[str] = None) -> Optional[str]:
        """
        Navigates to ticket details view by clicking a ticket link.
        If ticket_number is None, clicks the first available ticket link.
        Returns the ticket ID clicked.
        """
        self.wait_for_spinner()
        if ticket_number:
            link = self.page.locator(f"button:has-text('{ticket_number}'), a:has-text('{ticket_number}')").first
        else:
            link = self.ticket_links.first

        link.wait_for(state="visible", timeout=10000)
        clicked_text = link.inner_text().strip()
        m = re.search(r"TKT-[A-Z0-9]+", clicked_text)
        clicked_id = m.group(0) if m else clicked_text
        link.click()

        # Wait for navigation to detail view
        self.page.wait_for_url(re.compile(r".*/tickets/.*"), timeout=15000)
        self.wait_for_spinner()
        self.apply_zoom()
        self.page.wait_for_timeout(1000)
        return clicked_id

    def is_detail_view(self) -> bool:
        """Checks if current page is ticket detail view."""
        return "/tickets/" in self.page.url and not self.page.url.endswith("/tickets")

    def get_detail_ticket_number(self) -> str:
        """Returns ticket ID or title displayed in the detail view."""
        self.wait_for_spinner()
        tkt_match = self.page.locator("text=/TKT-[A-Z0-9]+/").first
        if tkt_match.is_visible(timeout=3000):
            return tkt_match.inner_text().strip()
        self.detail_title.wait_for(state="visible", timeout=10000)
        return self.detail_title.inner_text().strip()

    def get_detail_status(self) -> str:
        """Returns the current status text shown on detail page."""
        self.wait_for_spinner()
        # Find badges or tags
        badges = self.detail_status_badge.all()
        for b in badges:
            txt = b.inner_text().strip()
            if txt in ["Open", "Closed", "Archived", "Pending", "In Progress"]:
                return txt
        # Fallback to page text search
        for s in ["Open", "Closed", "Archived"]:
            if self.page.locator(f".ant-tag:has-text('{s}'), .ant-badge:has-text('{s}')").first.is_visible():
                return s
        return ""

    def send_ticket_reply(self, message_text: str) -> bool:
        """
        Fills reply input, sends message, and verifies appearance in conversation thread.
        Returns True if message is reflected.
        """
        self.reply_textarea.wait_for(state="visible", timeout=10000)
        self.reply_textarea.scroll_into_view_if_needed()
        self.reply_textarea.fill(message_text)

        # Ensure send button is enabled
        self.reply_send_btn.wait_for(state="visible", timeout=5000)
        self.page.wait_for_timeout(300)
        self.reply_send_btn.click()

        self.wait_for_spinner()
        self.page.wait_for_timeout(1500)

        # Verify message text appears in the thread
        msg_locator = self.page.locator(f"text='{message_text}'").first
        try:
            msg_locator.wait_for(state="visible", timeout=10000)
            return True
        except Exception:
            return False

    def is_send_reply_button_disabled(self) -> bool:
        """Checks if the send reply button is disabled when input is empty."""
        self.reply_send_btn.wait_for(state="visible", timeout=10000)
        is_disabled = self.reply_send_btn.is_disabled()
        classes = self.reply_send_btn.get_attribute("class") or ""
        return is_disabled or "disabled" in classes or "ant-btn-disabled" in classes

    def close_ticket(self) -> bool:
        """
        Clicks Close Ticket button and verifies status update to Closed.
        Returns True if status badge reflects Closed.
        """
        self.detail_close_ticket_btn.wait_for(state="visible", timeout=10000)
        self.detail_close_ticket_btn.click()

        # Handle any possible Ant Design modal confirmation
        confirm_btn = self.page.locator(".ant-modal button:has-text('Yes'), .ant-modal button:has-text('OK'), .ant-modal button:has-text('Confirm')").first
        try:
            if confirm_btn.is_visible(timeout=1500):
                confirm_btn.click()
        except Exception:
            pass

        self.wait_for_spinner()
        self.page.wait_for_timeout(1500)

        # Wait for status badge or text to show 'Closed'
        try:
            closed_badge = self.page.locator(".ant-tag:has-text('Closed'), .ant-badge:has-text('Closed')").first
            closed_badge.wait_for(state="visible", timeout=10000)
            return True
        except Exception:
            return "Closed" in self.get_detail_status()

    # =========================================================================
    # New Ticket Wizard Actions
    # =========================================================================

    def open_new_ticket(self) -> None:
        """Clicks New Ticket button to open creation wizard."""
        self.new_ticket_btn.wait_for(state="visible", timeout=10000)
        self.new_ticket_btn.click()
        self.wait_for_spinner()
        self.wizard_cancel_btn.wait_for(state="visible", timeout=10000)

    def cancel_new_ticket(self) -> None:
        """Cancels ticket creation wizard and returns to tickets list."""
        self.wizard_cancel_btn.wait_for(state="visible", timeout=10000)
        self.wizard_cancel_btn.click()
        self.wait_for_spinner()
        self.page.wait_for_timeout(800)

    def click_wizard_next(self) -> None:
        """Clicks Next button on creation wizard step."""
        self.wizard_next_btn.wait_for(state="visible", timeout=10000)
        self.wizard_next_btn.click()
        self.page.wait_for_timeout(500)

    def get_current_wizard_step(self) -> str:
        """Returns the active step text (e.g. '1Details')."""
        try:
            return self.wizard_active_step.inner_text().strip()
        except Exception:
            return ""

    def trigger_subject_validation(self) -> None:
        """Touches and clears the Subject field to trigger inline mandatory validation."""
        subj = self.page.locator(
            "input[placeholder*='Subject'], input#subject, input[name='subject'], .ant-form-item:has-text('Subject') input"
        ).first
        subj.wait_for(state="visible", timeout=5000)
        subj.click()
        subj.fill("temp")
        subj.fill("")
        self.page.keyboard.press("Tab")
        self.page.wait_for_timeout(500)

    def get_wizard_validation_errors(self) -> List[str]:
        """Returns validation error messages displayed on wizard step."""
        try:
            self.validation_errors.first.wait_for(state="visible", timeout=3000)
            texts = self.validation_errors.all_inner_texts()
            return [t.strip() for t in texts if t.strip()]
        except Exception:
            # Fallback to any explanation or error texts
            errs = self.page.locator(".ant-form-item-explain, text*='required'").all()
            return [e.inner_text().strip() for e in errs if e.inner_text().strip()]
