import pytest
from playwright.sync_api import Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from utils.test_data import ValidationMessages

@pytest.mark.login
class TestLogin:
    """Test suite covering authentication scenarios on the Nexora login page."""

    @pytest.mark.smoke
    def test_login_page_renders_properly(self, login_page: LoginPage, page: Page):
        """Verify login page loads with expected title and interactive elements."""
        login_page.open()

        expect(page).to_have_title("n3xora")
        assert login_page.is_login_page_loaded(), "Login page form inputs are not visible"
        assert login_page.register_button.is_visible(), "Register button should be visible"
        assert login_page.language_button.is_visible(), "Language button should be visible"

    @pytest.mark.smoke
    def test_successful_login(self, login_page: LoginPage, dashboard_page: DashboardPage, page: Page):
        """Verify successful login with valid credentials redirects to dashboard."""
        login_page.open()
        login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)

        dashboard_page.wait_until_loaded()
        assert "/dashboard" in page.url, f"Expected dashboard URL, got {page.url}"
        assert dashboard_page.is_dashboard_visible(), "Dashboard welcome header/avatar not visible"

    def test_login_empty_credentials_validation(self, login_page: LoginPage):
        """Verify validation errors appear when submitting empty login form."""
        login_page.open()
        login_page.click_login()

        errors = login_page.get_field_errors()
        assert ValidationMessages.EMAIL_REQUIRED in errors, f"Expected '{ValidationMessages.EMAIL_REQUIRED}' in {errors}"
        assert ValidationMessages.PASSWORD_REQUIRED in errors, f"Expected '{ValidationMessages.PASSWORD_REQUIRED}' in {errors}"

    def test_login_empty_password_only(self, login_page: LoginPage):
        """Verify validation error when email is provided but password is empty."""
        login_page.open()
        login_page.enter_email(settings.TEST_USER_EMAIL)
        login_page.click_login()

        errors = login_page.get_field_errors()
        assert ValidationMessages.PASSWORD_REQUIRED in errors, f"Expected '{ValidationMessages.PASSWORD_REQUIRED}' in {errors}"
        assert ValidationMessages.EMAIL_REQUIRED not in errors

    def test_login_empty_email_only(self, login_page: LoginPage):
        """Verify validation error when password is provided but email is empty."""
        login_page.open()
        login_page.enter_password(settings.TEST_USER_PASSWORD)
        login_page.click_login()

        errors = login_page.get_field_errors()
        assert ValidationMessages.EMAIL_REQUIRED in errors, f"Expected '{ValidationMessages.EMAIL_REQUIRED}' in {errors}"
        assert ValidationMessages.PASSWORD_REQUIRED not in errors

    @pytest.mark.regression
    def test_login_invalid_credentials(self, login_page: LoginPage, page: Page):
        """Verify error message is displayed when invalid credentials are provided."""
        login_page.open()
        login_page.login("invalid_tester_user@n3xora.com", "WrongPassword999!", expect_success=False)

        assert login_page.is_invalid_credentials_error_visible(), "Invalid credentials error message did not appear"
        assert "/login" in page.url, "User should remain on login page after failed authentication"

    @pytest.mark.regression
    def test_login_wrong_password(self, login_page: LoginPage, page: Page):
        """Verify error handling when correct email is paired with wrong password."""
        login_page.open()
        login_page.login(settings.TEST_USER_EMAIL, "IncorrectPass123!", expect_success=False)

        assert login_page.is_invalid_credentials_error_visible(), "Invalid credentials message expected"
        assert "/login" in page.url
