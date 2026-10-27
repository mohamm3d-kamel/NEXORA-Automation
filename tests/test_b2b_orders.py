import time
import pytest
from playwright.sync_api import Page, BrowserContext
from config.settings import settings
from pages.b2b_orders_page import B2BOrdersPage
from pages.login_page import LoginPage

@pytest.mark.b2b
class TestB2BOrders:
    """Comprehensive test suite for B2B Order Management across Tenant Admin and Merchant portals."""

    # -------------------------------------------------------------------------
    # VALID SCENARIOS
    # -------------------------------------------------------------------------
    def test_valid_b2b_merchant_classification_restriction(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Verify only merchants with B2B classification can be selected for B2B order creation."""
        b2b_page = authenticated_b2b_admin
        merchant_names = b2b_page.get_b2b_merchant_options()

        # B2B Merchant must be present
        assert any("B2B Merchant" in m for m in merchant_names), (
            f"Expected 'B2B Merchant' in options, found: {merchant_names}"
        )

        # B2C-only merchants must NOT be present
        assert not any("b2c-merchant" in m.lower() for m in merchant_names), (
            f"B2C-only merchant found in B2B creation options: {merchant_names}"
        )
        assert not any("burger" in m.lower() for m in merchant_names), (
            f"B2C-only merchant 'Burger' found in B2B creation options: {merchant_names}"
        )

    def test_valid_tenant_create_b2b_order(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Tenant Admin creates a full B2B order and verifies it in Pending Requests."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-T-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(
            is_tenant=True,
            merchant_name="B2B Merchant",
            ref_num=ref_num,
        )

        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("Pending Requests")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None, f"Order {ref_num} not found in Pending Requests after Tenant creation!"
        row_text = row.inner_text()
        assert "Pending Operations Review" in row_text, f"Unexpected status in row: {row_text}"

    def test_valid_merchant_create_b2b_order(
        self,
        authenticated_b2b_merchant: B2BOrdersPage,
    ):
        """B2B Merchant creates a B2B order and verifies submission in Merchant portal."""
        b2b_page = authenticated_b2b_merchant
        ref_num = f"REF-B2B-M-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(
            is_tenant=False,
            ref_num=ref_num,
        )

        b2b_page.open_merchant_b2b()
        b2b_page.switch_tab("Pending Requests")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None, f"Order {ref_num} not found in Merchant Pending Requests!"
        row_text = row.inner_text()
        assert "Pending Operations Review" in row_text, f"Unexpected status in row: {row_text}"

    def test_valid_tenant_accept_order(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Tenant accepts an order from Pending Requests; verifies transition to To Assign (Scheduled)."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-ACC-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        b2b_page.accept_order(ref_num)

        # Verify moved to To Assign with status Scheduled
        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("To Assign")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None, f"Order {ref_num} not found in To Assign after acceptance!"
        row_text = row.inner_text()
        assert "Scheduled" in row_text, f"Expected Scheduled status, found: {row_text}"

    def test_valid_tenant_reject_order(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Tenant rejects an order from Pending Requests; verifies transition to Rejected by Operations."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-REJ-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        b2b_page.reject_order(ref_num, reason="Operational Constraint")

        # Verify moved to Rejected by Operations
        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("Rejected by Operations")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None, f"Order {ref_num} not found in Rejected by Operations!"
        row_text = row.inner_text()
        assert "Rejected by Operations" in row_text, f"Expected Rejected by Operations status, found: {row_text}"

    def test_valid_tenant_accept_with_delay_merchant_accepts(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
        page: Page,
    ):
        """Tenant accepts with delay -> Merchant approves in Awaiting My Approval -> Transitions to To Assign."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-DELACC-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        b2b_page.accept_with_delay(ref_num, reason="Operational Constraint", remarks="Pickup delay proposed")

        # Check in Awaiting Merchant Approval
        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("Awaiting Merchant Approval")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None, f"Order {ref_num} not found in Awaiting Merchant Approval!"
        order_code = b2b_page.get_order_code_from_row(row)

        # Merchant approves
        m_ctx = page.context.browser.new_context()
        m_page = m_ctx.new_page()
        try:
            LoginPage(m_page).open().login(settings.B2B_MERCHANT_EMAIL, settings.B2B_MERCHANT_PASSWORD)
            m_b2b = B2BOrdersPage(m_page)
            m_b2b.open_merchant_b2b()
            m_b2b.merchant_accept_delay(order_code)

            # Verify in Merchant To Assign
            m_b2b.open_merchant_b2b()
            m_b2b.switch_tab("To Assign")
            m_row = m_b2b.find_order_row(ref_num)
            assert m_row is not None, f"Order {ref_num} not in Merchant To Assign after delay acceptance!"
            assert "Scheduled" in m_row.inner_text()
        finally:
            m_ctx.close()

    def test_valid_tenant_accept_with_delay_merchant_rejects(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
        page: Page,
    ):
        """Tenant accepts with delay -> Merchant rejects delay -> Transitions to Rejected by Merchant."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-DELREJ-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        b2b_page.accept_with_delay(ref_num, reason="Operational Constraint", remarks="Delay proposed for rejection test")

        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("Awaiting Merchant Approval")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None, f"Order {ref_num} not found in Awaiting Merchant Approval!"
        order_code = b2b_page.get_order_code_from_row(row)

        # Merchant rejects delay
        m_ctx = page.context.browser.new_context()
        m_page = m_ctx.new_page()
        try:
            LoginPage(m_page).open().login(settings.B2B_MERCHANT_EMAIL, settings.B2B_MERCHANT_PASSWORD)
            m_b2b = B2BOrdersPage(m_page)
            m_b2b.open_merchant_b2b()
            m_b2b.merchant_reject_delay(order_code, remarks="Merchant cannot accommodate this delay")

            # Verify in Merchant Rejected by Merchant tab
            m_b2b.open_merchant_b2b()
            m_b2b.switch_tab("Rejected by Merchant")
            m_row = m_b2b.find_order_row(ref_num)
            assert m_row is not None, f"Order {ref_num} not in Merchant Rejected by Merchant tab!"
            assert "Schedule Rejected by Merchant" in m_row.inner_text() or "Rejected by Merchant" in m_row.inner_text()
        finally:
            m_ctx.close()

    def test_valid_tenant_assign_driver(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Tenant assigns driver to an order in To Assign; verifies transition to In Progress (Driver Assigned)."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-DRV-{int(time.time() * 1000) % 10000000}"

        # 1. Create and accept order to move to To Assign
        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        b2b_page.accept_order(ref_num)

        # 2. Assign driver
        b2b_page.open_admin_b2b()
        b2b_page.assign_driver(ref_num, driver_name="B2C and B2B driver")

        # 3. Verify in In Progress
        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("In Progress")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None, f"Order {ref_num} not found in In Progress after driver assignment!"
        row_text = row.inner_text()
        assert "Driver Assigned" in row_text, f"Expected Driver Assigned status, found: {row_text}"
        assert "B2C and B2B driver" in row_text, f"Expected driver name in row, found: {row_text}"

    def test_valid_tenant_delete_b2b_order(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Tenant deletes a B2B order from Pending Requests; verifies removal."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-DEL-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        b2b_page.delete_order(ref_num)

        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("Pending Requests")
        row = b2b_page.find_order_row(ref_num)
        assert row is None, f"Order {ref_num} still present in Pending Requests after delete!"

    # -------------------------------------------------------------------------
    # INVALID / NEGATIVE SCENARIOS
    # -------------------------------------------------------------------------
    def test_invalid_b2b_creation_missing_required_fields(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Click Next on empty creation form triggers mandatory field validations."""
        b2b_page = authenticated_b2b_admin
        b2b_page.open_admin_create_form()
        next_btn = b2b_page.page.locator("button:has-text('Next')").first
        next_btn.click()
        b2b_page.page.wait_for_timeout(1500)

        # Validation errors or loading type notification should block progression
        is_blocked = (
            b2b_page.page.locator(".ant-form-item-explain-error").count() > 0
            or b2b_page.page.locator(".ant-notification").count() > 0
            or "form" in b2b_page.page.url
        )
        assert is_blocked, "Form unexpectedly allowed step progression without required fields!"

    def test_invalid_tenant_reject_without_reason(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Reject drawer blocks submission when reason is not selected."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-INVREJ-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        is_error = b2b_page.attempt_tenant_reject_without_reason(ref_num)
        assert is_error, "Reject request unexpectedly submitted without reason!"

        # Order must still remain in Pending Requests
        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("Pending Requests")
        assert b2b_page.find_order_row(ref_num) is not None

    def test_invalid_merchant_reject_without_remarks(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
        page: Page,
    ):
        """Merchant Reject modal requires remarks before allowing rejection of proposed delay."""
        b2b_page = authenticated_b2b_admin
        ref_num = f"REF-B2B-INVREM-{int(time.time() * 1000) % 10000000}"

        b2b_page.create_b2b_order(ref_num=ref_num)
        b2b_page.open_admin_b2b()
        b2b_page.accept_with_delay(ref_num, reason="Operational Constraint", remarks="Delay for remarks test")

        b2b_page.open_admin_b2b()
        b2b_page.switch_tab("Awaiting Merchant Approval")
        row = b2b_page.find_order_row(ref_num)
        assert row is not None
        order_code = b2b_page.get_order_code_from_row(row)

        m_ctx = page.context.browser.new_context()
        m_page = m_ctx.new_page()
        try:
            LoginPage(m_page).open().login(settings.B2B_MERCHANT_EMAIL, settings.B2B_MERCHANT_PASSWORD)
            m_b2b = B2BOrdersPage(m_page)
            m_b2b.open_merchant_b2b()
            is_blocked = m_b2b.attempt_merchant_reject_without_remarks(order_code)
            assert is_blocked, "Merchant reject submitted without required remarks!"
        finally:
            m_ctx.close()

    # -------------------------------------------------------------------------
    # EDGE SCENARIOS
    # -------------------------------------------------------------------------
    def test_edge_b2b_status_tab_cycling(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Cycle across all visible B2B status tabs, confirming stable rendering and no crashes."""
        b2b_page = authenticated_b2b_admin
        b2b_page.open_admin_b2b()

        tab_names = b2b_page.get_tab_names()
        assert len(tab_names) >= 6, f"Expected at least 6 status tabs, found: {tab_names}"

        for tab in tab_names:
            b2b_page.switch_tab(tab)
            # Table or empty state container must exist
            assert b2b_page.page.locator(".ant-table, .ant-empty").first.is_visible(), (
                f"Tab '{tab}' failed to render table container!"
            )

    def test_edge_cancel_creation_form_preserves_list(
        self,
        authenticated_b2b_admin: B2BOrdersPage,
    ):
        """Opening creation form and clicking Cancel safely returns to /orders/b2b."""
        b2b_page = authenticated_b2b_admin
        b2b_page.open_admin_create_form()
        cancel_btn = b2b_page.page.locator("button:has-text('Cancel')").first
        cancel_btn.click()
        b2b_page.page.wait_for_timeout(2000)

        assert "/orders/b2b" in b2b_page.page.url
        assert b2b_page.page.locator(".ant-tabs").first.is_visible()
