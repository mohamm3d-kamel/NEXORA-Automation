import re
from typing import List, Optional, Dict
from playwright.sync_api import Page, Locator, Download
from pages.base_page import BasePage
from config.settings import settings


class ManifestsPage(BasePage):
    """
    Page Object Model for the Manifests and Pickups Management modules:
    - Delivery Manifests (/manifests/delivery-manifests)
    - Ready for Delivery Manifests (/manifests/ready-for-delivery-manifests)
    - Intra-Hub Manifests (/manifests/intra-hub-manifests)
    - Return Manifests (/manifests/return-manifests)
    - Manifest Details & Export/Print actions
    - Pickups Integration (/admin/pickups)
    """

    def __init__(self, page: Page):
        super().__init__(page)

        # Base URLs
        self.delivery_manifests_url = f"{settings.BASE_URL}/tenant/ttenant/admin/manifests/delivery-manifests"
        self.ready_manifests_url = f"{settings.BASE_URL}/tenant/ttenant/admin/manifests/ready-for-delivery-manifests"
        self.intra_hub_manifests_url = f"{settings.BASE_URL}/tenant/ttenant/admin/manifests/intra-hub-manifests"
        self.return_manifests_url = f"{settings.BASE_URL}/tenant/ttenant/admin/manifests/return-manifests"
        self.admin_pickups_url = f"{settings.BASE_URL}/tenant/ttenant/admin/pickups"

        # Tab locators (buttons / tabs on manifests sub-navigation)
        self.tab_delivery_manifests: Locator = page.locator("button:has-text('Delivery Manifests'), [role='tab']:has-text('Delivery Manifests')").first
        self.tab_ready_manifests: Locator = page.locator("button:has-text('Ready for Delivery Manifests'), [role='tab']:has-text('Ready for Delivery Manifests')").first
        self.tab_intra_hub_manifests: Locator = page.locator("button:has-text('IntraHub Manifests'), [role='tab']:has-text('IntraHub Manifests')").first
        self.tab_return_manifests: Locator = page.locator("button:has-text('Return Manifests'), [role='tab']:has-text('Return Manifests')").first

        # Tables & Lists
        self.table_headers: Locator = page.locator("th")
        self.table_rows: Locator = page.locator(".ant-table-tbody tr")
        self.empty_state: Locator = page.locator(".ant-empty, .ant-table-placeholder")

        # Search Inputs
        self.manifest_search_input: Locator = page.locator("input[placeholder='Search']").first
        self.pickup_search_input: Locator = page.locator("input[placeholder*='Search by pickup']").first

        # Detail View Elements
        self.detail_back_btn: Locator = page.locator("button:has-text('Back')").first
        self.detail_export_excel_btn: Locator = page.locator("button:has-text('Export to Excel')").first
        self.detail_print_btn: Locator = page.locator("button:has-text('Print')").first
        self.detail_manifest_title: Locator = page.locator("h1, h2, h3, h4, h5, .ant-page-header-heading-title, [class*='title']").first

        # Creation Views (IntraHub & Returns)
        self.create_intra_hub_btn: Locator = page.locator("button:has-text('Create IntraHub Manifest')").first
        self.create_return_btn: Locator = page.locator("button:has-text('Create Return Manifest')").first
        self.create_next_btn: Locator = page.locator("button:has-text('Next')").first
        self.create_cancel_btn: Locator = page.locator("button:has-text('Cancel')").first
        self.validation_errors: Locator = page.locator(".ant-form-item-explain-error, .ant-form-item-explain, [role='alert']")

        # Pickups Elements
        self.pickup_rows: Locator = page.locator(".ant-table-tbody tr:has-text('PICK-')")

    # =========================================================================
    # Navigation Methods
    # =========================================================================

    def open_delivery_manifests(self) -> "ManifestsPage":
        """Navigate to Delivery Manifests list view."""
        self.navigate(self.delivery_manifests_url)
        self.wait_for_table_loaded()
        return self

    def open_ready_for_delivery_manifests(self) -> "ManifestsPage":
        """Navigate to Ready for Delivery Manifests list view."""
        self.navigate(self.ready_manifests_url)
        self.wait_for_table_loaded()
        return self

    def open_intra_hub_manifests(self) -> "ManifestsPage":
        """Navigate to Intra-Hub Manifests list view."""
        self.navigate(self.intra_hub_manifests_url)
        self.wait_for_table_loaded()
        return self

    def open_return_manifests(self) -> "ManifestsPage":
        """Navigate to Return Manifests list view."""
        self.navigate(self.return_manifests_url)
        self.wait_for_table_loaded()
        return self

    def open_admin_pickups(self) -> "ManifestsPage":
        """Navigate to Admin Pickups view."""
        self.navigate(self.admin_pickups_url)
        self.wait_for_table_loaded()
        return self

    def switch_tab(self, tab_name: str) -> "ManifestsPage":
        """Switch manifest tab via top UI button."""
        tab_btn = self.page.locator(f"button:has-text('{tab_name}'), [role='tab']:has-text('{tab_name}')").first
        tab_btn.wait_for(state="visible", timeout=self.default_timeout)
        tab_btn.click()
        self.page.wait_for_timeout(1500)
        self.wait_for_table_loaded()
        return self

    def wait_for_table_loaded(self, timeout: int = 15000) -> None:
        """Wait until network is idle and table or empty placeholder is rendered."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass
        self.page.wait_for_timeout(1000)

    # =========================================================================
    # Table & List Inspection
    # =========================================================================

    def get_table_headers(self) -> List[str]:
        """Return clean list of visible table header texts."""
        headers = self.table_headers.all_inner_texts()
        return [h.strip() for h in headers if h.strip()]

    def get_row_count(self) -> int:
        """Return count of data rows in the active table, excluding skeleton/placeholder."""
        self.wait_for_table_loaded()
        if self.is_empty_state_visible():
            return 0
        rows = self.table_rows.all()
        real_rows = [
            r for r in rows
            if r.is_visible()
            and not r.locator(".ant-skeleton").count()
            and "ant-table-placeholder" not in (r.get_attribute("class") or "")
            and "No Data" not in r.inner_text()
            and r.inner_text().strip()
        ]
        return len(real_rows)

    def get_all_rows_text(self) -> List[str]:
        """Return inner text of all data rows."""
        self.wait_for_table_loaded()
        rows = self.table_rows.all()
        results = []
        for r in rows:
            if r.is_visible() and not r.locator(".ant-skeleton").count():
                txt = r.inner_text().strip()
                if txt and "No Data" not in txt:
                    results.append(txt)
        return results

    def is_empty_state_visible(self) -> bool:
        """Check if empty placeholder ('No Data') is displayed."""
        self.page.wait_for_timeout(500)
        return self.empty_state.first.is_visible()

    # =========================================================================
    # Search & Filtering
    # =========================================================================

    def search_manifest(self, keyword: str) -> "ManifestsPage":
        """Type keyword into manifest search box and trigger search."""
        self.manifest_search_input.wait_for(state="visible", timeout=self.default_timeout)
        self.manifest_search_input.fill(keyword)
        self.manifest_search_input.press("Enter")
        self.page.wait_for_timeout(1500)
        self.wait_for_table_loaded()
        return self

    def search_pickup(self, keyword: str) -> "ManifestsPage":
        """Type keyword into pickup search box and trigger search."""
        self.pickup_search_input.wait_for(state="visible", timeout=self.default_timeout)
        self.pickup_search_input.fill(keyword)
        self.pickup_search_input.press("Enter")
        self.page.wait_for_timeout(1500)
        self.wait_for_table_loaded()
        return self

    # =========================================================================
    # Manifest Detail & Actions
    # =========================================================================

    def open_delivery_manifest_detail(self, manifest_id: Optional[str] = None) -> "ManifestsPage":
        """Click on a delivery manifest link to open its details view."""
        if manifest_id:
            link = self.page.locator(f"a:has-text('{manifest_id}'), button:has-text('{manifest_id}'), span:has-text('{manifest_id}')").first
        else:
            link = self.page.locator("a:has-text('DM-'), button:has-text('DM-'), span:has-text('DM-')").first
        
        link.wait_for(state="visible", timeout=self.default_timeout)
        link.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
        return self

    def open_ready_manifest_detail(self, manifest_id: Optional[str] = None) -> "ManifestsPage":
        """Click on a Ready for Delivery manifest link to open its details view."""
        if manifest_id:
            link = self.page.locator(f"a:has-text('{manifest_id}'), button:has-text('{manifest_id}'), span:has-text('{manifest_id}')").first
        else:
            link = self.page.locator("a:has-text('RFD-'), button:has-text('RFD-'), span:has-text('RFD-')").first

        link.wait_for(state="visible", timeout=self.default_timeout)
        link.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
        return self

    def get_detail_page_text(self) -> str:
        """Return entire inner text of the detail page container."""
        self.page.wait_for_timeout(1000)
        return self.page.inner_text("main, .ant-layout-content, body")

    def click_detail_back(self) -> "ManifestsPage":
        """Click 'Back' button on detail page."""
        self.detail_back_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.detail_back_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1500)
        return self

    def export_to_excel(self, timeout: int = 20000) -> Download:
        """Click 'Export to Excel' on details view and await browser download."""
        self.detail_export_excel_btn.wait_for(state="visible", timeout=self.default_timeout)
        with self.page.expect_download(timeout=timeout) as download_info:
            self.detail_export_excel_btn.click()
        return download_info.value

    def is_print_button_enabled(self) -> bool:
        """Verify Print button is visible and enabled."""
        if not self.detail_print_btn.is_visible():
            return False
        return self.detail_print_btn.is_enabled()

    def click_print(self) -> None:
        """Click Print button on manifest detail view."""
        self.detail_print_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.detail_print_btn.click()
        self.page.wait_for_timeout(1000)

    # =========================================================================
    # Intra-Hub & Return Manifest Creation Forms
    # =========================================================================

    def open_create_intra_hub(self) -> "ManifestsPage":
        """Navigate to IntraHub and click 'Create IntraHub Manifest'."""
        self.open_intra_hub_manifests()
        self.create_intra_hub_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.create_intra_hub_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1500)
        return self

    def open_create_return_manifest(self) -> "ManifestsPage":
        """Navigate to Return Manifests and click 'Create Return Manifest'."""
        self.open_return_manifests()
        self.create_return_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.create_return_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1500)
        return self

    def click_create_next(self) -> "ManifestsPage":
        """Click 'Next' button on manifest creation wizard."""
        self.create_next_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.create_next_btn.click()
        self.page.wait_for_timeout(1000)
        return self

    def click_create_cancel(self) -> "ManifestsPage":
        """Click 'Cancel' button on manifest creation wizard."""
        self.create_cancel_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.create_cancel_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1500)
        return self

    def get_validation_errors(self) -> List[str]:
        """Return list of validation errors displayed on creation form."""
        self.page.wait_for_timeout(500)
        errors = self.validation_errors.all_inner_texts()
        return [e.strip() for e in errors if e.strip()]

    # =========================================================================
    # Pickups Integration
    # =========================================================================

    def get_pickup_rows_text(self) -> List[str]:
        """Return list of text for all pickup rows starting with 'PICK-'."""
        self.wait_for_table_loaded()
        rows = self.pickup_rows.all()
        return [r.inner_text().strip() for r in rows if r.is_visible()]

    def open_pickup_detail(self, pickup_number: Optional[str] = None) -> "ManifestsPage":
        """Click pickup number or View action to open pickup details."""
        if pickup_number:
            btn = self.page.locator(f"button:has-text('{pickup_number}'), a:has-text('{pickup_number}')").first
        else:
            btn = self.page.locator("button:has-text('PICK-'), a:has-text('PICK-')").first
        
        btn.wait_for(state="visible", timeout=self.default_timeout)
        btn.click()
        self.page.wait_for_timeout(1500)
        return self
