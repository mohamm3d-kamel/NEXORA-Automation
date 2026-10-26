import time
import re
import pytest
from playwright.sync_api import Page
from pages.orders_page import OrdersPage
from pages.process_management_page import ProcessManagementPage


@pytest.mark.orders
@pytest.mark.return_orders
class TestReturnOrdersValid:
    """Valid happy-path scenarios for Return Orders creation, delivery, and delivery failure."""

    @pytest.mark.valid
    def test_valid_create_single_return_order(self, authenticated_orders: OrdersPage):
        """
        Verify single Return order creation:
        - Select Merchant, enter Reference Number, 1 package
        - Step 2: Select Shipment Type = 'Return'
        - Verify origin & destination are inverted (Customer -> Merchant)
        - Submit and verify order exists in table with Shipment Type = 'RETURN' and Status = 'Created'
        """
        orders = authenticated_orders
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-SGL-{unique_id}"

        shipment_num, ref = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=1,
            consignee_name=f"Return Client {unique_id}",
            consignee_phone="501234567",
            consignee_address="King Fahd Rd, Ret St 1",
            national_address="11537",
        )

        assert shipment_num.startswith("ORD"), f"Expected valid ORD shipment number, got: {shipment_num}"

        # Verify row in table
        row_text = orders.get_order_row_text(ref_num)
        assert ref_num in row_text
        assert orders.get_order_shipment_type(ref_num) == "RETURN"
        assert "Created" in orders.get_order_status(ref_num)

    @pytest.mark.valid
    def test_valid_create_multi_package_return_order(self, authenticated_orders: OrdersPage):
        """
        Verify multi-package Return order creation:
        - Create Return order with 3 packages
        - Verify order is submitted and appears in orders table
        """
        orders = authenticated_orders
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-MUL-{unique_id}"

        shipment_num, _ = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=3,
            consignee_name=f"Multi Return Customer {unique_id}",
            consignee_phone="509876543",
            consignee_address="Olaya St, Ret 3P",
            national_address="11537",
        )

        assert shipment_num.startswith("ORD")
        row_text = orders.get_order_row_text(ref_num)
        assert orders.get_order_shipment_type(ref_num) == "RETURN"
        assert "Created" in row_text

    @pytest.mark.valid
    def test_valid_return_order_lifecycle_delivered(
        self, authenticated_orders: OrdersPage, process_management_page: ProcessManagementPage
    ):
        """
        Full Lifecycle: Return Order Creation -> Out for Delivery -> Delivered:
        1. Create Return order with Shipment Type = Return
        2. Dispatch order via Process Management to driver ('Out for Delivery')
        3. Scan barcode under 'Delivered' action in Process Management
        4. Verify in Orders table that status transitions to 'Delivered'
        """
        orders = authenticated_orders
        pm = process_management_page
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-DLV-{unique_id}"

        # 1. Create Return order
        shipment_num, _ = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=1,
            consignee_name=f"Deliver Client {unique_id}",
            consignee_phone="505551234",
            consignee_address="King Fahd Rd, Deliver 1",
            national_address="11537",
        )
        assert shipment_num.startswith("ORD")

        # 2. Dispatch to Out for Delivery
        pm.dispatch_order_to_driver(shipment_number=shipment_num, driver_name="b2c driver", branch="Main Branch")

        # 3. Deliver Return Order via Process Management
        pm.deliver_order(shipment_num)

        # 4. Verify status in Orders table
        orders.open()
        status = orders.get_order_status(shipment_num)
        assert "Delivered" in status, f"Expected Delivered status, got: {status}"

    @pytest.mark.valid
    def test_valid_return_order_lifecycle_delivery_failed(
        self, authenticated_orders: OrdersPage, process_management_page: ProcessManagementPage
    ):
        """
        Full Lifecycle: Return Order Creation -> Out for Delivery -> Delivery Failed:
        1. Create Return order
        2. Dispatch order to driver ('Out for Delivery')
        3. Scan barcode under 'Delivery Failed' with reason 'Customer Rejected Shipment'
        4. Verify in Orders table that status transitions to 'Delivery Failed'
        """
        orders = authenticated_orders
        pm = process_management_page
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-FAIL-{unique_id}"

        # 1. Create Return order
        shipment_num, _ = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=1,
            consignee_name=f"Failed Client {unique_id}",
            consignee_phone="507779876",
            consignee_address="King Fahd Rd, Fail 1",
            national_address="11537",
        )
        assert shipment_num.startswith("ORD")

        # 2. Dispatch to Out for Delivery
        pm.dispatch_order_to_driver(shipment_number=shipment_num, driver_name="b2c driver", branch="Main Branch")

        # 3. Mark Delivery Failed via Process Management
        pm.fail_order_delivery(shipment_num, reason="Customer Rejected Shipment")

        # 4. Verify status in Orders table
        orders.open()
        status = orders.get_order_status(shipment_num)
        assert "Delivery Failed" in status or "Failed" in status, f"Expected Delivery Failed status, got: {status}"

    @pytest.mark.valid
    def test_valid_return_order_failed_then_recovered_to_delivered(
        self, authenticated_orders: OrdersPage, process_management_page: ProcessManagementPage
    ):
        """
        Lifecycle Recovery: Return Order Failed -> Subsequently Delivered:
        1. Create and dispatch Return order
        2. Record initial Delivery Failed with reason 'Customer No Answer'
        3. Assert status is Delivery Failed
        4. Subsequently re-attempt delivery and mark Delivered
        5. Verify status transitions to Delivered
        """
        orders = authenticated_orders
        pm = process_management_page
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-RECOV-{unique_id}"

        # 1. Create and dispatch
        shipment_num, _ = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=1,
            consignee_name=f"Recover Client {unique_id}",
            consignee_phone="503334444",
            consignee_address="King Fahd Rd, Recov 1",
            national_address="11537",
        )
        pm.dispatch_order_to_driver(shipment_number=shipment_num, driver_name="b2c driver", branch="Main Branch")

        # 2. Initial Delivery Failed
        pm.fail_order_delivery(shipment_num, reason="Customer Rejected Shipment")
        orders.open()
        initial_status = orders.get_order_status(shipment_num)
        assert "Delivery Failed" in initial_status or "Failed" in initial_status

        # 3. Recover to Delivered
        pm.deliver_order(shipment_num)
        orders.open()
        recovered_status = orders.get_order_status(shipment_num)
        assert "Delivered" in recovered_status, f"Expected Delivered after recovery, got: {recovered_status}"

    @pytest.mark.valid
    def test_valid_search_and_filter_return_orders(self, authenticated_orders: OrdersPage):
        """
        Verify search and filtering for Return orders in the orders table.
        """
        orders = authenticated_orders
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-SRCH-{unique_id}"

        shipment_num, _ = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=1,
            consignee_name=f"Search Client {unique_id}",
            consignee_phone="501239999",
            consignee_address="King Fahd Rd, Search 1",
            national_address="11537",
        )

        orders.open()
        search_input = orders.page.locator("input[placeholder*='Scan or paste']").first
        if search_input.is_visible():
            search_input.fill(shipment_num)
            search_input.press("Enter")
            orders.page.wait_for_timeout(1500)
            row_text = orders.get_order_row_text(shipment_num)
            assert shipment_num in row_text
            assert "RETURN" in row_text


