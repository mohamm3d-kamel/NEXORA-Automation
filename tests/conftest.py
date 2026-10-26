from pathlib import Path
import os
from typing import Dict, Any, Callable
import pytest
from playwright.sync_api import Page, Browser, BrowserContext
from config.settings import settings
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from pages.orders_page import OrdersPage
from pages.merchant_page import MerchantPage
from pages.pickups_admin_page import PickupsAdminPage
from pages.driver_page import DriverPage
from pages.process_management_page import ProcessManagementPage
from pages.accounting_page import AccountingPage
from pages.sla_page import SlaPage
from pages.reports_page import ReportsPage
from pages.manifests_page import ManifestsPage
from pages.tickets_page import TicketsPage

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: Dict[str, Any]):
    """Ensure the browser is launched maximized to fit the screen."""
    res = settings.get_screen_dimensions()
    current_args = list(browser_type_launch_args.get("args", [])) if browser_type_launch_args else []
    return {
        **browser_type_launch_args,
        "args": [
            *current_args,
            "--start-maximized",
            f"--window-size={res['width']},{res['height']}",
        ],
    }

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: Dict[str, Any]):
    """Configure browser context defaults to fit the screen and ignore SSL errors."""
    res = settings.get_screen_dimensions()
    return {
        **browser_context_args,
        "viewport": {"width": res["width"], "height": res["height"]},
        "ignore_https_errors": True,
    }

@pytest.fixture(autouse=True)
def configure_screen_fit_and_zoom(page: Page):
    """Automatically enforce screen fit and 67% zoom across all test pages."""
    res = settings.get_screen_dimensions()
    try:
        page.set_viewport_size({"width": res["width"], "height": res["height"]})
    except Exception:
        pass
    try:
        page.context.add_init_script("""
            function applyZoom() {
                if (document.documentElement) document.documentElement.style.zoom = '67%';
                if (document.body) document.body.style.zoom = '67%';
            }
            applyZoom();
            window.addEventListener('DOMContentLoaded', applyZoom);
            window.addEventListener('load', applyZoom);
        """)
    except Exception:
        pass
    yield page

@pytest.fixture
def create_fitted_context():
    """Factory fixture to create secondary multi-role contexts fitted to screen with 67% zoom."""
    created_contexts = []

    def _create(browser: Browser, **kwargs) -> BrowserContext:
        res = settings.get_screen_dimensions()
        ctx_args = {
            "viewport": {"width": res["width"], "height": res["height"]},
            "ignore_https_errors": True,
            **kwargs,
        }
        ctx = browser.new_context(**ctx_args)
        ctx.add_init_script("""
            function applyZoom() {
                if (document.documentElement) document.documentElement.style.zoom = '67%';
                if (document.body) document.body.style.zoom = '67%';
            }
            applyZoom();
            window.addEventListener('DOMContentLoaded', applyZoom);
            window.addEventListener('load', applyZoom);
        """)
        created_contexts.append(ctx)
        return ctx

    yield _create

    for c in created_contexts:
        try:
            c.close()
        except Exception:
            pass

@pytest.fixture
def login_page(page: Page) -> LoginPage:
    """Fixture to provide an initialized LoginPage instance."""
    return LoginPage(page)

@pytest.fixture
def dashboard_page(page: Page) -> DashboardPage:
    """Fixture to provide an initialized DashboardPage instance."""
    return DashboardPage(page)

@pytest.fixture
def orders_page(page: Page) -> OrdersPage:
    """Fixture to provide an initialized OrdersPage instance."""
    return OrdersPage(page)

@pytest.fixture
def merchant_page(page: Page) -> MerchantPage:
    """Fixture to provide an initialized MerchantPage instance."""
    return MerchantPage(page)

@pytest.fixture
def pickups_admin_page(page: Page) -> PickupsAdminPage:
    """Fixture to provide an initialized PickupsAdminPage instance."""
    return PickupsAdminPage(page)

@pytest.fixture
def driver_page(page: Page) -> DriverPage:
    """Fixture to provide an initialized DriverPage instance."""
    return DriverPage(page)

@pytest.fixture
def process_management_page(page: Page) -> ProcessManagementPage:
    """Fixture to provide an initialized ProcessManagementPage instance."""
    return ProcessManagementPage(page)

