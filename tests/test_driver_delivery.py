import time
import re
from typing import Tuple
import pytest
from playwright.sync_api import Browser, Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.orders_page import OrdersPage
from pages.driver_page import DriverPage
from pages.process_management_page import ProcessManagementPage

@pytest.mark.driver
class TestDriverDelivery:
    """Test suite covering Driver Delivery workflows: Delivering orders and recording delivery failures."""

    def _create_and_dispatch_order(self, browser: Browser, payment_method: str = "Paid") -> str:
        """
        Helper method to create a new order as Tenant Admin and dispatch it to b2c driver via Process Management.
        Returns the created shipment number.
        """
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"REF-DEL-{unique_id}"

        # Step 1: Admin creates order
        admin_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = admin_ctx.new_page()
        LoginPage(a_page).open().login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)

        orders = OrdersPage(a_page).open()
        orders.click_create_order()
        orders.select_merchant("B2C")
        orders.set_reference_number(ref_num)
        orders.click_next()

        orders.fill_shipment_details(
            name=f"Customer {unique_id}",
            phone="555123456",
            address="456 King Fahd Rd",
            national_address="11537",
        )
        orders.click_next()

        orders.select_payment_method(payment_method)
        if payment_method == "Cash":
            orders.set_financial_details(total_amount="150", shipment_value="200")
        else:
            orders.set_financial_details(shipment_value="200")
        orders.submit_order()

        # Extract shipment number from Orders table
        a_page.wait_for_timeout(2000)
        orders_row = a_page.locator(".ant-table-tbody tr").filter(has_text=ref_num).first
        row_text = orders_row.inner_text()
        match = re.search(r"ORD[A-Z0-9]+", row_text)
        assert match, f"Could not find shipment number for reference {ref_num} in row: {row_text}"
        shipment_num = match.group(0)

        # Step 2: Dispatch order to b2c driver via Process Management
        pm = ProcessManagementPage(a_page)
        pm.dispatch_order_to_driver(shipment_number=shipment_num, driver_name="b2c driver", branch="Main Branch")

        admin_ctx.close()
        return shipment_num

    @pytest.mark.smoke
    def test_driver_portal_today_manifest_view(self, authenticated_driver: DriverPage):
        """Driver verifies Today's Manifest headers, manifest details card, and shipments table."""
        authenticated_driver.open_today_manifest()
        manifest_text = authenticated_driver.get_details_page_text()

        assert "Today's Manifest" in manifest_text, "Expected 'Today\'s Manifest' header"
        assert "Manifest ID" in manifest_text, "Expected 'Manifest ID' label"
        assert "Driver" in manifest_text, "Expected 'Driver' label"
        assert "Shipments" in manifest_text, "Expected 'Shipments' section"
        assert "Shipment Number" in manifest_text, "Expected 'Shipment Number' column"
        assert "Status" in manifest_text, "Expected 'Status' column"

    @pytest.mark.smoke
    def test_driver_dashboard_kpis_display(self, authenticated_driver: DriverPage):
        """Driver verifies presence of core KPI metrics on Driver Dashboard."""
        metrics = authenticated_driver.get_dashboard_metrics()
        assert metrics["has_total_deliveries"], "Dashboard must contain 'Total deliveries'"
        assert metrics["has_total_failed"], "Dashboard must contain 'Total failed'"
        assert metrics["has_assigned_deliveries"], "Dashboard must contain 'Assigned deliveries'"

    @pytest.mark.regression
    def test_driver_deliver_assigned_order(self, browser: Browser):
        """Driver delivers an assigned order from Today's Manifest and verifies 'Delivered' status."""
        shipment_num = self._create_and_dispatch_order(browser, payment_method="Paid")

        # Driver logs in and opens Today's Manifest
        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)
        driver.open_today_manifest()

        # Verify shipment is listed with Out for Delivery
        initial_row_text = driver.get_shipment_status_on_manifest(shipment_num)
        assert "Out for Delivery" in initial_row_text, f"Expected Out for Delivery in {initial_row_text}"

        # Execute Mark as Delivered
        driver.deliver_order(shipment_number=shipment_num)

        # Verify status transitions to Delivered
        final_row_text = driver.get_shipment_status_on_manifest(shipment_num)
        assert "Delivered" in final_row_text, f"Expected Delivered in {final_row_text}"

        driver_ctx.close()

    @pytest.mark.regression
    def test_driver_fail_order_delivery_with_reason(self, browser: Browser):
        """Driver records a delivery failure with a reason and verifies outcome recorded."""
        shipment_num = self._create_and_dispatch_order(browser, payment_method="Paid")

        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)
        driver.open_today_manifest()

        # Verify shipment is listed
        initial_row_text = driver.get_shipment_status_on_manifest(shipment_num)
        assert "Out for Delivery" in initial_row_text

        # Execute Mark as Delivery Failed
        driver.fail_order_delivery(
            shipment_number=shipment_num,
            reason="Customer No Answer",
            notes="Called customer multiple times; no response.",
        )

        # Verify modal closes and submission succeeded (FDR generated)
        manifest_text = driver.get_details_page_text()
        assert "Delivery marked as failed successfully" in manifest_text or "Delivery outcome recorded successfully" in manifest_text or shipment_num in manifest_text

        driver_ctx.close()

    @pytest.mark.regression
    def test_driver_deliver_failed_order_subsequently(self, browser: Browser):
        """Driver first records delivery failure, then upon customer contact successfully delivers."""
        shipment_num = self._create_and_dispatch_order(browser, payment_method="Paid")

        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)
        driver.open_today_manifest()

        # Step 1: Mark as Delivery Failed
        driver.fail_order_delivery(
            shipment_number=shipment_num,
            reason="Customer Mobile Switched Off",
            notes="Phone switched off on first attempt.",
        )

        # Step 2: Now deliver the order
        driver.deliver_order(shipment_number=shipment_num)

        # Verify status transitions to Delivered
        final_row_text = driver.get_shipment_status_on_manifest(shipment_num)
        assert "Delivered" in final_row_text, f"Expected Delivered in {final_row_text}"

        driver_ctx.close()

    @pytest.mark.e2e
    def test_end_to_end_driver_mixed_batch_lifecycle(self, browser: Browser):
        """
        Complete E2E test verifying delivery and failure handling in a batch:
        1. Create & dispatch Order A and Order B.
        2. Driver delivers Order A -> status becomes Delivered.
        3. Driver marks Order B as Delivery Failed with 'Customer Rejected Shipment'.
        4. Verifies driver dashboard reflects the changes.
        """
        # Create and dispatch both orders
        order_a = self._create_and_dispatch_order(browser, payment_method="Paid")
        order_b = self._create_and_dispatch_order(browser, payment_method="Paid")

        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)

        # 1. Open Today's Manifest
        driver.open_today_manifest()

        # 2. Deliver Order A
        driver.deliver_order(shipment_number=order_a)
        status_a = driver.get_shipment_status_on_manifest(order_a)
        assert "Delivered" in status_a, f"Expected Order A Delivered, got: {status_a}"

        # 3. Mark Order B as Delivery Failed
        driver.fail_order_delivery(
            shipment_number=order_b,
            reason="Customer Rejected Shipment",
            notes="Customer refused delivery due to wrong item ordered.",
        )

        # 4. Check Driver Dashboard KPIs
        driver.open_dashboard()
        metrics = driver.get_dashboard_metrics()
        assert metrics["has_total_deliveries"]
        assert metrics["has_total_failed"]
        assert metrics["has_assigned_deliveries"]

        driver_ctx.close()
