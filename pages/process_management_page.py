from typing import Optional, List, Dict
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from config.settings import settings

class ProcessManagementPage(BasePage):
    """Page Object for Process Management barcode scanning and status transitions."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{settings.BASE_URL}/tenant/ttenant/admin/process-management"

        self.scan_action_select: Locator = page.locator(".ant-select").nth(1)
        self.barcode_input: Locator = page.locator("input[placeholder*='Scan barcode']").first
        self.branch_select: Locator = page.locator(".ant-select:has-text('Select branch')").first
        self.driver_select: Locator = page.locator(".ant-select:has-text('Select Driver')").first
        self.reason_select: Locator = page.locator(".ant-select:has-text('Select reason')").first

        self.notifications_table: Locator = page.locator(".ant-table-tbody").nth(1)
        self.scanned_list_table: Locator = page.locator(".ant-table-tbody").first

    def open(self) -> "ProcessManagementPage":
        """Navigate to Process Management."""
        self.navigate(self.url)
        self.page.wait_for_timeout(2000)
        return self

    def select_action(self, action_name: str) -> "ProcessManagementPage":
        """Select a scan action from the dropdown."""
        self.scan_action_select.click()
        self.page.wait_for_timeout(300)
        opt = self.page.locator(f".ant-select-item-option:has-text('{action_name}')").first
        opt.wait_for(state="visible", timeout=self.default_timeout)
        opt.click()
        self.page.wait_for_timeout(500)
        return self

    def select_branch(self, branch_name: str = "Main Branch") -> "ProcessManagementPage":
        """Select branch if required by action."""
        if self.branch_select.is_visible():
            self.branch_select.click()
            self.page.wait_for_timeout(300)
            b_opt = self.page.locator(f".ant-select-item-option:has-text('{branch_name}')").first
            b_opt.wait_for(state="visible", timeout=self.default_timeout)
            b_opt.click()
            self.page.wait_for_timeout(300)
        return self

    def select_driver(self, driver_name: str = "b2c driver") -> "ProcessManagementPage":
        """Select driver if required by action (e.g. Out for Delivery)."""
        if self.driver_select.is_visible():
            self.driver_select.click()
            self.page.wait_for_timeout(300)
            d_opt = self.page.locator(f".ant-select-item-option:has-text('{driver_name}')").first
            d_opt.wait_for(state="visible", timeout=self.default_timeout)
            d_opt.click()
            self.page.wait_for_timeout(300)
        return self

    def select_failure_reason(self, reason: str = "Customer No Answer") -> "ProcessManagementPage":
        """Select failure reason if required (e.g. Delivery Failed)."""
        if self.reason_select.is_visible():
            self.reason_select.click()
            self.page.wait_for_timeout(300)
            r_opt = self.page.locator(f".ant-select-item-option:has-text('{reason}')").first
            r_opt.wait_for(state="visible", timeout=self.default_timeout)
            r_opt.click()
            self.page.wait_for_timeout(300)
        return self

    def scan_barcode(self, barcode: str) -> None:
        """Type barcode / order number and press Enter to execute scan."""
        self.barcode_input.wait_for(state="visible", timeout=self.default_timeout)
        self.barcode_input.fill(barcode)
        self.barcode_input.press("Enter")
        self.page.wait_for_timeout(2000)

    def dispatch_order_to_driver(
        self,
        shipment_number: str,
        driver_name: str = "b2c driver",
        branch: str = "Main Branch",
    ) -> None:
        """
        Full lifecycle dispatch helper:
        1. Arrived in Warehouse (with branch)
        2. Received in Warehouse
        3. Out for Delivery (with driver assignment)
        """
        self.open()

        # Step 1: Arrived in Warehouse
        self.select_action("Arrived in Warehouse")
        self.select_branch(branch)
        self.scan_barcode(shipment_number)

        # Step 2: Received in Warehouse
        self.select_action("Received in Warehouse")
        self.scan_barcode(shipment_number)

        # Step 3: Out for Delivery
        self.select_action("Out for Delivery")
        self.select_driver(driver_name)
        self.scan_barcode(shipment_number)

    def deliver_order(self, shipment_number: str) -> None:
        """Mark an order as Delivered via Process Management barcode scan."""
        self.open()
        self.select_action("Delivered")
        self.scan_barcode(shipment_number)

    def fail_order_delivery(self, shipment_number: str, reason: str = "Customer Rejected Shipment") -> None:
        """Mark an order as Delivery Failed with a failure reason via Process Management."""
        self.open()
        self.select_action("Delivery Failed")
        self.select_failure_reason(reason)
        self.scan_barcode(shipment_number)

    def get_latest_notification_text(self) -> str:
        """Get latest notification text from the scan table."""
        if self.notifications_table.count() > 0:
            first_row = self.notifications_table.locator("tr").first
            if first_row.count() > 0:
                return first_row.inner_text().strip()
        return ""