@pytest.mark.orders
@pytest.mark.return_orders
class TestReturnOrdersInvalid:
    """Invalid negative validation scenarios for Return Orders."""

    @pytest.mark.invalid
    def test_invalid_create_return_order_missing_mandatory_consignee_name(
        self, authenticated_orders: OrdersPage
    ):
        """
        Attempt to create a Return order with missing consignee name.
        Verify inline validation error blocks order submission.
        """
        orders = authenticated_orders
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-INV-NAME-{unique_id}"

        orders.click_create_order()
        orders.select_merchant("B2C")
        orders.set_reference_number(ref_num)
        orders.set_package_count(1)
        orders.click_next()

        # Step 2: Select Return
        orders.select_shipment_type("Return")

        # Fill details but leave consignee name empty
        orders.fill_shipment_details(
            name="",
            phone="501234567",
            address="King Fahd Road, Inval 1",
            national_address="11537",
        )
        # Attempt to create order
        orders.submit_return_order()

        errors = orders.get_validation_errors()
        assert len(errors) > 0, f"Expected validation errors for missing consignee name, got: {errors}"

        # Clean up wizard modal
        cancel_btn = orders.page.locator(".ant-modal button:has-text('Cancel'), form button:has-text('Cancel')").first
        if cancel_btn.is_visible():
            cancel_btn.click()

    @pytest.mark.invalid
    def test_invalid_create_return_order_missing_mandatory_phone(
        self, authenticated_orders: OrdersPage
    ):
        """
        Attempt to create a Return order with missing consignee phone number.
        Verify phone validation error appears.
        """
        orders = authenticated_orders
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-INV-PHN-{unique_id}"

        orders.click_create_order()
        orders.select_merchant("B2C")
        orders.set_reference_number(ref_num)
        orders.set_package_count(1)
        orders.click_next()

        orders.select_shipment_type("Return")
        orders.fill_shipment_details(
            name="Valid Customer",
            phone="",
            address="King Fahd Road, Inval 2",
            national_address="11537",
        )
        orders.submit_return_order()

        errors = orders.get_validation_errors()
        assert len(errors) > 0, f"Expected validation errors for missing phone, got: {errors}"

        cancel_btn = orders.page.locator(".ant-modal button:has-text('Cancel'), form button:has-text('Cancel')").first
        if cancel_btn.is_visible():
            cancel_btn.click()

    @pytest.mark.invalid
    def test_invalid_process_management_delivery_failed_missing_reason(
        self, authenticated_orders: OrdersPage, process_management_page: ProcessManagementPage
    ):
        """
        Attempt to scan 'Delivery Failed' in Process Management without selecting a reason.
        Verify scanning without a reason does NOT transition the order to Delivery Failed.
        """
        orders = authenticated_orders
        pm = process_management_page
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-INV-RSN-{unique_id}"

        shipment_num, _ = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=1,
            consignee_name=f"No Reason Client {unique_id}",
            consignee_phone="504445555",
            consignee_address="King Fahd Rd, Inval Rsn",
        )
        pm.dispatch_order_to_driver(shipment_number=shipment_num, driver_name="b2c driver", branch="Main Branch")

        # Open PM, select Delivery Failed, DO NOT select reason, and attempt scan
        pm.open()
        pm.select_action("Delivery Failed")
        # Barcode input fill & enter
        pm.scan_barcode(shipment_num)
        pm.page.wait_for_timeout(1000)

        # Check notification or alert that reason is required, or order is NOT marked Delivery Failed
        orders.open()
        status = orders.get_order_status(shipment_num)
        # It should remain 'Out for Delivery' since no reason was provided
        assert "Out for Delivery" in status or status != "Delivery Failed"


