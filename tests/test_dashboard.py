import pytest
from playwright.sync_api import Page, expect
from pages.dashboard_page import DashboardPage
from utils.test_data import NavigationItems, DashboardKPIs

@pytest.mark.dashboard
class TestDashboard:
    """Test suite covering post-login Dashboard view and navigation."""

    @pytest.mark.smoke
    def test_dashboard_welcome_and_header(self, authenticated_dashboard: DashboardPage, page: Page):
        """Verify dashboard header components: greeting, avatar, search input."""
        expect(authenticated_dashboard.welcome_header).to_be_visible()
        expect(authenticated_dashboard.search_input).to_be_visible()
        assert authenticated_dashboard.is_dashboard_visible(), "Dashboard header elements missing"

    @pytest.mark.regression
    def test_sidebar_navigation_menus(self, authenticated_dashboard: DashboardPage):
        """Verify that all main sidebar navigation menu items are rendered."""
        sidebar_text = authenticated_dashboard.get_sidebar_menu_text()
        for menu in NavigationItems.SIDEBAR_MENUS:
            assert menu in sidebar_text, f"Sidebar menu item '{menu}' not found in navigation"

    @pytest.mark.regression
    def test_kpi_summary_cards_visible(self, authenticated_dashboard: DashboardPage):
        """Verify key performance indicator (KPI) metric cards render on dashboard."""
        for kpi in DashboardKPIs.EXPECTED_CARDS:
            assert authenticated_dashboard.is_kpi_card_visible(kpi), f"KPI card '{kpi}' not visible on dashboard"
