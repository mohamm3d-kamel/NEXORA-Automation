import pytest
from playwright.sync_api import Page, expect
from pages.reports_page import ReportsPage


@pytest.mark.reports
class TestReportsModule:
    """
    Comprehensive test suite for the Reports module:
    - Valid Scenarios: 3-view navigation (Shipment, Performance, Finance), UI tab switching,
      Shipment query preview execution, PDF export verification, Excel export and file download,
      and format-based table filtering (All, PDF, Excel).
    - Invalid Scenarios: Date range validation enforcement on Driver Performance and COD Collection builders.
    - Edge Scenarios: Column inclusion toggling, builder cancellation/back navigation preservation,
      and empty table state handling.
    """

    # =========================================================================
    # Valid Scenarios
    # =========================================================================

    @pytest.mark.valid
    def test_valid_navigate_all_report_sections(self, authenticated_reports: ReportsPage):
        """
        [Valid] Verify that all 3 Reports sections (Shipment Reports,
        Performance Reports, Finance Reports) load with expected table headers.
        """
        reports = authenticated_reports
        expected_headers = ["Report type", "Format", "Reported by", "Status", "Created at", "File name", "Download"]

        # 1. Shipment Reports
        reports.open_shipment_reports()
        shipment_headers = reports.get_table_header_titles()
        for h in expected_headers:
            assert h in shipment_headers, f"Expected '{h}' in Shipment Reports headers, got: {shipment_headers}"

        # 2. Performance Reports (Driver Performance)
        reports.open_performance_reports()
        perf_headers = reports.get_table_header_titles()
        for h in expected_headers:
            assert h in perf_headers, f"Expected '{h}' in Performance Reports headers, got: {perf_headers}"

        # 3. Finance Reports (COD Collection)
        reports.open_finance_reports()
        finance_headers = reports.get_table_header_titles()
        for h in expected_headers:
            assert h in finance_headers, f"Expected '{h}' in Finance Reports headers, got: {finance_headers}"

    @pytest.mark.valid
    def test_valid_report_tab_switching_via_ui(self, authenticated_reports: ReportsPage):
        """
        [Valid] Switch between report sections using top tabs via UI clicks
        and verify corresponding URLs update properly.
        """
        reports = authenticated_reports
        reports.open_shipment_reports()

        # Switch to Performance Reports via UI
        reports.switch_via_ui("Performance Reports")
        assert "reports/performance/driver-performance" in reports.current_url, (
            f"Expected URL to contain 'reports/performance/driver-performance', got: {reports.current_url}"
        )

        # Switch to Finance Reports via UI
        reports.switch_via_ui("Finance Reports")
        assert "reports/finance/cod-collection" in reports.current_url, (
            f"Expected URL to contain 'reports/finance/cod-collection', got: {reports.current_url}"
        )

        # Switch back to Shipment Reports via UI
        reports.switch_via_ui("Shipment Reports")
        assert "reports/shipment/info" in reports.current_url, (
            f"Expected URL to contain 'reports/shipment/info', got: {reports.current_url}"
        )

    @pytest.mark.valid
    def test_valid_shipment_report_run_preview(self, authenticated_reports: ReportsPage):
        """
        [Valid] Navigate to Shipment report builder, click 'Run Preview',
        assert API 200/201 response, and verify preview table data rows render.
        """
        reports = authenticated_reports
        reports.open_create_view("shipment")

        assert reports.run_preview_btn.is_visible(), "Expected 'Run Preview' button to be visible"
        success = reports.run_preview()
        assert success, "Expected Run Preview API to return 200 or 201"

        # Verify preview data rows rendered
        preview_count = reports.get_preview_rows_count()
        assert preview_count > 0, f"Expected preview table to have rows, got: {preview_count}"

    @pytest.mark.valid
    def test_valid_shipment_report_export_pdf_and_verify_list(self, authenticated_reports: ReportsPage):
        """
        [Valid] Navigate to Shipment report builder, click 'Export PDF',
        verify export API success, navigate back to reports list,
        and assert newly generated PDF report appears in the table.
        """
        reports = authenticated_reports
        reports.open_create_view("shipment")

        success = reports.export_pdf()
        assert success, "Expected Export PDF API to return 200 or 201"

        # Navigate back to report list
        reports.click_back_to_reports()
        reports.wait_for_table_loaded()

        # Verify top report entry has pdf format and Completed status
        top_row_text = reports.get_all_report_rows_text()[0]
        assert "pdf" in top_row_text.lower(), f"Expected 'pdf' in top row text, got: {top_row_text}"
        assert "completed" in top_row_text.lower(), f"Expected 'Completed' status in top row text, got: {top_row_text}"

    @pytest.mark.valid
    def test_valid_shipment_report_export_excel_and_download(self, authenticated_reports: ReportsPage):
        """
        [Valid] Navigate to Shipment report builder, click 'Export Excel',
        navigate back to list, click download icon on top row,
        and assert browser download captures valid .xlsx file.
        """
        reports = authenticated_reports
        reports.open_create_view("shipment")

        success = reports.export_excel()
        assert success, "Expected Export Excel API to return 200 or 201"

        reports.click_back_to_reports()
        reports.wait_for_table_loaded()

        # Download top report
        download = reports.download_top_report()
        filename = download.suggested_filename
        assert filename.endswith(".xlsx"), f"Expected downloaded filename to end with '.xlsx', got: {filename}"
        assert "orders" in filename.lower(), f"Expected 'orders' in filename, got: {filename}"

    @pytest.mark.valid
    def test_valid_reports_format_filter(self, authenticated_reports: ReportsPage):
        """
        [Valid] On Shipment Reports list, filter by 'PDF' and 'Excel'
        and assert that table rows reflect only selected format.
        """
        reports = authenticated_reports
        reports.open_shipment_reports()
        total_count = reports.get_report_rows_count()
        assert total_count >= 1, "Expected at least 1 baseline report in table"

        # 1. Filter by PDF
        reports.filter_by_format("PDF")
        pdf_rows = reports.get_all_report_rows_text()
        assert len(pdf_rows) > 0, "Expected PDF reports to be listed"
        for r in pdf_rows:
            assert "pdf" in r.lower(), f"Expected 'pdf' format in filtered row: {r}"

        # 2. Filter by Excel
        reports.filter_by_format("Excel")
        excel_rows = reports.get_all_report_rows_text()
        assert len(excel_rows) > 0, "Expected Excel reports to be listed"
        for r in excel_rows:
            assert "excel" in r.lower(), f"Expected 'excel' format in filtered row: {r}"

        # 3. Reset to All formats
        reports.filter_by_format("All formats")
        all_rows = reports.get_report_rows_count()
        assert all_rows >= len(pdf_rows), "Expected All formats to show full listing"

    # =========================================================================
    # Invalid Scenarios
    # =========================================================================

    @pytest.mark.invalid
    def test_invalid_driver_performance_missing_dates_validation(self, authenticated_reports: ReportsPage):
        """
        [Invalid] Attempt to Run Preview on Driver Performance report without entering
        mandatory date range. Verify inline validation errors appear.
        """
        reports = authenticated_reports
        reports.open_create_view("performance")

        reports.run_preview_btn.click()
        reports.page.wait_for_timeout(600)

        errors = reports.get_validation_errors()
        assert any("Created at from" in err for err in errors), (
            f"Expected 'Please enter Created at from' error, got: {errors}"
        )
        assert any("Created at to" in err for err in errors), (
            f"Expected 'Please enter Created at to' error, got: {errors}"
        )

    @pytest.mark.invalid
    def test_invalid_cod_collection_missing_dates_validation(self, authenticated_reports: ReportsPage):
        """
        [Invalid] Attempt to Run Preview on COD Collection report without entering
        mandatory date range. Verify inline validation errors appear.
        """
        reports = authenticated_reports
        reports.open_create_view("finance")

        reports.run_preview_btn.click()
        reports.page.wait_for_timeout(600)

        errors = reports.get_validation_errors()
        assert any("Created at from" in err for err in errors), (
            f"Expected 'Please enter Created at from' error, got: {errors}"
        )
        assert any("Created at to" in err for err in errors), (
            f"Expected 'Please enter Created at to' error, got: {errors}"
        )

    @pytest.mark.invalid
    def test_invalid_driver_performance_export_missing_dates_validation(self, authenticated_reports: ReportsPage):
        """
        [Invalid] Attempt to Export PDF on Driver Performance report without entering
        mandatory date range. Verify export is prevented and validation errors appear.
        """
        reports = authenticated_reports
        reports.open_create_view("performance")

        reports.export_pdf_btn.click()
        reports.page.wait_for_timeout(600)

        errors = reports.get_validation_errors()
        assert any("Created at from" in err for err in errors), (
            f"Expected 'Please enter Created at from' error on export attempt, got: {errors}"
        )

    # =========================================================================
    # Edge Scenarios
    # =========================================================================

    @pytest.mark.edge
    def test_edge_shipment_report_column_toggling(self, authenticated_reports: ReportsPage):
        """
        [Edge] Toggle column inclusion checkboxes in the Shipment report builder
        and verify preview query runs without breaking.
        """
        reports = authenticated_reports
        reports.open_create_view("shipment")

        # Toggle optional column checkboxes
        reports.toggle_column_checkbox("Priority")
        reports.toggle_column_checkbox("Package count")

        # Run preview with custom columns
        success = reports.run_preview()
        assert success, "Expected Run Preview to succeed with custom columns toggled"
        assert reports.get_preview_rows_count() > 0, "Expected preview table to display rows"

    @pytest.mark.edge
    def test_edge_report_create_back_navigation_preserves_list(self, authenticated_reports: ReportsPage):
        """
        [Edge] Navigate to report builder, click 'Back to report types',
        and verify returning to main list with preserved table count.
        """
        reports = authenticated_reports
        reports.open_shipment_reports()
        initial_count = reports.get_report_rows_count()

        reports.click_create_report()
        assert "create" in reports.current_url, "Expected URL to contain 'create'"

        reports.click_back_to_reports()
        assert "create" not in reports.current_url, "Expected URL to return to report list"
        after_count = reports.get_report_rows_count()
        assert after_count == initial_count, (
            f"Expected list count to remain {initial_count}, got: {after_count}"
        )

    @pytest.mark.edge
    def test_edge_empty_state_on_unmatched_format(self, authenticated_reports: ReportsPage):
        """
        [Edge] Open Performance Reports (empty state) and verify graceful
        rendering of the 'No Data' placeholder.
        """
        reports = authenticated_reports
        reports.open_performance_reports()

        # Performance reports table has 0 rows or empty placeholder
        assert reports.empty_placeholder.is_visible() or reports.get_report_rows_count(wait_for_rows=False) == 0, (
            "Expected empty state placeholder or 0 rows on empty performance reports table"
        )
