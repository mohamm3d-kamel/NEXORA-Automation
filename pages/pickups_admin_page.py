from typing import Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from config.settings import settings

class PickupsAdminPage(BasePage):
    """Page Object for Tenant Admin Pickups Management."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.pickups_url = f"{settings.BASE_URL}/tenant/ttenant/admin/pickups"

        self.table_rows: Locator = page.locator(".ant-table-row")
        self.assign_modal: Locator = page.locator(".ant-modal, [role='dialog']").first
        self.modal_ok_btn: Locator = page.locator(".ant-modal button:has-text('OK')").first
        self.search_input: Locator = page.locator("input[placeholder*='Search by pickup']").first

    def open(self) -> "PickupsAdminPage":
        """Navigate to Tenant Admin Pickups page."""
        self.navigate(self.pickups_url)
        self.page.wait_for_timeout(2000)
        return self

    def find_pickup_row(self, pickup_number: str) -> Locator:
        """Find the table row matching a pickup number using search if available."""
        if self.search_input.is_visible():
            self.search_input.fill(pickup_number)
            self.search_input.press("Enter")
            self.page.wait_for_timeout(1500)
        
        row = self.page.locator(f".ant-table-row:has-text('{pickup_number}')").first
        try:
            row.wait_for(state="visible", timeout=self.default_timeout)
        except Exception:
            pass
        return row

    def assign_driver(
        self,
        pickup_number: Optional[str] = None,
        driver_name: str = "b2c driver",
        branch_name: Optional[str] = None,
    ) -> None:
        """Assign or reassign a driver to a pickup."""
        self.open()

        if pickup_number:
            target_row = self.find_pickup_row(pickup_number)
            if target_row.count() == 0:
                target_row = self.table_rows.first
        else:
            target_row = self.table_rows.first

        # Click actions ellipsis in the target row
        ellipsis_btn = target_row.locator("button.ant-dropdown-trigger").first
        ellipsis_btn.wait_for(state="visible", timeout=self.default_timeout)
        ellipsis_btn.click()
        self.page.wait_for_timeout(500)

        # Click Assign driver or Reassign driver
        driver_menu_opt = self.page.locator(
            ".ant-dropdown:not(.ant-dropdown-hidden) .ant-dropdown-menu-item:has-text('driver')"
        ).first
        driver_menu_opt.wait_for(state="visible", timeout=self.default_timeout)
        driver_menu_opt.click()
        self.assign_modal.wait_for(state="visible", timeout=self.default_timeout)

        # Select Driver
        driver_select = self.assign_modal.locator(".ant-select").first
        driver_select.click()
        self.page.wait_for_timeout(500)
        driver_opt = self.page.locator(
            f".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('{driver_name}')"
        ).first
        if driver_opt.count() == 0:
            driver_opt = self.page.locator(
                ".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('driver')"
            ).first
        driver_opt.wait_for(state="visible", timeout=self.default_timeout)
        driver_opt.click()
        self.page.wait_for_timeout(500)

        # Select Branch if present
        branch_select = self.assign_modal.locator(".ant-select").nth(1)
        if branch_select.is_visible():
            branch_select.click()
            self.page.wait_for_timeout(500)
            branch_opt = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first
            if branch_opt.is_visible():
                branch_opt.click()
                self.page.wait_for_timeout(500)

        # Confirm modal
        self.modal_ok_btn.click()
        self.page.wait_for_timeout(3000)

    def get_pickup_status(self, pickup_number: Optional[str] = None) -> str:
        """Return the pickup status of the specified row or top row."""
        self.open()
        if pickup_number:
            row = self.find_pickup_row(pickup_number)
            if row.count() > 0:
                return row.inner_text()
        return self.table_rows.first.inner_text()
