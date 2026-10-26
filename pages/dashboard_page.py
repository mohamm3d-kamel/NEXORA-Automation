from typing import List
from playwright.sync_api import Page, Locator, expect
from pages.base_page import BasePage
from config.settings import settings

class DashboardPage(BasePage):
    """Page Object for Nexora Admin Dashboard."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.get_dashboard_url()

        # Header elements
        self.welcome_header: Locator = page.locator("text='Welcome back, Tenant Admin'")
        self.search_input: Locator = page.locator("input[placeholder*='shipment' i]")
        self.language_selector: Locator = page.locator("header button:has-text('English')")
        self.notification_bell: Locator = page.locator(".anticon-bell")
        self.avatar_button: Locator = page.get_by_role("button", name="Tenant Admin")
        self.avatar_initials: Locator = page.locator("header").get_by_text("TT")

        # Dropdown items
        self.profile_menu_item: Locator = page.get_by_text("Profile")
        self.logout_menu_item: Locator = page.get_by_text("Logout")

        # Sidebar navigation
        self.sidebar: Locator = page.locator("aside")

    def wait_until_loaded(self) -> "DashboardPage":
        """Wait until dashboard is fully rendered and authenticated."""
        self.wait_for_url("**/dashboard", timeout=settings.DEFAULT_TIMEOUT)
        self.welcome_header.wait_for(state="visible", timeout=settings.DEFAULT_TIMEOUT)
        return self

    def is_dashboard_visible(self) -> bool:
        """Returns True if the welcome header and avatar are displayed."""
        return self.is_visible(self.welcome_header) and (
            self.is_visible(self.avatar_button) or self.is_visible(self.avatar_initials)
        )

    def open_profile_dropdown(self) -> None:
        """Click user avatar to open profile/logout dropdown."""
        if self.avatar_button.is_visible():
            self.avatar_button.click()
        else:
            self.avatar_initials.click()
        self.page.wait_for_timeout(500)

    def logout(self) -> None:
        """Execute user logout flow."""
        self.open_profile_dropdown()
        self.logout_menu_item.wait_for(state="visible", timeout=settings.DEFAULT_TIMEOUT)
        self.logout_menu_item.click()
        self.wait_for_url("**/login", timeout=settings.DEFAULT_TIMEOUT)

    def get_sidebar_menu_text(self) -> str:
        """Retrieve full text of the navigation sidebar."""
        self.sidebar.wait_for(state="visible", timeout=settings.DEFAULT_TIMEOUT)
        return self.sidebar.inner_text()

    def is_kpi_card_visible(self, card_title: str) -> bool:
        """Check if a specific KPI widget / stat card is displayed on the dashboard."""
        card_locator = self.page.get_by_text(card_title, exact=False).first
        return self.is_visible(card_locator)