@pytest.fixture
def accounting_page(page: Page) -> AccountingPage:
    """Fixture to provide an initialized AccountingPage instance."""
    return AccountingPage(page)

@pytest.fixture
def sla_page(page: Page) -> SlaPage:
    """Fixture to provide an initialized SlaPage instance."""
    return SlaPage(page)

@pytest.fixture
def reports_page(page: Page) -> ReportsPage:
    """Fixture to provide an initialized ReportsPage instance."""
    return ReportsPage(page)

@pytest.fixture
def manifests_page(page: Page) -> ManifestsPage:
    """Fixture to provide an initialized ManifestsPage instance."""
    return ManifestsPage(page)

@pytest.fixture
def tickets_page(page: Page) -> TicketsPage:
    """Fixture to provide an initialized TicketsPage instance."""
    return TicketsPage(page)

@pytest.fixture
def proof_file_path() -> str:
    """Path to the dummy proof asset for cash transfer submissions."""
    asset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets", "dummy_proof.png"))
    if not os.path.exists(asset_path):
        os.makedirs(os.path.dirname(asset_path), exist_ok=True)
        with open(asset_path, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82')
    return asset_path

@pytest.fixture
def authenticated_merchant(page: Page, login_page: LoginPage, merchant_page: MerchantPage) -> MerchantPage:
    """Fixture that logs in as B2C Merchant and yields MerchantPage."""
    login_page.open()
    login_page.login(settings.MERCHANT_EMAIL, settings.MERCHANT_PASSWORD)
    merchant_page.open_dashboard()
    return merchant_page

@pytest.fixture
def authenticated_driver(page: Page, login_page: LoginPage, driver_page: DriverPage) -> DriverPage:
    """Fixture that logs in as Driver and yields DriverPage."""
    login_page.open()
    login_page.login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
    driver_page.open_active_pickups()
    return driver_page

@pytest.fixture
def authenticated_dashboard(page: Page, login_page: LoginPage, dashboard_page: DashboardPage) -> DashboardPage:
    """Fixture that completes login and yields a loaded DashboardPage."""
    login_page.open()
    login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
    dashboard_page.wait_until_loaded()
    return dashboard_page

@pytest.fixture
def authenticated_accounting(page: Page, login_page: LoginPage, accounting_page: AccountingPage) -> AccountingPage:
    """Fixture that completes admin login and opens Accounting COD collection."""
    login_page.open()
    login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
    accounting_page.open_cod_collection()
    return accounting_page

@pytest.fixture
def authenticated_sla(page: Page, login_page: LoginPage, sla_page: SlaPage) -> SlaPage:
    """Fixture that completes admin login and opens SLA Order Rules."""
    login_page.open()
    login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
    sla_page.open_rules("order")
    return sla_page

@pytest.fixture
def authenticated_reports(page: Page, login_page: LoginPage, reports_page: ReportsPage) -> ReportsPage:
    """Fixture that completes admin login and opens Shipment Reports."""
    login_page.open()
    login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
    reports_page.open_shipment_reports()
    return reports_page

@pytest.fixture
def authenticated_manifests(page: Page, login_page: LoginPage, manifests_page: ManifestsPage) -> ManifestsPage:
    """Fixture that completes admin login and opens Delivery Manifests."""
    login_page.open()
    login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
    manifests_page.open_delivery_manifests()
    return manifests_page

@pytest.fixture
def authenticated_tickets(page: Page, login_page: LoginPage, tickets_page: TicketsPage) -> TicketsPage:
    """Fixture that completes admin login and opens Tickets management."""
    login_page.open()
    login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
    tickets_page.open_tickets()
    return tickets_page

@pytest.fixture
def authenticated_orders(page: Page, login_page: LoginPage, orders_page: OrdersPage) -> OrdersPage:
    """Fixture that completes admin login and opens Orders management."""
    login_page.open()
    login_page.login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
    orders_page.open()
    return orders_page

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture a screenshot on test failure and save to screenshots/ directory."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page_fixture = item.funcargs.get("page", None)
        if page_fixture:
            screenshots_dir = Path("reports/screenshots")
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshots_dir / f"{item.name}.png"
            try:
                page_fixture.screenshot(path=str(screenshot_path), full_page=True)
                print(f"\n[Screenshot captured]: {screenshot_path}")
            except Exception as e:
                print(f"\nFailed to capture screenshot: {e}")
