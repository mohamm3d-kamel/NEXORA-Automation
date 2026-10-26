from typing import List, Optional
from playwright.sync_api import Page, Locator, expect, Download
from pages.base_page import BasePage
from config.settings import settings

class OrdersPage(BasePage):
    """Page Object for Nexora Orders List, Single Order Wizard, and Bulk Order Spreadsheet Import."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.orders_url = f"{settings.BASE_URL}/tenant/ttenant/admin/orders/orders"
        self.review_url = f"{settings.BASE_URL}/tenant/ttenant/admin/orders/review"

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

        # Bulk Order Spreadsheet Import Locators
        self.import_spreadsheet_btn: Locator = page.locator("button[aria-label='Import order(s) with spreadsheet'], button:has(.anticon-upload)").first
        self.import_modal: Locator = page.locator(".ant-modal").first
        self.template_download_btn: Locator = page.locator(".ant-modal button:has-text('template'), .ant-modal a:has-text('template')").first
        self.spreadsheet_file_input: Locator = page.locator(".ant-modal input[type='file']").first
        self.modal_next_btn: Locator = page.locator(".ant-modal button:has-text('Next')").first
        self.modal_cancel_btn: Locator = page.locator(".ant-modal button:has-text('Cancel')").first

        # Bulk Review Page Locators (/orders/review)
        self.review_table: Locator = page.locator(".ant-table").first
        self.review_merchant_select: Locator = page.locator(".ant-select:has-text('Select merchant'), .ant-select:has-text('Merchant')").first
        self.review_create_orders_btn: Locator = page.locator("button:has-text('Create Orders')").first
        self.review_cancel_btn: Locator = page.locator("button:has-text('Cancel')").first

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

    # =========================================================================
    # Bulk Order Import via Spreadsheet Methods
    # =========================================================================

    def open_import_modal(self) -> "OrdersPage":
        """Click the 'Import order(s) with spreadsheet' button to open import modal."""
        self.import_spreadsheet_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.import_spreadsheet_btn.click()
        self.import_modal.wait_for(state="visible", timeout=self.default_timeout)
        return self

    def is_import_modal_visible(self) -> bool:
        """Check if spreadsheet import modal is displayed."""
        return self.import_modal.is_visible()

    def download_order_template(self, timeout: int = 15000) -> Download:
        """Click template link inside modal and await browser download."""
        self.template_download_btn.wait_for(state="visible", timeout=self.default_timeout)
        with self.page.expect_download(timeout=timeout) as download_info:
            self.template_download_btn.click()
        return download_info.value

    def is_modal_next_enabled(self) -> bool:
        """Check if modal Next button is enabled."""
        if not self.modal_next_btn.is_visible():
            return False
        return self.modal_next_btn.is_enabled()

    def upload_bulk_spreadsheet(self, file_path: str) -> "OrdersPage":
        """Attach CSV or Excel spreadsheet into the modal file input."""
        self.spreadsheet_file_input.set_input_files(file_path)
        self.page.wait_for_timeout(1000)
        return self

    def click_modal_next(self) -> "OrdersPage":
        """Click Next button on modal and wait for /orders/review page to load."""
        self.modal_next_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.modal_next_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
        return self

    def click_modal_cancel(self) -> "OrdersPage":
        """Click Cancel button on import modal."""
        self.modal_cancel_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.modal_cancel_btn.click()
        self.page.wait_for_timeout(1000)
        return self

    def select_review_merchant(self, merchant_name: str = "B2C") -> "OrdersPage":
        """Select merchant from the dropdown at top of review page."""
        self.review_merchant_select.wait_for(state="visible", timeout=self.default_timeout)
        self.review_merchant_select.click()
        self.page.wait_for_timeout(500)
        opt = self.page.locator(f".ant-select-item-option:has-text('{merchant_name}')").first
        opt.wait_for(state="visible", timeout=self.default_timeout)
        opt.click()
        self.page.wait_for_timeout(1500)
        return self

    def is_create_orders_button_enabled(self) -> bool:
        """Check if 'Create Orders' button on review page is enabled."""
        if not self.review_create_orders_btn.is_visible():
            return False
        return self.review_create_orders_btn.is_enabled()

    def submit_bulk_orders(self) -> "OrdersPage":
        """Click 'Create Orders' button on review page and await redirection back to orders list."""
        self.review_create_orders_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.review_create_orders_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(3000)
        return self

    def cancel_bulk_review(self, confirm: bool = True) -> "OrdersPage":
        """
        Click Cancel button on review page.
        If confirm is True, clicks 'Yes' on the confirmation modal ('Are you sure you want to cancel upload?').
        If confirm is False, clicks 'No' to stay on review page.
        """
        self.review_cancel_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.review_cancel_btn.click()
        self.page.wait_for_timeout(500)
        confirm_btn_text = "Yes" if confirm else "No"
        confirm_btn = self.page.locator(f".ant-modal button:has-text('{confirm_btn_text}')").first
        if confirm_btn.is_visible():
            confirm_btn.click()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1500)
        return self

    def get_order_row_text(self, ref_number: str) -> str:
        """Return the inner text of the order row matching the given reference number."""
        self.page.wait_for_timeout(1000)
        row = self.page.locator(f".ant-table-tbody tr:has-text('{ref_number}')").first
        if row.is_visible():
            return row.inner_text().strip()
        return ""
