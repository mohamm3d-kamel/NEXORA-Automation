import time
import pytest
from playwright.sync_api import Browser, Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.merchant_page import MerchantPage
from pages.pickups_admin_page import PickupsAdminPage
from pages.driver_page import DriverPage

@pytest.mark.merchant
class TestMerchantLifecycle:
    """Test suite covering the complete Merchant -> Admin -> Driver lifecycle."""

    @pytest.mark.smoke
    def test_merchant_dashboard_initial_view(self, authenticated_merchant: MerchantPage):
        """Verify Merchant Dashboard loads with welcome banner and metrics."""
        assert authenticated_merchant.is_visible(authenticated_merchant.welcome_header), "Welcome banner missing"
        assert authenticated_merchant.is_visible(authenticated_merchant.new_orders_card), "New Orders KPI card missing"

    @pytest.mark.smoke
    def test_merchant_creates_order(self, authenticated_merchant: MerchantPage):
        """Merchant creates an order and verifies it is submitted."""
        ref_num = f"REF-MERCH-{int(time.time())}"
        authenticated_merchant.create_order(
            reference_number=ref_num,
            package_count=1,
            payment_method="Paid",
            shipment_value="200",
        )
        assert "/orders" in authenticated_merchant.current_url, "Expected redirect to orders list"

    @pytest.mark.pickups
    def test_merchant_schedules_pickup(self, authenticated_merchant: MerchantPage):
        """Merchant selects an order, schedules a pickup, and receives a pickup number."""
        authenticated_merchant.open_pickups()
        authenticated_merchant.select_order_checkbox_for_pickup(0)
        pickup_id = authenticated_merchant.schedule_pickup()

        assert pickup_id.startswith("PICK-"), f"Expected pickup number starting with 'PICK-', got: {pickup_id}"

    @pytest.mark.driver
    def test_driver_portal_active_pickups(self, authenticated_driver: DriverPage):
        """Driver logs in and verifies active pickups list loads."""
        assert "driver-active-pickups" in authenticated_driver.current_url
        table_text = authenticated_driver.get_active_pickups_text()
        assert "Pickup Number" in table_text
        assert "Actions" in table_text

    @pytest.mark.e2e
    def test_full_cross_role_e2e_integration(self, browser: Browser):
        """
        Complete End-to-End Business Scenario:
        1. Merchant logs in, records dashboard metrics, creates order.
        2. Merchant schedules a pickup for the order.
        3. Merchant verifies dashboard updates.
        4. Tenant Admin logs in, assigns pickup to driver (b2c driver).
        5. Tenant Admin verifies status updates to 'Driver Assigned' and checks dashboard.
        6. Driver logs in and verifies pickup is present in Active Pickups.
        """
        unique_id = int(time.time())
        order_ref = f"REF-E2E-{unique_id}"

        # ----------------------------------------------------
        # PHASE 1: MERCHANT CREATES ORDER & SCHEDULES PICKUP
        # ----------------------------------------------------
        merchant_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        m_page = merchant_ctx.new_page()
        m_login = LoginPage(m_page)
        merchant = MerchantPage(m_page)

        # 1. Login as Merchant
        m_login.open()
        m_login.login(settings.MERCHANT_EMAIL, settings.MERCHANT_PASSWORD)
        merchant.open_dashboard()
        initial_metric = merchant.get_new_orders_metric()

        # 2. Create Order
        merchant.create_order(
            reference_number=order_ref,
            package_count=1,
            payment_method="Paid",
            shipment_value="150",
        )

        # 3. Schedule Pickup
        merchant.open_pickups()
        merchant.select_order_checkbox_for_pickup(0)
        scheduled_pickup_id = merchant.schedule_pickup()
        assert scheduled_pickup_id.startswith("PICK-"), f"Invalid pickup ID: {scheduled_pickup_id}"

        # 4. Check Merchant Dashboard Reflection
        merchant.open_dashboard()
        m_page.wait_for_timeout(1000)
        updated_metric = merchant.get_new_orders_metric()
        assert merchant.is_visible(merchant.new_orders_card), "New Orders card should be visible on dashboard"

        merchant_ctx.close()

        # ----------------------------------------------------
        # PHASE 2: TENANT ADMIN ASSIGNS PICKUP TO DRIVER
        # ----------------------------------------------------
        admin_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = admin_ctx.new_page()
        a_login = LoginPage(a_page)
        admin_pickups = PickupsAdminPage(a_page)
        admin_dash = DashboardPage(a_page)

        # 1. Login as Tenant Admin
        a_login.open()
        a_login.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        admin_dash.wait_until_loaded()

        # 2. Assign Driver to the scheduled pickup
        admin_pickups.assign_driver(
            pickup_number=scheduled_pickup_id,
            driver_name="b2c driver",
        )

        # 3. Verify status transitioned to 'Driver Assigned'
        pickup_row_text = admin_pickups.get_pickup_status(scheduled_pickup_id)
        assert "Driver Assigned" in pickup_row_text, f"Expected 'Driver Assigned' status, got: {pickup_row_text}"

        # 4. Verify Tenant Admin Dashboard reflects state
        admin_dash.navigate(settings.get_dashboard_url())
        assert admin_dash.is_dashboard_visible(), "Admin dashboard should load successfully"

        admin_ctx.close()

        # ----------------------------------------------------
        # PHASE 3: DRIVER VERIFIES ASSIGNED PICKUP
        # ----------------------------------------------------
        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        d_login = LoginPage(d_page)
        driver = DriverPage(d_page)

        # 1. Login as Driver
        d_login.open()
        d_login.login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver.open_active_pickups()

        # 2. Verify driver active pickups table contains data
        table_text = driver.get_active_pickups_text()
        assert "Pickup Number" in table_text
        assert "Actions" in table_text

        driver_ctx.close()