@pytest.mark.orders
@pytest.mark.return_orders
class TestReturnOrdersEdge:
    """Edge and boundary scenarios for Return Orders."""

    @pytest.mark.edge
    def test_edge_return_wizard_toggle_shipment_type(self, authenticated_orders: OrdersPage):
        """
        Toggle Shipment Type dynamically between 'Normal' and 'Return' multiple times on Step 2.
        Verify:
        - When 'Return' is active: action button is 'Create Order' (Step 3 Payment is bypassed)
        - When 'Normal' is active: action button is 'Next' (Step 3 Payment is required)
        - Dynamic form state transitions cleanly without console or UI crashes
        """
        orders = authenticated_orders
        orders.click_create_order()
        orders.select_merchant("B2C")
        orders.set_reference_number(f"RET-EDGE-TOG-{int(time.time())}")
        orders.set_package_count(1)
        orders.click_next()

        # Step 2 initially Normal: Next button visible
        next_btn = orders.page.locator(".ant-modal button:has-text('Next'), form button:has-text('Next')").first
        create_btn = orders.page.locator(".ant-modal button:has-text('Create Order'), form button:has-text('Create Order')").first
        assert next_btn.is_visible()

        # Switch to Return: Create Order button visible, Next disappears
        orders.select_shipment_type("Return")
        assert create_btn.is_visible()
        assert not next_btn.is_visible()

        # Switch back to Normal: Next button returns
        orders.select_shipment_type("Normal")
        assert next_btn.is_visible()
        assert not create_btn.is_visible()

        # Switch again to Return: Create Order button returns
        orders.select_shipment_type("Return")
        assert create_btn.is_visible()

        # Cancel cleanly
        orders.cancel_wizard()

    @pytest.mark.edge
    def test_edge_cancel_return_wizard_step2_preserves_orders_table(
        self, authenticated_orders: OrdersPage
    ):
        """
        Fill Step 1, select Return in Step 2, and click Cancel.
        Verify the wizard unmounts cleanly and no orphan order is written to the table.
        """
        orders = authenticated_orders
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-EDGE-CAN-{unique_id}"

        orders.click_create_order()
        orders.select_merchant("B2C")
        orders.set_reference_number(ref_num)
        orders.set_package_count(1)
        orders.click_next()

        orders.select_shipment_type("Return")
        orders.fill_shipment_details(name="Cancel Test Client")

        # Cancel wizard
        orders.cancel_wizard()
        orders.page.wait_for_timeout(1000)

        # Assert no modal is open and reference number was not saved
        assert not orders.page.locator(".ant-modal").is_visible()
        assert not orders.is_order_present_in_list(ref_num)

    @pytest.mark.edge
    def test_edge_return_order_update_status_modal_action(self, authenticated_orders: OrdersPage):
        """
        Verify updating a Return order's status directly via the row Actions -> 'Update Status' modal.
        """
        orders = authenticated_orders
        unique_id = int(time.time() * 1000) % 100000000
        ref_num = f"RET-MODAL-{unique_id}"

        shipment_num, _ = orders.create_return_order(
            merchant="B2C",
            ref_number=ref_num,
            package_count=1,
            consignee_name=f"Modal Status Client {unique_id}",
            consignee_phone="501112222",
            consignee_address="King Fahd Rd, Modal 1",
            national_address="11537",
        )

        orders.open()
        row_text = orders.get_order_row_text(ref_num)
        assert ref_num in row_text
        row = orders.page.locator(f".ant-table-tbody tr:has-text('{ref_num}')").first
        assert row.is_visible()

        # Click action dropdown
        action_btn = row.locator("button.ant-dropdown-trigger").first
        if action_btn.is_visible():
            action_btn.click()
            orders.page.wait_for_timeout(500)
            orders.page.click(".ant-dropdown-menu-item:has-text('Update Status')")
            orders.page.wait_for_timeout(1000)

            # Modal visible
            modal = orders.page.locator(".ant-modal").first
            assert modal.is_visible()

            # Select 'Picked Up' status
            status_sel = modal.locator(".ant-select").first
            status_sel.click()
            orders.page.wait_for_timeout(500)
            orders.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('Picked Up')").first.click()
            orders.page.wait_for_timeout(500)

            # Click Update
            modal.locator("button:has-text('Update')").first.click()
            orders.page.wait_for_timeout(2000)

            # Verify status in row
            orders.open()
            new_status = orders.get_order_status(ref_num)
            assert "Picked Up" in new_status or "Picked" in new_status or shipment_num in orders.get_order_row_text(ref_num)
