# Nexora Web App Automation Testing Framework

An enterprise-grade, scalable End-to-End (E2E) automation testing framework designed for the **Nexora** web application (`https://staging.app.n3xora.net`).

Built with **Python 3.12**, **Playwright**, and **pytest**, implementing the **Page Object Model (POM)** architectural design pattern.

---

## 🏗️ Architecture Overview

The framework separates test logic, page interactions, configuration, and test data into decoupled layers:

```
NEXORA-Automation/
├── .env                         # Local environment variables & secrets
├── .env.example                 # Example configuration template
├── .gitignore                   # Git ignore rules
├── pytest.ini                   # Pytest configuration, flags, and markers
├── requirements.txt             # Project Python dependencies
├── README.md                    # Project documentation
│
├── config/                      # Environment & global framework settings
│   ├── __init__.py
│   └── settings.py              # Strongly-typed configuration loaded from .env
│
├── pages/                       # Page Object Model (POM) representations
│   ├── __init__.py
│   ├── base_page.py             # Reusable UI actions, waits, and assertions
│   ├── login_page.py            # Nexora Login page locators and user actions
│   ├── dashboard_page.py        # Nexora Dashboard header, sidebar, and KPI cards
│   ├── orders_page.py           # Orders list & multi-step Order Creation Wizard
│   ├── merchant_page.py         # Merchant dashboard, orders, and pickup scheduling
│   ├── pickups_admin_page.py    # Tenant Admin pickups list & driver assignment
│   ├── driver_page.py           # Driver active pickups, Today's Manifest, deliver/fail modals
│   ├── process_management_page.py # Process Management warehouse scanning & dispatch
│   ├── accounting_page.py       # Accounting, COD Collection, Manifest Closure & Cash Transfer
│   ├── sla_page.py              # Service Level Agreement (Rules, Tracking, Rematch)
│   ├── reports_page.py          # Reports (Shipment, Performance, Finance, Query Builder, Export)
│   └── manifests_page.py        # Delivery & Pickup Manifests, Intra-Hub, Return & Pickups page objects
│
├── tests/                       # Pytest test suites
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and failure screenshot hooks
│   ├── assets/                  # Test fixture assets (e.g. proof of transfer)
│   ├── test_login.py            # Authentication, validation, and error handling tests
│   ├── test_dashboard.py        # Dashboard KPIs and sidebar navigation tests
│   ├── test_logout.py           # Session termination and authorization redirect tests
│   ├── test_orders.py           # Orders creation (Cash/Paid, 1-N packages, validations)
│   ├── test_merchant_lifecycle.py # End-to-end Merchant -> Admin -> Driver lifecycle tests
│   ├── test_driver_actions.py   # Driver accept/reject and pickup progression tests
│   ├── test_driver_delivery.py  # Driver order delivery, failure recording & FDR tests
│   ├── test_finance_accounting_cod.py # Finance & Accounting COD collection, closure & cash transfer tests
│   ├── test_sla.py              # SLA module rules, tracking, rematch & validation tests
│   ├── test_reports.py          # Reports module generation, preview, export & format tests
│   └── test_manifests.py        # Delivery & Pickup Manifests, detail view, export & validation tests
│
├── utils/                       # Common helpers and constants
│   ├── __init__.py
│   └── test_data.py             # Validation messages, menu items, and KPI card titles
│
└── reports/                     # Test execution outputs
    ├── test-report.html         # Self-contained HTML test report
    └── screenshots/             # Automatically captured screenshots on failures
```

---

## 📋 Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **PowerShell / Bash** terminal

---

## 🚀 Getting Started

### 1. Clone & Setup Virtual Environment

```powershell
# Navigate to the workspace
cd d:\N3XORA\NEXORA-Automation

# Create Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate
```

### 2. Install Dependencies & Playwright Browsers

```powershell
# Upgrade pip and install required packages
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 3. Configure Environment Variables

Verify or customize `.env`:

```ini
BASE_URL=https://staging.app.n3xora.net
LOGIN_PATH=/ttenant/login
DASHBOARD_PATH=/tenant/ttenant/admin/dashboard

