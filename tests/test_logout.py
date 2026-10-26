import pytest
from playwright.sync_api import Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage

@pytest.mark.logout
class TestLogout:
    """Test suite covering user logout and session termination."""

    @pytest.mark.smoke
    def test_user_logout_success(self, authenticated_dashboard: DashboardPage, login_page: LoginPage, page: Page):
        """Verify user can log out from the header profile dropdown."""
        authenticated_dashboard.logout()

        assert "/login" in page.url, f"Expected redirect to login page, but got {page.url}"
        assert login_page.is_login_page_loaded(), "Login page form was not displayed after logout"

    @pytest.mark.regression
    def test_dashboard_inaccessible_after_logout(self, authenticated_dashboard: DashboardPage, login_page: LoginPage, page: Page):
        """Verify that navigating to dashboard URL after logout redirects back to login."""
        authenticated_dashboard.logout()

        # Attempt to navigate directly back to the protected dashboard URL
        page.goto(settings.get_dashboard_url(), wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Assert unauthorized access redirects to login
        assert "/login" in page.url, f"Expected redirect to login page when unauthenticated, got: {page.url}"
        assert login_page.is_login_page_loaded(), "Login page should be rendered for unauthenticated session"
