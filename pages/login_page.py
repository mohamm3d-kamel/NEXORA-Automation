from typing import List
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from config.settings import settings

class LoginPage(BasePage):
    """Page Object for Nexora Login Page."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.get_login_url()

        # Locators
        self.email_input: Locator = page.locator("input[name='email']")
        self.password_input: Locator = page.locator("input[name='passwordHash']")
        self.login_button: Locator = page.locator("button[type='submit']")
        self.register_button: Locator = page.locator("button:has-text('Register')")
        self.forgot_password_button: Locator = page.locator("button:has-text('Forgot Your Password'), a:has-text('Forgot Your Password')")
        self.language_button: Locator = page.locator("button:has-text('English')")
        self.validation_errors: Locator = page.locator(".ant-form-item-explain-error")
        self.error_alert: Locator = page.locator("text='Login failed'")
        self.invalid_credentials_message: Locator = page.locator("text='Invalid credentials'")
        self.password_visibility_toggle: Locator = page.locator(".ant-input-password-icon, .anticon-eye, .anticon-eye-invisible")

    def open(self) -> "LoginPage":
        """Navigate to the Nexora login page."""
        self.navigate(self.url)
        return self

    def enter_email(self, email: str) -> "LoginPage":
        """Type email into email field."""
        self.fill(self.email_input, email)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        """Type password into password field."""
        self.fill(self.password_input, password)
        return self

    def click_login(self) -> None:
        """Click the Login submit button."""
        self.click(self.login_button)

    def login(self, email: str, password: str, expect_success: bool = True) -> None:
        """Perform a full login action with given credentials."""
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()
        if expect_success:
            try:
                self.page.wait_for_url("**/dashboard", timeout=self.default_timeout)
            except Exception:
                pass
        else:
            self.page.wait_for_timeout(2000)

    def get_field_errors(self) -> List[str]:
        """Return list of inline form field validation error texts."""
        self.page.wait_for_timeout(500)
        return [err.strip() for err in self.validation_errors.all_inner_texts() if err.strip()]

    def is_invalid_credentials_error_visible(self, timeout: int = 5000) -> bool:
        """Check if invalid credentials error appears."""
        return self.is_visible(self.invalid_credentials_message, timeout=timeout) or \
               self.is_visible(self.error_alert, timeout=timeout)

    def is_login_page_loaded(self, timeout: int = 5000) -> bool:
        """Check if primary login page elements are visible."""
        try:
            self.email_input.wait_for(state="visible", timeout=timeout)
            self.password_input.wait_for(state="visible", timeout=timeout)
            self.login_button.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False