# Tenant Admin Credentials
TEST_USER_EMAIL=ttenant@gmail.com
TEST_USER_PASSWORD=12345678

# Merchant Credentials
MERCHANT_EMAIL=b2c@merchant.com
MERCHANT_PASSWORD=123456789

# Driver Credentials
DRIVER_EMAIL=b2c@driver.com
DRIVER_PASSWORD=12345678

HEADLESS=true
BROWSER=chromium
DEFAULT_TIMEOUT=30000
DEFAULT_ZOOM=67%
```

---

## 🖥️ Screen Fit & Zoom (67%)

- **Automatic Screen Fit**: The framework dynamically queries the host display resolution (`user32` DPI-aware) and launches Chromium with `--start-maximized` and `--window-size=<width>,<height>`, matching the full viewport size across all single- and multi-role contexts.
- **67% Zoom**: Enforced via Playwright `add_init_script` and reinforced on every navigation in [`BasePage`](file:///d:/N3XORA/NEXORA-Automation/pages/base_page.py). This ensures that dense Ant Design tables, KPI cards, sidebar navigation, and multi-step modals scale down to 67%, preventing horizontal overflow or truncated elements.

---

## 🧪 Running Tests

### Run Full Test Suite

```powershell
pytest
```

### Run in Headed Mode (Watch Browser Execution)

```powershell
pytest --headed --slowmo 500
```

### Run Tests in Parallel (Multi-threaded)

```powershell
pytest -n auto
# Or specify worker count:
pytest -n 2
```

### Run Specific Test Suites by Marker

```powershell
# Run smoke tests only
pytest -m smoke

# Run regression tests only
pytest -m regression

# Run finance & accounting tests only
pytest -m accounting
pytest -m finance

# Run SLA (Service Level Agreement) tests only
pytest -m sla

# Run Reports module tests only
pytest -m reports

# Run Manifests (Delivery & Pickups) tests only
pytest -m manifests

# Run authentication/login tests only
pytest -m login

# Run dashboard tests only
pytest -m dashboard

# Run logout tests only
pytest -m logout

# Run orders tests only
pytest -m orders

# Run merchant lifecycle tests only
pytest -m merchant

# Run pickup assignment tests only
pytest -m pickups

# Run driver portal & delivery tests only
pytest -m driver

