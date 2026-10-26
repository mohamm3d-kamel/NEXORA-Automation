"""Page Object Model (POM) classes for Nexora."""
from pages.base_page import BasePage
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

__all__ = [
    "BasePage",
    "LoginPage",
    "DashboardPage",
    "OrdersPage",
    "MerchantPage",
    "PickupsAdminPage",
    "DriverPage",
    "ProcessManagementPage",
    "AccountingPage",
    "SlaPage",
    "ReportsPage",
]
