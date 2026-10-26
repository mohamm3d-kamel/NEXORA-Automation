import os
import time
import pytest
from playwright.sync_api import Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.orders_page import OrdersPage

@pytest.mark.orders
class TestOrderCreation:
    """Test suite covering Order Creation scenarios (Single Orders & Bulk Spreadsheet Import)."""

    @pytest.fixture(autouse=True)
    def setup_authenticated_orders(
        self, page: Page, login_page: LoginPage, dashboard_page: DashboardPage, orders_page: OrdersPage
    ):
        """Pre-condition: Authenticate and navigate to Orders page before each test."""
        login_page.open()
        login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        dashboard_page.wait_until_loaded()
        orders_page.open()

    # =========================================================================
    # SINGLE ORDER CREATION SCENARIOS
    # =========================================================================

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
            phone="555222333",
            address="456 Tahlia Street",
            national_address="PAID2002",
        )
        orders_page.click_next()

        # Step 3: Payment (Paid - Prepaid)
        orders_page.select_payment_method("Paid")
        assert not orders_page.is_total_amount_field_visible(), "Total Amount input should be hidden for Paid"
        orders_page.set_financial_details(shipment_value="250")

        # Submit and verify
        orders_page.submit_order()
        assert orders_page.is_order_present_in_list(ref_num), f"Order {ref_num} not found in orders table"

    @pytest.mark.regression
    def test_create_order_multiple_packages_paid(self, orders_page: OrdersPage):
        """Create an order with multiple (2) packages and Paid payment method."""
        ref_num = f"REF-PAID-2P-{int(time.time())}"

        orders_page.click_create_order()

        # Step 1: General (2 Packages)
        orders_page.select_merchant("B2C")
        orders_page.set_reference_number(ref_num)
        orders_page.set_package_count(2)
        assert len(orders_page.get_package_headers()) == 2
        orders_page.click_next()

        # Step 2: Shipment
        orders_page.fill_shipment_details(
            name="Multi Package Paid Customer",
            phone="555666777",
            address="Commercial Ring Rd",
            national_address="PAID4004",
        )
        orders_page.click_next()

        # Step 3: Payment
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

    # =========================================================================
    # BULK ORDER CREATION SCENARIOS (SPREADSHEET IMPORT)
    # =========================================================================

    @pytest.mark.smoke
    @pytest.mark.valid
    def test_valid_download_order_template_csv(self, orders_page: OrdersPage):
        """
        Valid Scenario:
        From Orders list, open spreadsheet import modal, click 'template', and verify
        that 'Order_Template.csv' downloads successfully with expected schema headers.
        """
        orders_page.open_import_modal()
        assert orders_page.is_import_modal_visible(), "Expected import modal to be visible"

        download = orders_page.download_order_template()
        assert download.suggested_filename == "Order_Template.csv", f"Expected Order_Template.csv, got {download.suggested_filename}"

        # Save and verify file structure
        tmp_path = download.path()
        with open(tmp_path, "r", encoding="utf-8-sig") as f:
            header_line = f.readline()
        assert "referenceNumber" in header_line
        assert "consignorName" in header_line
        assert "consignorAddressId" in header_line
        assert "paymentMethod" in header_line

    @pytest.mark.smoke
    @pytest.mark.valid
    def test_valid_bulk_order_creation_end_to_end(self, orders_page: OrdersPage):
        """
        Valid Scenario:
        End-to-End Bulk Order Creation:
        1. Prepare a bulk CSV with 2 unique orders
        2. Upload spreadsheet in Import modal
        3. Advance to Review wizard (/admin/orders/review)
        4. Select B2C Merchant from dropdown to map address and shipping service
        5. Verify 'Create Orders' button becomes enabled
        6. Submit bulk batch and verify both orders reflect in orders table with 'System Bulk' type and 'Created' status.
        """
        unique = int(time.time())
        ref1 = f"BULK-E2E-{unique}-1"
        ref2 = f"BULK-E2E-{unique}-2"

        csv_content = f"""referenceNumber,secondaryReferenceNumber,priority,packageCount,weightKg,specialInstructions,shippingService,consignorName,consignorPhone,consignorEmail,consignorAddressId,customerId,customerName,customerPhone,customerEmail,address1,city,country,state,postalCode,nationalAddress,latitude,longitude,insuranceRequired,signatureRequired,fragileItems,shipmentValue,paymentMethod,totalAmount
{ref1},,HIGH,1,1.5,Fragile,Standard,B2C Merchant,+966555848993,b2c@merchant.com,0c6345f4-e3df-46fe-982b-e7f26d844370,,Bulk Customer 1,+966555123456,bulk1@test.com,123 Main St,Riyadh,Saudi Arabia,,11511,,1,1,false,false,false,150,CASH,150
{ref2},,NORMAL,1,2.0,Handle with care,Standard,B2C Merchant,+966555848993,b2c@merchant.com,0c6345f4-e3df-46fe-982b-e7f26d844370,,Bulk Customer 2,+966555654321,bulk2@test.com,456 King Rd,Riyadh,Saudi Arabia,,11512,,1,1,false,false,false,200,CASH,200
"""
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
        os.makedirs(assets_dir, exist_ok=True)
        csv_path = os.path.join(assets_dir, f"bulk_orders_{unique}.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        try:
            # 1. Open Import Modal & Upload CSV
            orders_page.open_import_modal()
            orders_page.upload_bulk_spreadsheet(csv_path)

            # 2. Advance to Review Page
            orders_page.click_modal_next()
            assert "orders/review" in orders_page.page.url

            # 3. Select Merchant to populate address & service
            orders_page.select_review_merchant("B2C")
            assert orders_page.is_create_orders_button_enabled(), "Create Orders button must be enabled once merchant is selected"

            # 4. Submit Bulk Orders
            orders_page.submit_bulk_orders()
            assert "orders" in orders_page.page.url

            # 5. Verify Orders appear in Orders Table
            row1_text = orders_page.get_order_row_text(ref1)
            row2_text = orders_page.get_order_row_text(ref2)

            assert ref1 in row1_text, f"Expected order {ref1} in table row: {row1_text}"
            assert "System Bulk" in row1_text, f"Expected type 'System Bulk' in row: {row1_text}"
            assert "Created" in row1_text, f"Expected status 'Created' in row: {row1_text}"

            assert ref2 in row2_text, f"Expected order {ref2} in table row: {row2_text}"
            assert "System Bulk" in row2_text, f"Expected type 'System Bulk' in row: {row2_text}"
            assert "Created" in row2_text, f"Expected status 'Created' in row: {row2_text}"

        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    @pytest.mark.regression
    @pytest.mark.invalid
    def test_invalid_bulk_import_empty_file_next_disabled(self, orders_page: OrdersPage):
        """
        Invalid Scenario:
        Assert that in the spreadsheet import modal, the 'Next' button is strictly disabled
        until a file is uploaded.
        """
        orders_page.open_import_modal()
        assert not orders_page.is_modal_next_enabled(), "Next button must be disabled when no spreadsheet file is uploaded"

        # Cleanup: close modal
        orders_page.click_modal_cancel()
        assert not orders_page.is_import_modal_visible(), "Expected modal to close on Cancel"

    @pytest.mark.regression
    @pytest.mark.invalid
    def test_invalid_bulk_review_create_orders_disabled_without_merchant(self, orders_page: OrdersPage):
        """
        Invalid Scenario:
        Upload a template spreadsheet with missing merchant mapping and verify that on the Review page,
        'Create Orders' button remains disabled until a merchant is selected.
        """
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "Order_Template.csv"))
        if not os.path.exists(template_path):
            orders_page.open_import_modal()
            orders_page.download_order_template().save_as(template_path)
            orders_page.click_modal_cancel()

        orders_page.open_import_modal()
        orders_page.upload_bulk_spreadsheet(template_path)
        orders_page.click_modal_next()

        assert "orders/review" in orders_page.page.url
        assert not orders_page.is_create_orders_button_enabled(), "Create Orders button must be disabled when mandatory fields/merchant are unselected"

        # Cleanup: cancel back to orders
        orders_page.cancel_bulk_review()
        assert "orders" in orders_page.page.url

    @pytest.mark.regression
    @pytest.mark.edge
    def test_edge_bulk_import_modal_cancel_preserves_orders_list(self, orders_page: OrdersPage):
        """
        Edge Scenario:
        Attach spreadsheet file in modal, then click 'Cancel', asserting modal closes and orders table is preserved.
        """
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "Order_Template.csv"))
        orders_page.open_import_modal()
        if os.path.exists(template_path):
            orders_page.upload_bulk_spreadsheet(template_path)

        orders_page.click_modal_cancel()
        assert not orders_page.is_import_modal_visible(), "Modal must be closed after clicking Cancel"
        assert "orders" in orders_page.page.url

    @pytest.mark.regression
    @pytest.mark.edge
    def test_edge_bulk_review_cancel_redirects_to_orders(self, orders_page: OrdersPage):
        """
        Edge Scenario:
        Advance to Review page (/admin/orders/review), then click 'Cancel', verifying safe redirection
        back to /admin/orders without corrupting order state.
        """
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "Order_Template.csv"))
        orders_page.open_import_modal()
        orders_page.upload_bulk_spreadsheet(template_path)
        orders_page.click_modal_next()

        assert "orders/review" in orders_page.page.url
        orders_page.cancel_bulk_review()

        assert "orders" in orders_page.page.url
        assert "review" not in orders_page.page.url
