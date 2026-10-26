import time
import pytest
from playwright.sync_api import Browser, Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.merchant_page import MerchantPage
from pages.pickups_admin_page import PickupsAdminPage
from pages.driver_page import DriverPage

@pytest.mark.driver
class TestDriverActions:
    """Test suite covering Driver persona actions: Accept, Reject, and Proceeding with Pickups."""

    @pytest.mark.smoke
    def test_driver_portal_active_pickups_table(self, authenticated_driver: DriverPage):
        """Driver verifies the Active Pickups table headers and action controls."""
        table_text = authenticated_driver.get_active_pickups_text()
        assert "Pickup Number" in table_text, "Expected 'Pickup Number' column"
        assert "Pickup Status" in table_text, "Expected 'Pickup Status' column"
        assert "Actions" in table_text, "Expected 'Actions' column"

    @pytest.mark.regression
    def test_driver_proceed_accepted_pickup_details(self, authenticated_driver: DriverPage):
        """Driver proceeds with an accepted pickup by opening and reviewing its details."""
        authenticated_driver.view_pickup_details()
        details_text = authenticated_driver.get_details_page_text()

        assert "Driver Accepted" in details_text, "Expected status 'Driver Accepted' on details page"
        assert "Merchant" in details_text, "Expected merchant information section"
        assert "Pickup Orders" in details_text, "Expected pickup orders list on details page"

    @pytest.mark.regression
    def test_driver_accept_assigned_pickup(self, browser: Browser):
        """Driver accepts an assigned pickup and verifies status transitions to 'Driver Accepted'."""
        unique_id = int(time.time())
        order_ref = f"REF-ACC-{unique_id}"

        # Step 1: Merchant creates order & schedules pickup
        merchant_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        m_page = merchant_ctx.new_page()
        LoginPage(m_page).open().login(settings.MERCHANT_EMAIL, settings.MERCHANT_PASSWORD)
        merchant = MerchantPage(m_page)
        merchant.create_order(reference_number=order_ref, package_count=1, payment_method="Paid")
        merchant.open_pickups()
        merchant.select_order_checkbox_for_pickup(0)
        pickup_id = merchant.schedule_pickup()
        merchant_ctx.close()

        # Step 2: Tenant Admin assigns driver
        admin_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = admin_ctx.new_page()
        LoginPage(a_page).open().login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        admin = PickupsAdminPage(a_page)
        admin.assign_driver(pickup_number=pickup_id, driver_name="b2c driver")
        admin_ctx.close()

        # Step 3: Driver accepts pickup
        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)
        driver.open_active_pickups()

        driver.accept_pickup(pickup_number=pickup_id)

        # Step 4: Verify status transitions to Driver Accepted
        accepted_row = driver.find_pickup_row(pickup_number=pickup_id)
        assert "Driver Accepted" in accepted_row.inner_text(), "Pickup status should be 'Driver Accepted'"

        driver_ctx.close()

    @pytest.mark.regression
    def test_driver_reject_assigned_pickup(self, browser: Browser):
        """Driver rejects an assigned pickup and verifies rejection."""
        unique_id = int(time.time())
        order_ref = f"REF-REJ-{unique_id}"

        # Step 1: Merchant creates order & schedules pickup
        merchant_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        m_page = merchant_ctx.new_page()
        LoginPage(m_page).open().login(settings.MERCHANT_EMAIL, settings.MERCHANT_PASSWORD)
        merchant = MerchantPage(m_page)
        merchant.create_order(reference_number=order_ref, package_count=1, payment_method="Paid")
        merchant.open_pickups()
        merchant.select_order_checkbox_for_pickup(0)
        pickup_id = merchant.schedule_pickup()
        merchant_ctx.close()

        # Step 2: Tenant Admin assigns driver
        admin_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = admin_ctx.new_page()
        LoginPage(a_page).open().login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        admin = PickupsAdminPage(a_page)
        admin.assign_driver(pickup_number=pickup_id, driver_name="b2c driver")
        admin_ctx.close()

        # Step 3: Driver rejects pickup
        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)
        driver.open_active_pickups()

        driver.reject_pickup(pickup_number=pickup_id)

        # Step 4: Verify rejection
        assert "Pickup rejected successfully" in d_page.inner_text("body") or not driver.is_pickup_present(pickup_id)

        driver_ctx.close()

    @pytest.mark.e2e
    def test_full_lifecycle_driver_accept_and_proceed(self, browser: Browser):
        """
        Complete end-to-end integration:
        1. Merchant creates order and schedules pickup.
        2. Tenant Admin assigns to b2c driver.
        3. Driver accepts the assigned pickup.
        4. Driver proceeds to view pickup details, verifying merchant info, scheduled date, and order readiness.
        """
        unique_id = int(time.time())
        order_ref = f"REF-FULL-{unique_id}"

        # 1. Merchant creates order and schedules pickup
        m_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        m_page = m_ctx.new_page()
        LoginPage(m_page).open().login(settings.MERCHANT_EMAIL, settings.MERCHANT_PASSWORD)
        merchant = MerchantPage(m_page)
        merchant.create_order(reference_number=order_ref, package_count=1, payment_method="Paid")
        merchant.open_pickups()
        merchant.select_order_checkbox_for_pickup(0)
        pickup_id = merchant.schedule_pickup()
        assert pickup_id.startswith("PICK-")
        m_ctx.close()

        # 2. Tenant Admin assigns driver
        a_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = a_ctx.new_page()
        LoginPage(a_page).open().login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        admin = PickupsAdminPage(a_page)
        admin.assign_driver(pickup_number=pickup_id, driver_name="b2c driver")
        assert "Driver Assigned" in admin.get_pickup_status(pickup_id)
        a_ctx.close()

        # 3. Driver accepts the pickup
        d_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = d_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)
        driver.open_active_pickups()
        driver.accept_pickup(pickup_number=pickup_id)

        # 4. Driver proceeds with accepted pickup (View details)
        driver.view_pickup_details(pickup_number=pickup_id)
        details = driver.get_details_page_text()

        assert "Driver Accepted" in details
        assert "B2C Merchant" in details
        assert "Ready to Pick Up" in details

        d_ctx.close()
