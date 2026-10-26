import time
import pytest
from playwright.sync_api import Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.orders_page import OrdersPage

@pytest.mark.orders
class TestOrderCreation:
    """Test suite covering Order Creation scenarios with different package counts and payment types."""

    @pytest.fixture(autouse=True)
    def setup_authenticated_orders(
        self, page: Page, login_page: LoginPage, dashboard_page: DashboardPage, orders_page: OrdersPage
    ):
        """Pre-condition: Authenticate and navigate to Orders page before each test."""
        login_page.open()
        login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        dashboard_page.wait_until_loaded()
        orders_page.open()

    @pytest.mark.smoke
    def test_create_order_single_package_cash(self, orders_page: OrdersPage):
        """Create an order with 1 package and Cash (COD) payment method."""
        ref_num = f"REF-CASH-1P-{int(time.time())}"

        orders_page.click_create_order()

        # Step 1: General (1 Package)
        orders_page.select_merchant("B2C")
        orders_page.set_reference_number(ref_num)
        orders_page.set_package_count(1)
        assert len(orders_page.get_package_headers()) == 1, "Expected 1 package header"
        orders_page.click_next()

        # Step 2: Shipment Details
        orders_page.fill_shipment_details(
            name="Cash Single Receiver",
            phone="555111222",
            address="Building 10, King Fahd Rd",
            national_address="CASH1001",
        )
        orders_page.click_next()

        # Step 3: Payment (Cash)
        orders_page.select_payment_method("Cash")
        assert orders_page.is_total_amount_field_visible(), "Total Amount input must be visible for Cash payment"
        orders_page.set_financial_details(total_amount="120", shipment_value="150")

        # Submit and verify
        orders_page.submit_order()
        assert orders_page.is_order_present_in_list(ref_num), f"Order {ref_num} not found in orders table"

    @pytest.mark.regression
    def test_create_order_multiple_packages_cash(self, orders_page: OrdersPage):
        """Create an order with multiple (3) packages and Cash (COD) payment."""
        ref_num = f"REF-CASH-3P-{int(time.time())}"

        orders_page.click_create_order()

        # Step 1: General with 3 packages
        orders_page.select_merchant("B2C")
        orders_page.set_reference_number(ref_num)
        orders_page.set_package_count(3)
        headers = orders_page.get_package_headers()
        assert len(headers) == 3, f"Expected 3 package headers, got: {headers}"
        orders_page.click_next()

        # Step 2: Shipment
        orders_page.fill_shipment_details(
            name="Multi Package Cash Client",
            phone="555333444",
            address="789 Olaya Street",
            national_address="CASH3003",
        )
        orders_page.click_next()

        # Step 3: Payment (Cash)
        orders_page.select_payment_method("Cash")
        orders_page.set_financial_details(total_amount="450", shipment_value="500")

        # Submit and verify
        orders_page.submit_order()
        assert orders_page.is_order_present_in_list(ref_num), f"Order {ref_num} not found in orders table"

    @pytest.mark.smoke
    def test_create_order_single_package_paid(self, orders_page: OrdersPage):
        """Create an order with 1 package and Paid (prepaid) payment method."""
        ref_num = f"REF-PAID-1P-{int(time.time())}"

        orders_page.click_create_order()

        # Step 1: General (1 Package)
        orders_page.select_merchant("B2C")
        orders_page.set_reference_number(ref_num)
        orders_page.set_package_count(1)
        orders_page.click_next()

        # Step 2: Shipment Details
        orders_page.fill_shipment_details(
            name="Paid Single Receiver",
            phone="555777888",
            address="45 Al Malaz District",
            national_address="PAID1001",
        )
        orders_page.click_next()

        # Step 3: Payment (Paid)
        orders_page.select_payment_method("Paid")
        assert not orders_page.is_total_amount_field_visible(), "Total Amount must be hidden for Paid orders"
        orders_page.set_financial_details(shipment_value="250")

        # Submit and verify
        orders_page.submit_order()
        assert orders_page.is_order_present_in_list(ref_num), f"Order {ref_num} not found in orders table"

    @pytest.mark.regression
    def test_create_order_multiple_packages_paid(self, orders_page: OrdersPage):
        """Create an order with multiple (2) packages and Paid (prepaid) payment."""
        ref_num = f"REF-PAID-2P-{int(time.time())}"

        orders_page.click_create_order()

        # Step 1: General (2 Packages)
        orders_page.select_merchant("B2C")
        orders_page.set_reference_number(ref_num)
        orders_page.set_package_count(2)
        assert len(orders_page.get_package_headers()) == 2
        orders_page.click_next()

        # Step 2: Shipment Details
        orders_page.fill_shipment_details(
            name="Multi Package Paid Client",
            phone="555999000",
            address="12 Al Nakheel Blvd",
            national_address="PAID2002",
        )
        orders_page.click_next()

        # Step 3: Payment (Paid)
        orders_page.select_payment_method("Paid")
        orders_page.set_financial_details(shipment_value="350")

        # Submit and verify
        orders_page.submit_order()
        assert orders_page.is_order_present_in_list(ref_num), f"Order {ref_num} not found in orders table"

    @pytest.mark.regression
    def test_payment_method_dynamic_fields_toggle(self, orders_page: OrdersPage):
        """Verify dynamic visibility: 'Cash' displays Total Amount, 'Paid' hides Total Amount."""
        orders_page.click_create_order()

        # Step 1 & 2 Quick navigation
        orders_page.select_merchant("B2C")
        orders_page.set_reference_number(f"REF-TOGGLE-{int(time.time())}")
        orders_page.click_next()

        orders_page.fill_shipment_details()
        orders_page.click_next()

        # Test selecting Cash -> Total Amount visible
        orders_page.select_payment_method("Cash")
        assert orders_page.is_total_amount_field_visible(), "Total Amount should be visible when Cash is selected"

        # Test selecting Paid -> Total Amount hidden
        orders_page.select_payment_method("Paid")
        assert not orders_page.is_total_amount_field_visible(), "Total Amount should NOT be visible when Paid is selected"

        # Toggle back to Cash -> Total Amount visible again
        orders_page.select_payment_method("Cash")
        assert orders_page.is_total_amount_field_visible(), "Total Amount should reappear when switching back to Cash"

    @pytest.mark.regression
    def test_package_count_dynamically_renders_sections(self, orders_page: OrdersPage):
        """Verify changing package count updates the number of package sections."""
        orders_page.click_create_order()

        # Verify initial default count is 1
        assert len(orders_page.get_package_headers()) == 1

        # Change to 4 packages
        orders_page.set_package_count(4)
        headers = orders_page.get_package_headers()
        assert len(headers) == 4, f"Expected 4 package cards, got: {headers}"
        assert "Package 1" in headers
        assert "Package 4" in headers

        # Change down to 2 packages
        orders_page.set_package_count(2)
        assert len(orders_page.get_package_headers()) == 2

    @pytest.mark.regression
    def test_validation_empty_merchant_step1(self, orders_page: OrdersPage):
        """Verify advancing Step 1 without selecting merchant shows validation error."""
        orders_page.click_create_order()

        orders_page.set_reference_number("REF-NO-MERCHANT")
        orders_page.click_next()

        errors = orders_page.get_validation_errors()
        assert "This field is required" in errors, f"Expected validation error in {errors}"

    @pytest.mark.regression
    def test_validation_empty_consignee_step2(self, orders_page: OrdersPage):
        """Verify advancing Step 2 without required consignee info shows validation errors."""
        orders_page.click_create_order()

        # Fill Step 1 validly
        orders_page.select_merchant("B2C")
        orders_page.set_reference_number(f"REF-ERR-S2-{int(time.time())}")
        orders_page.click_next()

        # Click Next on Step 2 without filling consignee info
        orders_page.click_next()

        errors = orders_page.get_validation_errors()
        assert "This field is required" in errors, f"Expected required field errors on Step 2, got: {errors}"
