from typing import List, Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from config.settings import settings

class MerchantPage(BasePage):
    """Page Object for B2C Merchant portal (Dashboard, Orders, Pickups)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.dashboard_url = f"{settings.BASE_URL}/tenant/ttenant/merchant/b2c-merchant/dashboard"
        self.orders_url = f"{settings.BASE_URL}/tenant/ttenant/merchant/b2c-merchant/order-management/orders"
        self.pickups_url = f"{settings.BASE_URL}/tenant/ttenant/merchant/b2c-merchant/pickups"

        # Dashboard Locators
        self.welcome_header: Locator = page.locator("text='Welcome back, Merchant'")
        self.new_orders_card: Locator = page.locator("text='New Orders' >> xpath=..")
        self.picked_orders_card: Locator = page.locator("text='Picked Orders' >> xpath=..")

        # Orders Management Locators
        self.create_new_order_btn: Locator = page.locator("button:has-text('Create New Order')").first

        # Wizard Step 1 Locators
        self.reference_number_input: Locator = page.locator("input[name='referenceNumber']").first
        self.package_count_input: Locator = page.locator("input[name='packageCount']").first
        self.next_button: Locator = page.locator("button:has-text('Next')").first

        # Wizard Step 2 Locators
        self.existing_customer_select: Locator = page.locator(".ant-select:has-text('Search by name')").first

        # Wizard Step 3 Locators
        self.payment_method_select: Locator = page.locator(".ant-form-item:has-text('Payment Method') .ant-select").first
        self.total_amount_input: Locator = page.locator(".ant-form-item:has-text('Total Amount') input").first
        self.shipment_value_input: Locator = page.locator(".ant-form-item:has-text('Shipment Value') input").first
        self.submit_order_button: Locator = page.locator("button:has-text('Create Order')").first

        # Pickups Locators
        self.orders_for_pickup_tab: Locator = page.locator("button:has-text('Orders for Pickup'), [role='tab']:has-text('Orders for Pickup')").first
        self.all_pickups_tab: Locator = page.locator("button:has-text('All Pickups'), [role='tab']:has-text('All Pickups')").first
        self.create_pickup_button: Locator = page.locator("button:has-text('Create Pickup')").first

        # Schedule Pickup Modal Locators
        self.schedule_modal: Locator = page.locator(".ant-modal, [role='dialog']").first
        self.pickup_address_select: Locator = page.locator(".ant-modal .ant-select:has-text('Select an address')").first
        self.date_picker: Locator = page.locator(".ant-modal .ant-picker").first
        self.modal_ok_button: Locator = page.locator(".ant-modal button:has-text('OK')").first

    def open_dashboard(self) -> "MerchantPage":
        """Navigate to Merchant Dashboard."""
        self.navigate(self.dashboard_url)
        self.page.wait_for_timeout(1000)
        return self

    def get_new_orders_metric(self) -> str:
        """Retrieve current count text from the 'New Orders' KPI card."""
        self.open_dashboard()
        return self.new_orders_card.inner_text().strip()

    def open_orders_management(self) -> "MerchantPage":
        """Navigate to Merchant Orders Management."""
        self.navigate(self.orders_url)
        self.page.wait_for_timeout(1000)
        return self

    def create_order(
        self,
        reference_number: str,
        package_count: int = 1,
        payment_method: str = "Paid",
        total_amount: Optional[str] = None,
        shipment_value: str = "200",
    ) -> None:
        """Create an order through the Merchant creation wizard."""
        self.open_orders_management()
        self.create_new_order_btn.click()
        self.page.wait_for_timeout(1500)

        # Step 1: General
        self.fill(self.reference_number_input, reference_number)
        if package_count > 1:
            self.fill(self.package_count_input, str(package_count))
        self.next_button.click()
        self.page.wait_for_timeout(1500)

        # Step 2: Shipment (Select existing customer to auto-fill address)
        self.existing_customer_select.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
        self.page.wait_for_timeout(500)
        self.next_button.click()
        self.page.wait_for_timeout(1500)

        # Step 3: Payment
        self.payment_method_select.click()
        self.page.wait_for_timeout(500)
        self.page.locator(
            f".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('{payment_method}')"
        ).first.click()
        self.page.wait_for_timeout(500)

        if payment_method == "Cash" and total_amount:
            self.fill(self.total_amount_input, total_amount)

        self.fill(self.shipment_value_input, shipment_value)
        self.submit_order_button.click()
        self.page.wait_for_timeout(3000)

    def open_pickups(self) -> "MerchantPage":
        """Navigate to Merchant Pickups page."""
        self.navigate(self.pickups_url)
        self.page.wait_for_timeout(1000)
        return self

    def select_order_checkbox_for_pickup(self, index: int = 0) -> None:
        """Select order checkbox by row index."""
        checkbox = self.page.locator(".ant-table-row .ant-checkbox-input, tbody input[type='checkbox']").nth(index)
        checkbox.check()
        self.page.wait_for_timeout(500)

    def schedule_pickup(self) -> str:
        """Schedule a pickup for selected order(s) and return generated pickup number."""
        self.create_pickup_button.click()
        self.schedule_modal.wait_for(state="visible", timeout=self.default_timeout)

        # Select Pickup Address
        self.pickup_address_select.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
        self.page.wait_for_timeout(500)

        # Select date/time from picker (click future date cell and OK)
        self.date_picker.click()
        self.page.wait_for_timeout(500)
        cell = self.page.locator(
            ".ant-picker-dropdown:not(.ant-picker-dropdown-hidden) td:not(.ant-picker-cell-disabled) .ant-picker-cell-inner"
        ).last
        cell.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-picker-dropdown:not(.ant-picker-dropdown-hidden) button:has-text('OK')").first.click()
        self.page.wait_for_timeout(500)

        # Confirm modal
        self.modal_ok_button.click()
        self.page.wait_for_timeout(3000)

        # Switch to All Pickups tab to read the newly generated pickup number
        self.all_pickups_tab.click()
        self.page.wait_for_timeout(2000)
        
        # Extract pickup ID matching PICK-[A-Z0-9]+
        row_text = self.page.locator(".ant-table-row").first.inner_text()
        import re
        match = re.search(r"PICK-[A-Z0-9]+", row_text)
        if match:
            return match.group(0)
        return ""
