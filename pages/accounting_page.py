import os
from typing import Optional, List, Dict
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from config.settings import settings

class AccountingPage(BasePage):
    """
    Page Object for Accounting module:
    - COD Collection (Pending collection, Partial completed, Completed)
    - Delivery Manifest Closure Verification
    - Cash Transfer (Pending transfer, Pending approval, Approved/Rejected history)
    - Branch / Hub isolation
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self.cod_collection_url = f"{settings.BASE_URL}/tenant/ttenant/admin/payment-profile/accounting/cod-collection"
        self.cash_transfer_url = f"{settings.BASE_URL}/tenant/ttenant/admin/payment-profile/accounting/cash-transfer"
        self.delivery_manifests_url = f"{settings.BASE_URL}/tenant/ttenant/admin/manifests/delivery-manifests"

        # Tab & Table Locators
        self.active_tabpane: Locator = page.locator(".ant-tabs-tabpane-active")
        self.active_table_rows: Locator = page.locator(".ant-tabs-tabpane-active .ant-table-tbody tr")

        # Modal Locators
        self.modal: Locator = page.locator(".ant-modal:not([style*='display: none'])").first
        self.modal_amount_input: Locator = page.locator(".ant-modal input#amount, .ant-modal .ant-input-number-input").first
        self.modal_notes_textarea: Locator = page.locator(".ant-modal textarea").first
        self.modal_file_input: Locator = page.locator(".ant-modal input[type='file']").first
        self.modal_submit_button: Locator = page.locator(".ant-modal button:has-text('Submit'), .ant-modal button:has-text('Save')").last
        self.modal_cancel_button: Locator = page.locator(".ant-modal button:has-text('Cancel')").first
        self.modal_close_button: Locator = page.locator(".ant-modal .ant-modal-close").first
        self.modal_rejection_textarea: Locator = page.locator(".ant-modal textarea#rejectionReason, .ant-modal textarea").first
        self.modal_reject_confirm_button: Locator = page.locator(".ant-modal button:has-text('Reject')").last

        # Cash Transfer controls
        self.submit_cash_transfer_btn: Locator = page.locator("button:has-text('Submit Cash Transfer')").first
        self.hub_listbox: Locator = page.locator("div[role='listbox']")
        self.hub_options: Locator = page.locator("div[role='listbox'] button[role='option']")

    # =========================================================================
    # Navigation Methods
    # =========================================================================
    def open_cod_collection(self) -> "AccountingPage":
        """Navigate to COD Collection page."""
        self.navigate(self.cod_collection_url)
        self.page.wait_for_timeout(2000)
        return self

    def open_cash_transfer(self) -> "AccountingPage":
        """Navigate to Cash Transfer page."""
        self.navigate(self.cash_transfer_url)
        self.page.wait_for_timeout(2000)
        return self

    def open_delivery_manifests(self) -> "AccountingPage":
        """Navigate to Delivery Manifests page."""
        self.navigate(self.delivery_manifests_url)
        self.page.wait_for_timeout(2000)
        return self

    # =========================================================================
    # COD Collection Methods
    # =========================================================================
    def switch_cod_tab(self, tab_label: str) -> "AccountingPage":
        """Switch between Pending collection, Partial completed, or Completed."""
        tab = self.page.locator(f".ant-tabs-tab:has-text('{tab_label}')").first
        tab.wait_for(state="visible", timeout=self.default_timeout)
        tab.click()
        self.page.wait_for_timeout(1500)
        return self

    def find_cod_manifest_row(self, manifest_id: str) -> Locator:
        """Find table row for a delivery manifest under active COD tab."""
        return self.page.locator(f".ant-tabs-tabpane-active tr:has-text('{manifest_id}')").first

    def get_cod_manifest_status(self, manifest_id: str) -> str:
        """Get the Status text for a manifest in Pending collection (e.g. 'Open', 'Ready for collection')."""
        row = self.find_cod_manifest_row(manifest_id)
        if row.is_visible():
            return row.inner_text()
        return ""

    def is_collect_payment_enabled(self, manifest_id: str) -> bool:
        """Check if 'Collect Payment' button is enabled for the specified manifest."""
        row = self.find_cod_manifest_row(manifest_id)
        btn = row.locator("button:has-text('Collect Payment')").first
        if not btn.is_visible():
            return False
        return btn.is_enabled()

    def collect_payment(
        self,
        manifest_id: str,
        amount: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """
        Execute Collect Payment action:
        1. Click 'Collect Payment' button on manifest row
        2. Verify modal opens
        3. Optionally override collected amount or provide notes
        4. Click Save and await submission
        """
        row = self.find_cod_manifest_row(manifest_id)
        btn = row.locator("button:has-text('Collect Payment')").first
        btn.wait_for(state="visible", timeout=self.default_timeout)
        btn.click()
        self.page.wait_for_timeout(1000)

        self.modal.wait_for(state="visible", timeout=self.default_timeout)
        if amount:
            self.modal_amount_input.fill(amount)
        if notes and self.modal_notes_textarea.is_visible():
            self.modal_notes_textarea.fill(notes)

        self.modal_submit_button.click()
        self.page.wait_for_timeout(3000)

    def get_completed_cod_rows(self) -> List[Dict[str, str]]:
        """Return structured data of completed COD settlements."""
        self.switch_cod_tab("Completed")
        rows = self.page.locator(".ant-tabs-tabpane-active tbody tr").all()
        results = []
        for r in rows:
            text = r.inner_text().strip()
            if text and "no data" not in text.lower():
                cols = [c.strip() for c in r.locator("td").all_text_contents() if c.strip()]
                results.append({"raw_text": text, "columns": cols})
        return results

    # =========================================================================
    # Delivery Manifest Verification
    # =========================================================================
    def get_delivery_manifest_status(self, manifest_id: str) -> str:
        """Retrieve manifest status on Delivery Manifests list (e.g. 'Active', 'Completed', 'Closed')."""
        self.open_delivery_manifests()
        row = self.page.locator(f".ant-table-tbody tr:has-text('{manifest_id}')").first
        row.wait_for(state="visible", timeout=self.default_timeout)
        return row.inner_text()

    # =========================================================================
    # Cash Transfer Methods
    # =========================================================================
    def switch_cash_transfer_tab(self, tab_label: str) -> "AccountingPage":
        """
        Switch tabs in Cash Transfer:
        - 'COD Completed pending transfer'
        - 'Cash transfers pending approval'
        - 'Cash transfers approved/rejected'
        """
        tab = self.page.locator(f".ant-tabs-tab:has-text('{tab_label}')").first
        tab.wait_for(state="visible", timeout=self.default_timeout)
        tab.click()
        self.page.wait_for_timeout(1500)
        return self

    def select_hub_branch(self, branch_name: str) -> "AccountingPage":
        """Select a Hub / Branch filter card (e.g. 'Main Branch', 'Dammam Branch')."""
        card = self.hub_options.filter(has_text=branch_name).first
        card.wait_for(state="visible", timeout=self.default_timeout)
        card.click()
        self.page.wait_for_timeout(1000)
        return self

    def get_selected_hub_branch(self) -> str:
        """Get the currently active selected Hub branch name."""
        card = self.page.locator("div[role='listbox'] button[role='option'][aria-selected='true']").first
        if card.is_visible():
            return card.inner_text().strip()
        return ""

    def get_available_hub_branches(self) -> List[str]:
        """Return list of all Hub branch names available in the filter bar."""
        if self.hub_listbox.is_visible():
            return [b.strip() for b in self.hub_options.all_text_contents() if b.strip()]
        return []

    def find_cod_pending_transfer_row(self, settlement_id: str) -> Locator:
        """Locate COD row in 'COD Completed pending transfer' tab."""
        return self.page.locator(f".ant-tabs-tabpane-active tr:has-text('{settlement_id}')").first

    def select_cod_checkbox(self, settlement_id: str) -> None:
        """Select the checkbox corresponding to a settlement ID."""
        row = self.find_cod_pending_transfer_row(settlement_id)
        row.wait_for(state="visible", timeout=self.default_timeout)
        checkbox = row.locator("input[type='checkbox']").first
        checkbox.click()
        self.page.wait_for_timeout(500)

    def is_submit_cash_transfer_button_visible(self) -> bool:
        """Check if 'Submit Cash Transfer' button is visible."""
        return self.submit_cash_transfer_btn.is_visible()

    def is_submit_cash_transfer_button_enabled(self) -> bool:
        """Check if 'Submit Cash Transfer' button is enabled."""
        if not self.submit_cash_transfer_btn.is_visible():
            return False
        return self.submit_cash_transfer_btn.is_enabled()

    def open_submit_cash_transfer_modal(self) -> None:
        """Click 'Submit Cash Transfer' button to open modal."""
        self.submit_cash_transfer_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.submit_cash_transfer_btn.click()
        self.page.wait_for_timeout(1000)

    def get_submit_modal_summary_text(self) -> str:
        """Return modal summary line (e.g. '1 selected • Total 120')."""
        if self.modal.is_visible():
            return self.modal.inner_text()
        return ""

    def close_submit_modal_cancel(self) -> None:
        """Close the Submit Cash Transfer modal via Cancel button, close icon, or Escape and wait for backdrop."""
        if self.modal_close_button.is_visible():
            self.modal_close_button.click()
        elif self.modal_cancel_button.is_visible() and self.modal_cancel_button.is_enabled():
            self.modal_cancel_button.click()
        else:
            self.page.keyboard.press("Escape")
        try:
            self.page.locator(".ant-modal-wrap").first.wait_for(state="hidden", timeout=5000)
        except Exception:
            self.page.wait_for_timeout(1000)

    def submit_cash_transfer(
        self,
        proof_file_path: str,
        amount: Optional[str] = None,
    ) -> None:
        """
        Submit Cash Transfer with proof file:
        1. Open modal
        2. Set file upload
        3. Optionally edit amount
        4. Click Submit
        """
        self.open_submit_cash_transfer_modal()
        self.modal.wait_for(state="visible", timeout=self.default_timeout)

        # Upload proof file
        assert os.path.exists(proof_file_path), f"Proof file does not exist: {proof_file_path}"
        self.modal_file_input.set_input_files(proof_file_path)
        self.page.wait_for_timeout(500)

        if amount:
            self.modal_amount_input.fill(amount)

        self.modal_submit_button.click()
        self.page.wait_for_timeout(3000)

    # =========================================================================
    # Approval & Rejection Methods
    # =========================================================================
    def find_pending_approval_row(self, transfer_number: str) -> Locator:
        """Locate transfer row in 'Cash transfers pending approval' tab."""
        return self.page.locator(f".ant-tabs-tabpane-active tbody tr:has-text('{transfer_number}')").first

    def approve_transfer(self, transfer_number: str) -> None:
        """Click 'Approve' on the transfer row in pending approval tab."""
        row = self.find_pending_approval_row(transfer_number)
        row.wait_for(state="visible", timeout=self.default_timeout)
        btn = row.locator("button:has-text('Approve')").first
        btn.wait_for(state="visible", timeout=self.default_timeout)
        btn.click()
        self.page.wait_for_timeout(3000)

    def reject_transfer(self, transfer_number: str, reason: str) -> None:
        """
        Reject transfer with reason:
        1. Click 'Reject' button
        2. Enter reason in modal textarea
        3. Confirm Reject
        """
        row = self.find_pending_approval_row(transfer_number)
        row.wait_for(state="visible", timeout=self.default_timeout)
        btn = row.locator("button:has-text('Reject')").first
        btn.wait_for(state="visible", timeout=self.default_timeout)
        btn.click()
        self.page.wait_for_timeout(1000)

        self.modal.wait_for(state="visible", timeout=self.default_timeout)
        self.modal_rejection_textarea.fill(reason)
        self.modal_reject_confirm_button.click()
        self.page.wait_for_timeout(3000)

    def find_history_row(self, transfer_number: str) -> Locator:
        """Locate transfer row in 'Cash transfers approved/rejected' tab."""
        return self.page.locator(f".ant-tabs-tabpane-active tbody tr:has-text('{transfer_number}')").first

    def get_history_transfer_status(self, transfer_number: str) -> str:
        """Get status text (e.g. 'Approved', 'Rejected') of a transfer in history tab."""
        row = self.find_history_row(transfer_number)
        if row.is_visible():
            return row.inner_text()
        return ""
