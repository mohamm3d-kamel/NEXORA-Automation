from typing import List, Optional
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from config.settings import settings

class OrdersPage(BasePage):
    """Page Object for Nexora Orders List and Order Creation Wizard."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.orders_url = f"{settings.BASE_URL}/tenant/ttenant/admin/orders/orders"

        # List View Locators
        self.create_order_button: Locator = page.locator("button:has-text('Create Order')").first
        self.orders_table: Locator = page.locator(".ant-table, [class*='table']").first

        # Wizard Step Indicators
        self.step_general: Locator = page.locator("text='1General'")
        self.step_shipment: Locator = page.locator("text='2Shipment'")
        self.step_payment: Locator = page.locator("text='3Payment'")

        # Navigation Buttons in Wizard
        self.next_button: Locator = page.locator("button:has-text('Next')").first
        self.back_button: Locator = page.locator("button:has-text('Back')").first
        self.cancel_button: Locator = page.locator("button:has-text('Cancel')").first
        self.submit_order_button: Locator = page.locator("button:has-text('Create Order')").first

        # Step 1: General Locators
        self.merchant_select: Locator = page.locator(".ant-form-item:has-text('Select Merchant') .ant-select").first
        self.merchant_search_input: Locator = page.locator(".ant-form-item:has-text('Select Merchant') input[role='combobox']").first
        self.reference_number_input: Locator = page.locator("input[name='referenceNumber']").first
        self.secondary_reference_input: Locator = page.locator("input[name='secondaryReferenceNumber']").first
        self.priority_select: Locator = page.locator(".ant-form-item:has-text('Priority') .ant-select").first
        self.package_count_input: Locator = page.locator("input[name='packageCount']").first
        self.package_card_headers: Locator = page.locator("h5:has-text('Package')")

        # Step 2: Shipment Locators
        self.consignee_name_input: Locator = page.locator("input[name='shipment.customer.name']").first
        self.consignee_phone_input: Locator = page.locator("input[placeholder='Enter phone number']").last
        self.consignee_email_input: Locator = page.locator("input[name='shipment.customer.email']").first
        self.consignee_address_input: Locator = page.locator("input[name='shipment.shipTo.address1']").first
        self.consignee_postal_code_input: Locator = page.locator("input[name='shipment.shipTo.postalCode']").first
        self.consignee_national_address_input: Locator = page.locator("input[name='shipment.shipTo.nationalAddress']").first
        self.country_select: Locator = page.locator(".ant-form-item:has-text('Country') .ant-select").first
        self.city_select: Locator = page.locator(".ant-form-item:has-text('City') .ant-select").first

        # Step 3: Payment Locators
        self.payment_method_select: Locator = page.locator(".ant-form-item:has-text('Payment Method') .ant-select").first
        self.total_amount_item: Locator = page.locator(".ant-form-item:has-text('Total Amount')")
        self.total_amount_input: Locator = page.locator(".ant-form-item:has-text('Total Amount') input").first
        self.shipment_value_item: Locator = page.locator(".ant-form-item:has-text('Shipment Value')")
        self.shipment_value_input: Locator = page.locator(".ant-form-item:has-text('Shipment Value') input").first

        # Validation Errors
        self.form_errors: Locator = page.locator(".ant-form-item-explain-error")

    # --- Navigation Actions ---
    def open(self) -> "OrdersPage":
        """Navigate directly to Orders page."""
        self.navigate(self.orders_url)
        return self

    def click_create_order(self) -> "OrdersPage":
        """Click 'Create Order' button to launch creation wizard."""
        self.create_order_button.wait_for(state="visible", timeout=self.default_timeout)
        self.create_order_button.click()
        self.page.wait_for_timeout(1000)
        return self

    def click_next(self) -> None:
        """Click 'Next' button to advance to next wizard step."""
        self.next_button.click()
        self.page.wait_for_timeout(1500)

    def click_back(self) -> None:
        """Click 'Back' button to return to previous wizard step."""
        self.back_button.click()
        self.page.wait_for_timeout(1000)

    # --- Step 1: General Actions ---
    def select_merchant(self, search_text: str = "B2C") -> None:
        """Search and select a merchant from the dropdown."""
        self.merchant_search_input.click()
        self.merchant_search_input.fill(search_text)
        self.page.wait_for_timeout(1000)
        option = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first
        option.wait_for(state="visible", timeout=self.default_timeout)
        option.click()

    def set_reference_number(self, ref: str) -> None:
        """Fill reference number."""
        self.fill(self.reference_number_input, ref)

    def set_package_count(self, count: int) -> None:
        """Set total number of packages."""
        self.fill(self.package_count_input, str(count))
        self.page.wait_for_timeout(500)

    def get_package_headers(self) -> List[str]:
        """Return list of visible package section header titles."""
        return [h.strip() for h in self.package_card_headers.all_inner_texts() if h.strip()]

    # --- Step 2: Shipment Actions ---
    def fill_shipment_details(
        self,
        name: str = "Test Customer",
        phone: str = "555123456",
        address: str = "123 Commercial St",
        national_address: str = "RRRR1234",
    ) -> None:
        """Fill receiver customer and destination address fields."""
        self.fill(self.consignee_name_input, name)
        self.fill(self.consignee_phone_input, phone)
        self.fill(self.consignee_address_input, address)
        self.fill(self.consignee_national_address_input, national_address)

        # Select Country if not selected
        if self.country_select.is_visible():
            self.country_select.click()
            c_opt = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first
            try:
                c_opt.wait_for(state="visible", timeout=5000)
                c_opt.click()
                self.page.wait_for_timeout(500)
            except Exception:
                pass

        # Select City
        if self.city_select.is_visible():
            self.city_select.click()
            city_opt = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first
            try:
                city_opt.wait_for(state="visible", timeout=5000)
                city_opt.click()
                self.page.wait_for_timeout(500)
            except Exception:
                pass

    # --- Step 3: Payment Actions ---
    def select_payment_method(self, method: str) -> None:
        """Select payment method ('Cash' or 'Paid')."""
        self.payment_method_select.click()
        self.page.wait_for_timeout(500)
        method_opt = self.page.locator(
            f".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('{method}')"
        ).first
        method_opt.wait_for(state="visible", timeout=self.default_timeout)
        method_opt.click()
        self.page.wait_for_timeout(500)

    def is_total_amount_field_visible(self) -> bool:
        """Returns True if Total Amount (SAR) input is visible."""
        return self.is_visible(self.total_amount_input, timeout=2000)

    def set_financial_details(self, total_amount: Optional[str] = None, shipment_value: Optional[str] = None) -> None:
        """Fill financial amounts (Total Amount for Cash, Shipment Value)."""
        if total_amount and self.is_total_amount_field_visible():
            self.fill(self.total_amount_input, total_amount)
        if shipment_value and self.is_visible(self.shipment_value_input, timeout=2000):
            self.fill(self.shipment_value_input, shipment_value)

    def submit_order(self) -> None:
        """Click the final 'Create Order' button to submit."""
        self.submit_order_button.click()
        self.page.wait_for_timeout(3000)

    def is_order_present_in_list(self, ref_number: str) -> bool:
        """Check if an order reference number exists in the orders table."""
        self.wait_for_url("**/orders", timeout=self.default_timeout)
        target = self.page.get_by_text(ref_number)
        return target.count() > 0

    def get_validation_errors(self) -> List[str]:
        """Retrieve list of currently visible form validation error messages."""
        self.page.wait_for_timeout(500)
        return [err.strip() for err in self.form_errors.all_inner_texts() if err.strip()]
