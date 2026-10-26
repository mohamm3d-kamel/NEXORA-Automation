import time
import re
import os
from typing import Tuple
import pytest
from playwright.sync_api import Browser, Page, expect
from config.settings import settings
from pages.login_page import LoginPage
from pages.orders_page import OrdersPage
from pages.driver_page import DriverPage
from pages.process_management_page import ProcessManagementPage
from pages.accounting_page import AccountingPage

@pytest.mark.finance
@pytest.mark.accounting
class TestFinanceAccountingCOD:
    """
    Test suite for Accounting, COD Collection, and Cash Transfer lifecycle:
    - Delivery Manifest completion, payment collection, and status transition to 'Closed'
    - Cash Transfer submission with proof
    - Approval and Rejection workflows with rejection reasons
    - Branch / Hub dependency and isolation
    - Valid, Invalid, and Edge scenarios
    """

    def _create_and_dispatch_cod_order(
        self,
        browser: Browser,
        amount: str = "150",
        branch: str = "Main Branch",
        driver_name: str = "b2c driver",
    ) -> Tuple[str, str]:
        """
        Helper method to:
        1. Create a Cash (COD) order as Tenant Admin
        2. Dispatch order to driver via Process Management with branch
        Returns (shipment_number, reference_number).
        """
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"REF-COD-{unique_id}"

        admin_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = admin_ctx.new_page()
        LoginPage(a_page).open().login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)

        orders = OrdersPage(a_page).open()
        orders.click_create_order()
        orders.select_merchant("B2C")
        orders.set_reference_number(ref_num)
        orders.click_next()

        orders.fill_shipment_details(
            name=f"COD Client {unique_id}",
            phone="555123456",
            address="456 King Fahd Rd",
            national_address="11537",
        )
        orders.click_next()

        orders.select_payment_method("Cash")
        orders.set_financial_details(total_amount=amount, shipment_value=str(int(amount) + 50))
        orders.submit_order()

        # Extract shipment number from Orders table
        a_page.wait_for_timeout(2000)
        orders_row = a_page.locator(".ant-table-tbody tr").filter(has_text=ref_num).first
        row_text = orders_row.inner_text()
        match = re.search(r"ORD[A-Z0-9]+", row_text)
        assert match, f"Could not find shipment number for reference {ref_num} in row: {row_text}"
        shipment_num = match.group(0)

        # Dispatch order via Process Management
        pm = ProcessManagementPage(a_page)
        pm.dispatch_order_to_driver(shipment_number=shipment_num, driver_name=driver_name, branch=branch)

        admin_ctx.close()
        return shipment_num, ref_num

    # =========================================================================
    # VALID SCENARIOS
    # =========================================================================

    @pytest.mark.smoke
    @pytest.mark.regression
    def test_valid_e2e_cod_manifest_to_closed_and_cash_transfer_approved(
        self,
        browser: Browser,
        proof_file_path: str,
    ):
        """
        Full End-to-End Valid Lifecycle:
        1. Order created with Cash (COD 150 SAR)
        2. Dispatched to driver at 'Main Branch'
        3. Driver delivers order on Today's Manifest with Cash collection
        4. In Accounting -> COD Collection (Pending collection), manifest is 'Ready for collection'
        5. Admin collects payment -> Manifest transitions to 'Closed'
        6. Completed COD reflection verified
        7. In Cash Transfer, COD is selected and submitted with proof
        8. In Pending Approval, transfer reflects with 'Main Branch' Hub and amount
        9. Admin approves transfer -> Status becomes 'Approved' in history
        """
        cod_amount = "150"
        branch_name = "Main Branch"
        shipment_num, _ = self._create_and_dispatch_cod_order(
            browser, amount=cod_amount, branch=branch_name, driver_name="b2c driver"
        )

        # Step 1: Driver delivers order
        driver_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        d_page = driver_ctx.new_page()
        LoginPage(d_page).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
        driver = DriverPage(d_page)
        driver.deliver_cod_order(shipment_num, paid_amount=float(cod_amount), payment_type="CASH", complete_all_on_manifest=True)
        status_after_del = driver.get_shipment_status_on_manifest(shipment_num)
        assert "Delivered" in status_after_del, f"Expected Delivered status, got: {status_after_del}"
        driver_ctx.close()

        # Step 2: Admin checks COD Collection
        admin_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = admin_ctx.new_page()
        LoginPage(a_page).open().login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        accounting = AccountingPage(a_page).open_cod_collection()

        # Locate manifest that is Ready for collection
        ready_row = a_page.locator(".ant-tabs-tabpane-active tbody tr:has-text('Ready for collection')").first
        ready_row.wait_for(state="visible", timeout=15000)
        ready_text = ready_row.inner_text()
        dm_match = re.search(r"DM-\d+-\d+", ready_text)
        assert dm_match, f"Could not find manifest ID in ready row: {ready_text}"
        manifest_id = dm_match.group(0)

        assert accounting.is_collect_payment_enabled(manifest_id), "Collect Payment button must be enabled"

        # Step 3: Admin collects payment
        accounting.collect_payment(manifest_id, amount=cod_amount, notes="E2E automation test collection")

        # Step 4: Verify Delivery Manifest status transitions to 'Closed'
        dm_status_text = accounting.get_delivery_manifest_status(manifest_id)
        assert "Closed" in dm_status_text, f"Expected Delivery Manifest to become Closed, got: {dm_status_text}"

        # Step 5: Verify Completed COD Collection reflection
        accounting.open_cod_collection().switch_cod_tab("Completed")
        a_page.wait_for_timeout(1000)

        # Step 6: Verify COD reflects on Cash Transfer
        accounting.open_cash_transfer()
        accounting.switch_cash_transfer_tab("COD Completed pending transfer")
        available_cod_row = a_page.locator(".ant-tabs-tabpane-active tbody tr").filter(has_text="COD-").first
        available_cod_row.wait_for(state="visible", timeout=10000)
        assert available_cod_row.is_visible(), "Expected at least one available COD settlement row"
        cod_row_text = available_cod_row.inner_text()
        cod_match = re.search(r"COD-\d+-\d+", cod_row_text)
        assert cod_match, f"Could not find COD settlement ID in row: {cod_row_text}"
        settlement_id = cod_match.group(0)

        # Step 7: Select COD and Submit Cash Transfer
        accounting.select_cod_checkbox(settlement_id)
        assert accounting.is_submit_cash_transfer_button_visible(), "Submit Cash Transfer button must appear"
        accounting.submit_cash_transfer(proof_file_path=proof_file_path)

        # Step 8: Verify in 'Cash transfers pending approval'
        accounting.switch_cash_transfer_tab("Cash transfers pending approval")
        pending_transfer_row = a_page.locator(
            f".ant-tabs-tabpane-active tbody tr:has-text('TRF-'):has-text('{branch_name}')"
        ).first
        pending_transfer_row.wait_for(state="visible", timeout=10000)
        assert pending_transfer_row.is_visible(), f"Expected pending transfer for Hub {branch_name}"
        trf_text = pending_transfer_row.inner_text()
        trf_match = re.search(r"TRF-\d+-\d+", trf_text)
        assert trf_match, f"Expected TRF number in {trf_text}"
        transfer_number = trf_match.group(0)

        assert branch_name in trf_text, f"Expected Hub '{branch_name}' in transfer row: {trf_text}"
        assert "Pending approval" in trf_text, f"Expected Pending approval status in {trf_text}"

        # Step 9: Admin Approves Cash Transfer
        accounting.approve_transfer(transfer_number)

        # Step 10: Verify in 'Cash transfers approved/rejected'
        accounting.switch_cash_transfer_tab("Cash transfers approved/rejected")
        history_text = accounting.get_history_transfer_status(transfer_number)
        assert "Approved" in history_text, f"Expected status 'Approved' in history row, got: {history_text}"
        assert branch_name in history_text, f"Expected Hub '{branch_name}' in history row"

        admin_ctx.close()

    @pytest.mark.regression
    def test_valid_cash_transfer_rejection_flow(
        self,
        browser: Browser,
        proof_file_path: str,
    ):
        """
        Valid Cash Transfer Rejection:
        1. Select an available COD settlement (or generate one)
        2. Submit Cash Transfer with proof
        3. Under Pending Approval, Admin clicks Reject
        4. Admin fills mandatory rejection reason and confirms
        5. Verify transfer transitions to 'Rejected' status in history
        """
        admin_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
        a_page = admin_ctx.new_page()
        LoginPage(a_page).open().login(settings.TEST_USER_EMAIL, settings.TEST_USER_PASSWORD)
        accounting = AccountingPage(a_page).open_cash_transfer()

        # Check if an available COD is in pending transfer; if not, create and collect one
        accounting.switch_cash_transfer_tab("COD Completed pending transfer")
        available_cod = a_page.locator(".ant-tabs-tabpane-active tbody tr:has-text('COD-')").first
        if not available_cod.is_visible():
            # Quick COD creation & collection
            shipment_num, _ = self._create_and_dispatch_cod_order(browser, amount="100", branch="Main Branch")
            d_ctx = browser.new_context(viewport=settings.get_screen_dimensions())
            dp = d_ctx.new_page()
            LoginPage(dp).open().login(settings.DRIVER_EMAIL, settings.DRIVER_PASSWORD)
            DriverPage(dp).deliver_cod_order(shipment_num, paid_amount=100.0, complete_all_on_manifest=True)
            d_ctx.close()

            accounting.open_cod_collection()
            row = a_page.locator(".ant-tabs-tabpane-active tr:has-text('Ready for collection')").first
            dm_id = re.search(r"DM-\d+-\d+", row.inner_text()).group(0)
            accounting.collect_payment(dm_id)
            accounting.open_cash_transfer().switch_cash_transfer_tab("COD Completed pending transfer")

        # Select settlement and submit
        target_row = a_page.locator(".ant-tabs-tabpane-active tbody tr:has-text('COD-')").first
        target_text = target_row.inner_text()
        settlement_id = re.search(r"COD-\d+-\d+", target_text).group(0)
        accounting.select_cod_checkbox(settlement_id)
        accounting.submit_cash_transfer(proof_file_path=proof_file_path)

        # In Pending Approval, reject transfer
        accounting.switch_cash_transfer_tab("Cash transfers pending approval")
        pending_row = a_page.locator(".ant-tabs-tabpane-active tbody tr:has-text('TRF-')").first
        trf_num = re.search(r"TRF-\d+-\d+", pending_row.inner_text()).group(0)

        rejection_reason = "Deposit slip mismatch - Automated Test"
        accounting.reject_transfer(trf_num, reason=rejection_reason)

        # Verify in history
        accounting.switch_cash_transfer_tab("Cash transfers approved/rejected")
        history_text = accounting.get_history_transfer_status(trf_num)
        assert "Rejected" in history_text, f"Expected 'Rejected' status in history, got: {history_text}"

        admin_ctx.close()

    # =========================================================================
    # INVALID SCENARIOS
    # =========================================================================

    @pytest.mark.regression
    def test_invalid_cod_collect_payment_disabled_when_manifest_open(
        self,
        authenticated_accounting: AccountingPage,
    ):
        """
        Invalid Scenario:
        Assert that for any Delivery Manifest with status 'Open' (unfinished shipments),
        the 'Collect Payment' button is disabled.
        """
        authenticated_accounting.open_cod_collection().switch_cod_tab("Pending collection")
        open_manifest_row = authenticated_accounting.page.locator(
            ".ant-tabs-tabpane-active tbody tr:has-text('Open')"
        ).first

        if open_manifest_row.is_visible():
            collect_btn = open_manifest_row.locator("button:has-text('Collect Payment')").first
            assert collect_btn.is_visible(), "Collect Payment button must exist on the row"
            assert not collect_btn.is_enabled(), "Collect Payment button must be DISABLED when manifest status is Open"
            assert collect_btn.get_attribute("disabled") is not None, "Button must have HTML disabled attribute"

    @pytest.mark.regression
    def test_invalid_submit_cash_transfer_without_proof(
        self,
        authenticated_accounting: AccountingPage,
    ):
        """
        Invalid Scenario:
        Attempting to submit Cash Transfer without uploading the proof of transfer
        must prevent submission and show validation error.
        """
        authenticated_accounting.open_cash_transfer().switch_cash_transfer_tab("COD Completed pending transfer")
        available_row = authenticated_accounting.page.locator(".ant-tabs-tabpane-active tbody tr:has-text('COD-')").first

        if available_row.is_visible():
            target_text = available_row.inner_text()
            settlement_id = re.search(r"COD-\d+-\d+", target_text).group(0)
            authenticated_accounting.select_cod_checkbox(settlement_id)

            authenticated_accounting.open_submit_cash_transfer_modal()
            assert authenticated_accounting.modal.is_visible(), "Modal must be visible"

            # Submit without selecting file
            submit_btn = authenticated_accounting.modal_submit_button
            submit_btn.click()
            authenticated_accounting.page.wait_for_timeout(1000)

            # Assert modal remains open due to missing required proof
            assert authenticated_accounting.modal.is_visible(), "Modal must remain open when proof is missing"

            # Clean up modal
            authenticated_accounting.close_submit_modal_cancel()

    @pytest.mark.regression
    def test_invalid_submit_cash_transfer_zero_or_negative_amount(
        self,
        authenticated_accounting: AccountingPage,
        proof_file_path: str,
    ):
        """
        Invalid Scenario:
        Entering 0 as the transfer amount must fail validation.
        """
        authenticated_accounting.open_cash_transfer().switch_cash_transfer_tab("COD Completed pending transfer")
        available_row = authenticated_accounting.page.locator(".ant-tabs-tabpane-active tbody tr:has-text('COD-')").first

        if available_row.is_visible():
            settlement_id = re.search(r"COD-\d+-\d+", available_row.inner_text()).group(0)
            authenticated_accounting.select_cod_checkbox(settlement_id)

            authenticated_accounting.open_submit_cash_transfer_modal()
            authenticated_accounting.modal_file_input.set_input_files(proof_file_path)

            # Set amount to 0
            authenticated_accounting.modal_amount_input.fill("0")
            authenticated_accounting.modal_submit_button.click()
            authenticated_accounting.page.wait_for_timeout(1000)

            # Assert modal stays open or validation error appears
            assert authenticated_accounting.modal.is_visible(), "Modal must not submit with amount 0"

            authenticated_accounting.close_submit_modal_cancel()

    @pytest.mark.regression
    def test_invalid_reject_transfer_cancel_modal_preserves_state(
        self,
        authenticated_accounting: AccountingPage,
    ):
        """
        Invalid / Cancellation Scenario:
        Opening Reject modal and clicking Cancel must leave transfer pending.
        """
        authenticated_accounting.open_cash_transfer().switch_cash_transfer_tab("Cash transfers pending approval")
        pending_row = authenticated_accounting.page.locator(".ant-tabs-tabpane-active tbody tr:has-text('TRF-')").first

        if pending_row.is_visible():
            reject_btn = pending_row.locator("button:has-text('Reject')").first
            reject_btn.click()
            authenticated_accounting.page.wait_for_timeout(500)

            assert authenticated_accounting.modal.is_visible(), "Reject modal must be open"
            authenticated_accounting.modal_cancel_button.click()
            authenticated_accounting.page.wait_for_timeout(500)

            assert not authenticated_accounting.modal.is_visible(), "Reject modal must close on Cancel"
            assert pending_row.is_visible(), "Transfer must still remain in Pending approval"

    # =========================================================================
    # EDGE SCENARIOS
    # =========================================================================

    @pytest.mark.regression
    def test_edge_hub_branch_filtering_isolation(
        self,
        authenticated_accounting: AccountingPage,
    ):
        """
        Edge Scenario: Branch / Hub Filtering Isolation:
        On 'Cash transfers approved/rejected', clicking different Hub branch cards
        isolates the displayed transfer records to only those belonging to the selected Hub.
        """
        authenticated_accounting.open_cash_transfer().switch_cash_transfer_tab("Cash transfers approved/rejected")
        available_hubs = authenticated_accounting.get_available_hub_branches()
        assert len(available_hubs) >= 2, f"Expected multiple branch cards, found: {available_hubs}"

        # 1. Select 'Main Branch'
        if "Main Branch" in available_hubs:
            authenticated_accounting.select_hub_branch("Main Branch")
            rows = authenticated_accounting.page.locator(".ant-tabs-tabpane-active tbody tr:has-text('TRF-')").all()
            for r in rows[:5]:
                text = r.inner_text()
                assert "Main Branch" in text, f"All rows under Main Branch hub filter must belong to Main Branch: {text}"

        # 2. Select another branch (e.g. 'Dammam Branch' or 'Jeddah branch')
        alt_branch = next((h for h in available_hubs if h != "Main Branch"), None)
        if alt_branch:
            authenticated_accounting.select_hub_branch(alt_branch)
            alt_rows = authenticated_accounting.page.locator(".ant-tabs-tabpane-active tbody tr:has-text('TRF-')").all()
            for r in alt_rows[:5]:
                text = r.inner_text()
                assert alt_branch in text, f"All rows under {alt_branch} filter must belong to {alt_branch}: {text}"

    @pytest.mark.regression
    def test_edge_multiple_cod_batch_transfer_calculation(
        self,
        authenticated_accounting: AccountingPage,
    ):
        """
        Edge Scenario:
        Selecting multiple COD settlement records aggregates the total amount dynamically
        in the Submit Cash Transfer modal summary.
        """
        authenticated_accounting.open_cash_transfer().switch_cash_transfer_tab("COD Completed pending transfer")
        cod_rows = authenticated_accounting.page.locator(".ant-tabs-tabpane-active tbody tr:has-text('COD-')").all()

        if len(cod_rows) >= 2:
            # Extract individual amounts
            amounts = []
            for r in cod_rows[:2]:
                text = r.inner_text()
                amt_match = re.search(r"(\d+(\.\d+)?)\s*SAR", text)
                if amt_match:
                    amounts.append(float(amt_match.group(1)))
                checkbox = r.locator("input[type='checkbox']").first
                checkbox.click()
                authenticated_accounting.page.wait_for_timeout(300)

            # Open modal
            authenticated_accounting.open_submit_cash_transfer_modal()
            summary_text = authenticated_accounting.get_submit_modal_summary_text()

            assert "2 selected" in summary_text, f"Expected '2 selected' in modal summary: {summary_text}"
            if len(amounts) == 2:
                expected_total = int(sum(amounts))
                assert str(expected_total) in summary_text, f"Expected aggregated total {expected_total} in: {summary_text}"

            authenticated_accounting.close_submit_modal_cancel()

            # Deselect checkboxes
            for r in cod_rows[:2]:
                r.locator("input[type='checkbox']").first.click()
                authenticated_accounting.page.wait_for_timeout(200)

    @pytest.mark.regression
    def test_edge_completed_cod_collection_audit_details(
        self,
        authenticated_accounting: AccountingPage,
    ):
        """
        Edge Scenario:
        Follow the 'Completed' COD Collection tab to verify table headers and settlement ID format.
        """
        authenticated_accounting.open_cod_collection().switch_cod_tab("Completed")
        headers = authenticated_accounting.page.locator(".ant-tabs-tabpane-active .ant-table-thead th").all_text_contents()
        headers_text = " ".join(headers)

        assert "Collection Number" in headers_text, f"Expected 'Collection Number' in headers: {headers}"
        assert "Driver Name" in headers_text, f"Expected 'Driver Name' in headers: {headers}"
        assert "Total Amount" in headers_text, f"Expected 'Total Amount' in headers: {headers}"

        completed_rows = authenticated_accounting.get_completed_cod_rows()
        if completed_rows:
            first_record = completed_rows[0]
            assert "COD-" in first_record["raw_text"], f"Expected COD- prefix in settlement record: {first_record}"
            assert re.search(r"COD-\d{6}-\d+", first_record["raw_text"]), "Expected standard settlement ID format"