# Run full cross-role E2E tests only
pytest -m e2e
```

### Run a Specific Test File

```powershell
pytest tests/test_login.py
pytest tests/test_dashboard.py
pytest tests/test_logout.py
pytest tests/test_orders.py
pytest tests/test_merchant_lifecycle.py
pytest tests/test_driver_actions.py
pytest tests/test_driver_delivery.py
pytest tests/test_finance_accounting_cod.py
pytest tests/test_sla.py
pytest tests/test_reports.py
pytest tests/test_manifests.py
```

---

## 📊 Test Reports & Failure Artifacts

- **HTML Report**: Automatically generated on every test run at `reports/test-report.html`. Open it in any browser:
  ```powershell
  Start-Process reports/test-report.html
  ```
- **Automatic Failure Screenshots**: If any assertion or interaction fails, the `pytest_runtest_makereport` hook captures a full-page screenshot in `reports/screenshots/<test_name>.png`.

---

## 🧩 Test Coverage Details (90 Automated Tests)

| Module | Test Case | Description | Marker |
|---|---|---|---|
| `test_login.py` | `test_login_page_renders_properly` | Validates page title and presence of email, password inputs, buttons | `smoke`, `login` |
| `test_login.py` | `test_successful_login` | Authenticates with valid tenant credentials and verifies redirect to `/dashboard` | `smoke`, `login` |
| `test_login.py` | `test_login_empty_credentials_validation` | Validates "Email is required" and "Password is required" on empty submit | `login` |
| `test_login.py` | `test_login_empty_password_only` | Validates "Password is required" error when only email is typed | `login` |
| `test_login.py` | `test_login_empty_email_only` | Validates "Email is required" error when only password is typed | `login` |
| `test_login.py` | `test_login_invalid_credentials` | Asserts `401` response, "Invalid credentials" error alert, and prevents login | `regression`, `login` |
| `test_login.py` | `test_login_wrong_password` | Asserts "Invalid credentials" error when given incorrect password | `regression`, `login` |
| `test_dashboard.py` | `test_dashboard_welcome_and_header` | Verifies "Welcome back, Tenant Admin", avatar, and search input | `smoke`, `dashboard` |
| `test_dashboard.py` | `test_sidebar_navigation_menus` | Verifies all 10 sidebar links (Orders, Reports, Finance, SLA, etc.) | `regression`, `dashboard` |
| `test_dashboard.py` | `test_kpi_summary_cards_visible` | Validates core KPI widgets (New Orders, Delivery Rate, Cash Pending, etc.) | `regression`, `dashboard` |
| `test_logout.py` | `test_user_logout_success` | Verifies profile menu logout terminates session and returns to login page | `smoke`, `logout` |
| `test_logout.py` | `test_dashboard_inaccessible_after_logout` | Asserts unauthenticated access to `/dashboard` redirects back to `/login` | `regression`, `logout` |
| `test_orders.py` | `test_create_order_single_package_cash` | Creates 1-package order with Cash (COD), asserts order created in list | `smoke`, `orders` |
| `test_orders.py` | `test_create_order_multiple_packages_cash` | Creates multi-package (3) order with Cash, asserts 3 package cards & submission | `regression`, `orders` |
| `test_orders.py` | `test_create_order_single_package_paid` | Creates 1-package order with Paid (prepaid), Total Amount hidden, asserts submission | `smoke`, `orders` |
| `test_orders.py` | `test_create_order_multiple_packages_paid` | Creates multi-package (2) order with Paid, asserts submission in list | `regression`, `orders` |
| `test_orders.py` | `test_payment_method_dynamic_fields_toggle` | Verifies switching Cash -> Paid hides Total Amount, and switching back reveals it | `regression`, `orders` |
| `test_orders.py` | `test_package_count_dynamically_renders_sections` | Verifies dynamic package section rendering when changing package count | `regression`, `orders` |
| `test_orders.py` | `test_validation_empty_merchant_step1` | Asserts validation error when clicking Next without selecting a merchant | `regression`, `orders` |
| `test_orders.py` | `test_validation_empty_consignee_step2` | Asserts required field validation errors when clicking Next with empty consignee | `regression`, `orders` |
| `test_orders.py` | `test_valid_download_order_template_csv` | Downloads spreadsheet template from modal, asserts filename `Order_Template.csv` and header schema | `smoke`, `valid`, `orders` |
| `test_orders.py` | `test_valid_bulk_order_creation_end_to_end` | E2E bulk import: uploads CSV ➔ advances to review ➔ selects merchant ➔ submits batch ➔ verifies `System Bulk` orders created | `smoke`, `valid`, `orders` |
| `test_orders.py` | `test_invalid_bulk_import_empty_file_next_disabled` | Asserts `Next` button is strictly disabled on import modal until file is attached | `regression`, `invalid`, `orders` |
| `test_orders.py` | `test_invalid_bulk_review_create_orders_disabled_without_merchant` | Asserts `Create Orders` button remains disabled on review page when merchant is unselected | `regression`, `invalid`, `orders` |
| `test_orders.py` | `test_edge_bulk_import_modal_cancel_preserves_orders_list` | Attaches file in import modal and clicks Cancel; asserts modal closes and orders table preserved | `regression`, `edge`, `orders` |
| `test_orders.py` | `test_edge_bulk_review_cancel_redirects_to_orders` | Advances to Review page, clicks Cancel ➔ Yes on confirm modal; asserts safe redirect to orders | `regression`, `edge`, `orders` |
| `test_merchant_lifecycle.py` | `test_merchant_dashboard_initial_view` | Verifies Merchant Portal greeting ("Welcome back, Merchant") and KPI cards | `smoke`, `merchant` |
| `test_merchant_lifecycle.py` | `test_merchant_creates_order` | Merchant creates an order with pre-filled merchant profile and existing customer | `smoke`, `merchant` |
| `test_merchant_lifecycle.py` | `test_merchant_schedules_pickup` | Merchant selects order, schedules pickup with address & date, asserts `PICK-` ID | `pickups`, `merchant` |
| `test_merchant_lifecycle.py` | `test_driver_portal_active_pickups` | Driver logs in and verifies Active Pickups table with status and actions | `driver` |
| `test_merchant_lifecycle.py` | `test_full_cross_role_e2e_integration` | Full multi-role flow: Merchant creates order ➔ schedules pickup ➔ dashboard updates ➔ Tenant Admin assigns driver (`b2c driver`) ➔ status transitions to 'Driver Assigned' ➔ driver views active pickup | `e2e`, `merchant` |
| `test_driver_actions.py` | `test_driver_portal_active_pickups_table` | Driver logs in and validates Active Pickups table columns and action buttons | `smoke`, `driver` |
| `test_driver_actions.py` | `test_driver_proceed_accepted_pickup_details` | Driver proceeds with accepted pickup (`View details`), asserts details & orders list | `regression`, `driver` |
| `test_driver_actions.py` | `test_driver_accept_assigned_pickup` | Driver clicks `Accept` on assigned pickup; asserts status transitions to `Driver Accepted` | `regression`, `driver` |
| `test_driver_actions.py` | `test_driver_reject_assigned_pickup` | Driver clicks `Reject` on assigned pickup; asserts rejection confirmation | `regression`, `driver` |
| `test_driver_actions.py` | `test_full_lifecycle_driver_accept_and_proceed` | End-to-end flow: Order creation ➔ Pickup scheduling ➔ Admin driver assignment ➔ Driver accept ➔ Driver proceeds to view pickup details | `e2e`, `driver` |
| `test_driver_delivery.py` | `test_driver_portal_today_manifest_view` | Driver verifies Today's Manifest headers, manifest details card, and shipments table | `smoke`, `driver` |
| `test_driver_delivery.py` | `test_driver_dashboard_kpis_display` | Driver verifies presence of core KPI metrics (`Total deliveries`, `Total failed`, etc.) | `smoke`, `driver` |
| `test_driver_delivery.py` | `test_driver_deliver_assigned_order` | Driver delivers assigned order from Today's Manifest; asserts status updates to `Delivered` | `regression`, `driver` |
| `test_driver_delivery.py` | `test_driver_fail_order_delivery_with_reason` | Driver records delivery failure with reason (`Customer No Answer`) and delivery notes | `regression`, `driver` |
| `test_driver_delivery.py` | `test_driver_deliver_failed_order_subsequently` | Driver records failure, then recovers and marks order as `Delivered` | `regression`, `driver` |
| `test_driver_delivery.py` | `test_end_to_end_driver_mixed_batch_lifecycle` | End-to-end multi-order batch: Order A delivered, Order B failed with `Customer Rejected Shipment`, driver dashboard reflects statistics | `e2e`, `driver` |
| `test_finance_accounting_cod.py` | `test_valid_e2e_cod_manifest_to_closed_and_cash_transfer_approved` | Full E2E valid lifecycle: COD order creation ➔ dispatch ➔ driver delivery with cash collection ➔ COD Collection `Collect Payment` ➔ Delivery Manifest status transitions to `Closed` ➔ reflects in Cash Transfer ➔ submit transfer with proof file ➔ verify pending approval with branch hub ➔ Admin approves transfer ➔ reflects `Approved` in history | `smoke`, `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_valid_cash_transfer_rejection_flow` | Submit cash transfer for COD collection ➔ In Pending Approval, Admin clicks Reject with mandatory reason ➔ transitions to `Rejected` status in history | `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_invalid_cod_collect_payment_disabled_when_manifest_open` | Asserts `Collect Payment` button is disabled (has HTML `disabled` attribute) when manifest has unfinished shipments | `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_invalid_submit_cash_transfer_without_proof` | Asserts submitting cash transfer without mandatory proof file upload fails validation and preserves modal | `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_invalid_submit_cash_transfer_zero_or_negative_amount` | Asserts entering amount 0 in cash transfer modal triggers validation error and prevents submission | `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_invalid_reject_transfer_cancel_modal_preserves_state` | Verifies opening Reject modal and clicking Cancel leaves the transfer pending without modification | `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_edge_hub_branch_filtering_isolation` | Verifies branch / hub dependency: selecting Hub filter cards (`Main Branch`, `Dammam Branch`, etc.) strictly isolates records by manifest branch | `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_edge_multiple_cod_batch_transfer_calculation` | Asserts selecting multiple COD checkboxes dynamically calculates and aggregates total amount in modal summary | `regression`, `finance`, `accounting` |
| `test_finance_accounting_cod.py` | `test_edge_completed_cod_collection_audit_details` | Audits Completed COD Collection tab headers and verifies standard settlement ID format (`COD-YYMMDD-XXXX`) | `regression`, `finance`, `accounting` |
| `test_sla.py` | `test_valid_navigate_all_sla_rules_views` | Validates loading and header schemas for all 3 SLA Rules sections (Order, FDR, Ticket) | `valid`, `sla` |
| `test_sla.py` | `test_valid_navigate_all_sla_tracking_views` | Validates loading and column schemas for all 3 SLA Tracking sections (Order, FDR, Ticket) | `valid`, `sla` |
| `test_sla.py` | `test_valid_sla_tab_switching_via_ui` | Switches Rules/Tracking tabs and Order/FDR/Ticket subtabs via UI buttons and verifies URLs | `valid`, `sla` |
| `test_sla.py` | `test_valid_create_order_sla_rule` | Creates full Order SLA Rule across 3-step wizard, verifies table entry with ACTIVE status & cleans up | `valid`, `sla` |
| `test_sla.py` | `test_valid_order_sla_tracking_rematch` | Triggers 'Rematch Rules' on Order SLA Tracking and verifies 202/200 API response | `valid`, `sla` |
| `test_sla.py` | `test_invalid_order_sla_empty_step1_validation` | Asserts 'This field is required' error when clicking Next on Step 1 with empty Rule Name | `invalid`, `sla` |
| `test_sla.py` | `test_invalid_order_sla_empty_step2_route_validation` | Asserts 4 route validation errors when clicking Next on Step 2 without route details | `invalid`, `sla` |
| `test_sla.py` | `test_invalid_order_sla_empty_step3_hours_validation` | Asserts 'This field is required' error when attempting to Save on Step 3 with empty transit hours | `invalid`, `sla` |
| `test_sla.py` | `test_invalid_fdr_sla_empty_role_validation` | Asserts 'This field is required' error when advancing FDR SLA wizard without Role | `invalid`, `sla` |
| `test_sla.py` | `test_invalid_ticket_sla_empty_reason_validation` | Asserts 'Reason is required' error when advancing Ticket SLA wizard without Reason | `invalid`, `sla` |
| `test_sla.py` | `test_edge_order_sla_search_filtering` | Verifies search filtering with matching query, empty state for non-existent query & clear search | `edge`, `sla` |
| `test_sla.py` | `test_edge_order_sla_cancel_wizard_preserves_state` | Verifies opening wizard, entering draft name, and clicking Cancel leaves table count unchanged | `edge`, `sla` |
| `test_sla.py` | `test_edge_order_sla_cancel_delete_modal` | Verifies clicking delete icon and then Cancel (No) in modal preserves the rule | `edge`, `sla` |
| `test_reports.py` | `test_valid_navigate_all_report_sections` | Validates loading and header schemas across Shipment, Performance, and Finance reports | `valid`, `reports` |
| `test_reports.py` | `test_valid_report_tab_switching_via_ui` | Switches between Shipment, Performance, and Finance reports via UI tabs and verifies URLs | `valid`, `reports` |
| `test_reports.py` | `test_valid_shipment_report_run_preview` | Runs report query preview via API 201/200 and validates preview table rows render | `valid`, `reports` |
| `test_reports.py` | `test_valid_shipment_report_export_pdf_and_verify_list` | Dispatches PDF export, navigates back to list, and verifies new PDF report with Completed status | `valid`, `reports` |
| `test_reports.py` | `test_valid_shipment_report_export_excel_and_download` | Dispatches Excel export, clicks download, and validates captured `.xlsx` file | `valid`, `reports` |
| `test_reports.py` | `test_valid_reports_format_filter` | Filters reports list by PDF and Excel formats, asserting rows match selected format | `valid`, `reports` |
| `test_reports.py` | `test_invalid_driver_performance_missing_dates_validation` | Asserts date range validation errors on Driver Performance preview without dates | `invalid`, `reports` |
| `test_reports.py` | `test_invalid_cod_collection_missing_dates_validation` | Asserts date range validation errors on COD Collection preview without dates | `invalid`, `reports` |
| `test_reports.py` | `test_invalid_driver_performance_export_missing_dates_validation` | Asserts date range validation errors on Driver Performance export attempt | `invalid`, `reports` |
| `test_reports.py` | `test_edge_shipment_report_column_toggling` | Toggles column inclusion switches in report builder and verifies preview runs cleanly | `edge`, `reports` |
| `test_reports.py` | `test_edge_report_create_back_navigation_preserves_list` | Verifies back navigation from builder preserves reports list and count | `edge`, `reports` |
| `test_reports.py` | `test_edge_empty_state_on_unmatched_format` | Verifies graceful rendering of empty placeholder on empty report views | `edge`, `reports` |
| `test_manifests.py` | `test_valid_navigate_all_manifest_tabs` | Validates loading, correct routes and header schemas across all 4 manifest tabs (Delivery, Ready for Delivery, IntraHub, Returns) | `smoke`, `valid`, `manifests` |
| `test_manifests.py` | `test_valid_delivery_manifests_table_data` | Verifies Delivery Manifests table contains data rows with `DM-` identifiers and valid statuses | `smoke`, `valid`, `manifests` |
| `test_manifests.py` | `test_valid_delivery_manifest_detail_view_and_shipments` | Opens delivery manifest detail view, asserts manifest metadata card, status, and shipments table | `smoke`, `valid`, `manifests` |
| `test_manifests.py` | `test_valid_delivery_manifest_export_excel` | Dispatches Excel export from manifest detail view, asserts `.xlsx` download and filename format | `regression`, `valid`, `manifests` |
| `test_manifests.py` | `test_valid_ready_for_delivery_manifest_detail_and_back` | Opens Ready for Delivery (`RFD-`), verifies detail view and returns safely using Back button | `regression`, `valid`, `manifests` |
| `test_manifests.py` | `test_valid_admin_pickups_table_headers_and_search` | Verifies Admin Pickups headers and executes search by `PICK-` prefix | `regression`, `valid`, `manifests` |
| `test_manifests.py` | `test_valid_pickup_detail_view_inspection` | Clicks pickup ID from list, verifies URL transitions with `pickupId` and detail elements render | `regression`, `valid`, `manifests` |
| `test_manifests.py` | `test_valid_pickup_driver_assigned_reflection` | Verifies Pickups table displays assigned driver and recognized lifecycle status | `regression`, `valid`, `manifests` |
| `test_manifests.py` | `test_invalid_intra_hub_manifest_missing_required_fields` | Asserts validation errors (`Branch is required`, etc.) when advancing wizard without fields | `regression`, `invalid`, `manifests` |
| `test_manifests.py` | `test_invalid_return_manifest_missing_required_fields` | Asserts validation errors (`Branch is required`, etc.) on Return Manifest wizard without fields | `regression`, `invalid`, `manifests` |
| `test_manifests.py` | `test_invalid_search_nonexistent_manifest` | Searches for nonexistent manifest ID and asserts table displays `No Data` empty state with 0 rows | `regression`, `invalid`, `manifests` |
| `test_manifests.py` | `test_edge_rapid_tab_switching_preserves_stability` | Rapidly switches across all 4 manifest tabs, asserting UI stability and clean final rendering | `regression`, `edge`, `manifests` |
| `test_manifests.py` | `test_edge_delivery_manifest_print_button_interaction` | Verifies Print button on manifest detail view is enabled and clickable without unhandled errors | `regression`, `edge`, `manifests` |
| `test_manifests.py` | `test_edge_pickups_search_nonexistent_handles_empty_state` | Searches for nonexistent pickup identifier and asserts clean empty state handling | `regression`, `edge`, `manifests` |
