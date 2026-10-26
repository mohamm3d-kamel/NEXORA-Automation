import os
from typing import Optional, List, Dict
from playwright.sync_api import Page, Locator, expect, Download
from pages.base_page import BasePage
from config.settings import settings


class ReportsPage(BasePage):
    """
    Page Object Model for the Reports module:
    - Shipment Reports (/reports/shipment/info)
    - Performance Reports: Driver Performance (/reports/performance/driver-performance)
    - Finance Reports: COD Collection (/reports/finance/cod-collection)
    - Report Creation / Query Builder (/create view)
    - Preview generation, PDF / Excel exports, download verification, and format filtering.
    """

    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = f"{settings.BASE_URL}/tenant/ttenant/admin/reports"

        # Navigation tabs (top tabs)
        self.shipment_reports_tab: Locator = page.get_by_role("tab", name="Shipment Reports")
        self.performance_reports_tab: Locator = page.get_by_role("tab", name="Performance Reports")
        self.finance_reports_tab: Locator = page.get_by_role("tab", name="Finance Reports")

        # Subnav items
        self.shipment_info_subtab: Locator = page.get_by_role("button", name="Shipment Info", exact=True)
        self.driver_performance_subtab: Locator = page.get_by_role("button", name="Driver Performance", exact=True)
        self.cod_collection_subtab: Locator = page.get_by_role("button", name="COD Collection", exact=True)

        # Reports list view elements
        self.create_btn: Locator = page.locator("button:has-text('Create')").first
        self.reports_btn: Locator = page.locator("button:has-text('Reports')").first
        self.format_filter_select: Locator = page.locator(".ant-select.ant-select-lg").first
        self.table: Locator = page.locator(".ant-table")
        self.table_headers: Locator = page.locator(".ant-table-thead th")
        self.table_rows: Locator = page.locator(".ant-table-tbody tr.ant-table-row")
        self.empty_placeholder: Locator = page.locator(".ant-empty")

        # Report Builder / Create view elements
        self.back_to_reports_btn: Locator = page.locator("button:has-text('Back to report types'), button:has-text('Reports')").first
        self.run_preview_btn: Locator = page.locator("button:has-text('Run Preview')").first
        self.export_excel_btn: Locator = page.locator("button:has-text('Export Excel')").first
        self.export_pdf_btn: Locator = page.locator("button:has-text('Export PDF')").first

        # Builder Filter inputs
        self.merchant_select: Locator = page.locator(".ant-form-item:has-text('Merchant') .ant-select").first
        self.branch_select: Locator = page.locator(".ant-form-item:has-text('Branch') .ant-select").first
        self.status_select: Locator = page.locator(".ant-form-item:has-text('Status') .ant-select").first
        self.created_at_from_picker: Locator = page.locator(".ant-form-item:has-text('Created at from') input").first
        self.created_at_to_picker: Locator = page.locator(".ant-form-item:has-text('Created at to') input").first
        self.page_number_input: Locator = page.locator(".ant-form-item:has-text('Page') input.ant-input-number-input").first
        self.limit_input: Locator = page.locator(".ant-form-item:has-text('Limit') input.ant-input-number-input").first

        # Validation errors
        self.form_errors: Locator = page.locator(".ant-form-item-explain-error")

    # =========================================================================
    # Navigation Methods
    # =========================================================================
    def open(self) -> "ReportsPage":
        """Navigate to default reports view (Shipment Reports)."""
        return self.open_shipment_reports()

    def wait_for_table_loaded(self, timeout: int = 10000) -> None:
        """Wait for table headers and either data rows or empty state to render."""
        try:
            self.table_headers.first.wait_for(state="visible", timeout=timeout)
        except Exception:
            pass
        try:
            self.page.locator(".ant-table-tbody tr.ant-table-row, .ant-empty").first.wait_for(
                state="visible", timeout=timeout
            )
        except Exception:
            pass

    def open_shipment_reports(self) -> "ReportsPage":
        """Navigate directly to Shipment Reports list."""
        self.navigate(f"{self.base_url}/shipment/info")
        self.wait_for_table_loaded()
        return self

    def open_performance_reports(self) -> "ReportsPage":
        """Navigate directly to Driver Performance Reports list."""
        self.navigate(f"{self.base_url}/performance/driver-performance")
        self.wait_for_table_loaded()
        return self

    def open_finance_reports(self) -> "ReportsPage":
        """Navigate directly to COD Collection Finance Reports list."""
        self.navigate(f"{self.base_url}/finance/cod-collection")
        self.wait_for_table_loaded()
        return self

    def open_create_view(self, category: str = "shipment") -> "ReportsPage":
        """Navigate to the report builder / create view for a given category."""
        url_map = {
            "shipment": f"{self.base_url}/shipment/info/create",
            "performance": f"{self.base_url}/performance/driver-performance/create",
            "finance": f"{self.base_url}/finance/cod-collection/create",
        }
        if category not in url_map:
            raise ValueError(f"Unknown category: {category}. Choose from {list(url_map.keys())}")
        self.navigate(url_map[category])
        self.page.wait_for_timeout(1500)
        return self

    def switch_via_ui(self, category: str = "Shipment Reports") -> "ReportsPage":
        """Switch between report categories using the top tabs."""
        if "shipment" in category.lower():
            self.shipment_reports_tab.click()
        elif "performance" in category.lower():
            self.performance_reports_tab.click()
        elif "finance" in category.lower():
            self.finance_reports_tab.click()
        self.wait_for_table_loaded()
        return self

    # =========================================================================
    # Report List Table & Filtering
    # =========================================================================
    def get_table_header_titles(self) -> List[str]:
        """Return list of text for all table headers."""
        self.wait_for_table_loaded()
        headers = self.table_headers.all_text_contents()
        return [h.strip() for h in headers if h.strip()]

    def get_report_rows_count(self, wait_for_rows: bool = True) -> int:
        """Return number of data rows in reports list table."""
        if wait_for_rows:
            try:
                self.table_rows.first.wait_for(state="visible", timeout=6000)
            except Exception:
                pass
        return self.table_rows.count()

    def get_all_report_rows_text(self, wait_for_rows: bool = True) -> List[str]:
        """Return text of all data rows in reports list table."""
        if wait_for_rows:
            try:
                self.table_rows.first.wait_for(state="visible", timeout=6000)
            except Exception:
                pass
        rows = self.table_rows.all_text_contents()
        return [r.strip() for r in rows if r.strip()]

    def filter_by_format(self, format_name: str) -> "ReportsPage":
        """Filter reports table by format: 'All formats', 'Excel', or 'PDF'."""
        self.format_filter_select.click()
        self.page.wait_for_timeout(400)
        dropdown = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)")
        dropdown.locator(f".ant-select-item-option:has-text('{format_name}')").first.click()
        self.page.wait_for_timeout(1000)
        self.wait_for_table_loaded()
        return self

    def click_create_report(self) -> "ReportsPage":
        """Click 'Create' button to open report builder."""
        self.create_btn.click()
        self.page.wait_for_timeout(1500)
        return self

    def click_back_to_reports(self) -> "ReportsPage":
        """Click 'Back to report types' or 'Reports' button to return to report list."""
        self.back_to_reports_btn.click()
        self.wait_for_table_loaded()
        return self

    # =========================================================================
    # Report Builder Actions & Export
    # =========================================================================
    def run_preview(self) -> bool:
        """
        Click 'Run Preview' on create view and wait for preview API response.
        Returns True if API returned 200 or 201.
        """
        with self.page.expect_response(lambda r: "reports/v2/run" in r.url or "reports" in r.url, timeout=15000) as resp_info:
            self.run_preview_btn.click()
        resp = resp_info.value
        self.page.wait_for_timeout(1000)
        return resp.status in [200, 201]

    def get_preview_rows_count(self) -> int:
        """Return number of data rows in the preview table."""
        return self.table_rows.count()

    def export_pdf(self) -> bool:
        """
        Click 'Export PDF' and wait for export API response.
        Returns True if API returned 200 or 201.
        """
        with self.page.expect_response(lambda r: "reports/v2/export" in r.url, timeout=15000) as resp_info:
            self.export_pdf_btn.click()
        resp = resp_info.value
        self.page.wait_for_timeout(1000)
        return resp.status in [200, 201]

    def export_excel(self) -> bool:
        """
        Click 'Export Excel' and wait for export API response.
        Returns True if API returned 200 or 201.
        """
        with self.page.expect_response(lambda r: "reports/v2/export" in r.url, timeout=15000) as resp_info:
            self.export_excel_btn.click()
        resp = resp_info.value
        self.page.wait_for_timeout(1000)
        return resp.status in [200, 201]

    def download_top_report(self) -> Download:
        """
        Click download icon on first table row and return Download object.
        """
        self.wait_for_table_loaded()
        first_row = self.table_rows.first
        dl_btn = first_row.locator("span.anticon-download, button:has(.anticon-download), a:has(.anticon-download)").first
        with self.page.expect_download(timeout=15000) as dl_info:
            dl_btn.click()
        return dl_info.value

    def toggle_column_switch(self, column_label: str) -> "ReportsPage":
        """Toggle the switch for an optional column in the report builder."""
        container = self.page.locator("div").filter(has=self.page.locator(f"span:has-text('{column_label}')")).filter(has=self.page.locator("button[role='switch']")).first
        switch = container.locator("button[role='switch']").first
        switch.click()
        self.page.wait_for_timeout(300)
        return self

    def toggle_column_checkbox(self, column_label: str) -> "ReportsPage":
        """Alias for toggle_column_switch."""
        return self.toggle_column_switch(column_label)

    def get_validation_errors(self) -> List[str]:
        """Return active form validation error messages."""
        return [err.strip() for err in self.form_errors.all_text_contents() if err.strip()]
