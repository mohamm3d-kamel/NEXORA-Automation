"""Reusable test data constants and expected assertions."""

class ValidationMessages:
    EMAIL_REQUIRED = "Email is required"
    PASSWORD_REQUIRED = "Password is required"
    INVALID_CREDENTIALS = "Invalid credentials"
    LOGIN_FAILED = "Login failed"

class NavigationItems:
    SIDEBAR_MENUS = [
        "Dashboard",
        "Orders",
        "Reports",
        "Process Management",
        "Finance",
        "Manifests",
        "SLA",
        "Tickets",
        "Shipment Labels",
        "Settings",
    ]

class DashboardKPIs:
    EXPECTED_CARDS = [
        "New Orders",
        "Picked Orders",
        "In Warehouse",
        "Ready For Delivery",
        "Out for Delivery",
        "Delivered",
        "Not Delivered",
        "Delivery Rate",
        "Failed Rate",
        "SLA Breach",
        "Cash Pending Collection",
    ]
