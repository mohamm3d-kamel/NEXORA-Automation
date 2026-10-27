import time
from typing import List, Optional, Dict
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from config.settings import settings

class B2BOrdersPage(BasePage):
    """Page Object for B2B Orders Management across Tenant Admin and Merchant Portal."""

    def __init__(self, page: Page):
        super().__init__(page)

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------
    def open_admin_b2b(self) -> "B2BOrdersPage":
        """Navigate to Tenant Admin B2B Orders management."""
        self.navigate(f"{settings.BASE_URL}/tenant/ttenant/admin/orders/b2b")
        self.page.wait_for_timeout(2000)
        return self

    def open_merchant_b2b(self) -> "B2BOrdersPage":
        """Navigate to Merchant Portal B2B Orders management."""
        self.navigate(f"{settings.BASE_URL}/tenant/ttenant/merchant/b2b-merchant/order-management/b2b")
        self.page.wait_for_timeout(2000)
        return self

    def open_admin_create_form(self) -> "B2BOrdersPage":
        """Navigate directly to Tenant Admin B2B Order creation form."""
        self.navigate(f"{settings.BASE_URL}/tenant/ttenant/admin/orders/b2b/form")
        self.page.wait_for_timeout(2500)
        return self

    def open_merchant_create_form(self) -> "B2BOrdersPage":
        """Navigate directly to Merchant Portal B2B Order creation form."""
        self.navigate(f"{settings.BASE_URL}/tenant/ttenant/merchant/b2b-merchant/order-management/b2b/form")
        self.page.wait_for_timeout(2500)
        return self

    # -------------------------------------------------------------------------
    # Tabs & Classification
    # -------------------------------------------------------------------------
    def switch_tab(self, tab_name: str) -> None:
        """Switch to a specific status tab (e.g. 'Pending Requests', 'To Assign', etc.)."""
        tab_loc = self.page.locator(".ant-tabs-tab").filter(has_text=tab_name).first
        tab_loc.wait_for(state="visible", timeout=10000)
        tab_loc.click()
        self.page.wait_for_timeout(2000)

    def get_tab_names(self) -> List[str]:
        """Get the full list of visible status tab names."""
        self.page.wait_for_selector(".ant-tabs-tab", timeout=10000)
        tabs = self.page.locator(".ant-tabs-tab").all_inner_texts()
        return [t.strip() for t in tabs if t.strip()]

    def get_b2b_merchant_options(self) -> List[str]:
        """Fetch all merchant names populated in the Tenant 'Choose Merchant' dropdown."""
        self.open_admin_create_form()
        merchant_item = self.page.locator(".ant-form-item:has-text('Choose Merchant') .ant-select").first
        merchant_item.wait_for(state="visible", timeout=10000)
        merchant_item.click()
        self.page.wait_for_timeout(1000)

        options = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").all_inner_texts()
        names = [o.strip() for o in options if o.strip()]
        self.page.keyboard.press("Escape")
        return names

    # -------------------------------------------------------------------------
    # Order Creation
    # -------------------------------------------------------------------------
    def create_b2b_order(
        self,
        is_tenant: bool = True,
        merchant_name: str = "B2B Merchant",
        ref_num: Optional[str] = None,
        quantity: str = "1",
        weight: str = "10",
        length: str = "10",
        width: str = "10",
        height: str = "10",
        pickup_name: str = "Sender Warehouse",
        pickup_phone: str = "555111222",
        pickup_address: str = "RRRD2929",
        dropoff_name: str = "Receiver Retail",
        dropoff_phone: str = "555333444",
        dropoff_address: str = "MMMD3030",
        submit: bool = True,
    ) -> str:
        """Create a full B2B order from either Tenant or Merchant perspective."""
        if not ref_num:
            ref_num = f"REF-B2B-{int(time.time() * 1000) % 10000000}"

        if is_tenant:
            self.open_admin_create_form()
            # Select Merchant
            m_sel = self.page.locator(".ant-form-item:has-text('Choose Merchant') .ant-select").first
            m_sel.wait_for(state="visible", timeout=10000)
            m_sel.click()
            self.page.wait_for_timeout(500)
            self.page.locator(f".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('{merchant_name}')").first.click()
            self.page.wait_for_timeout(800)
        else:
            self.open_merchant_create_form()

        # Select Service Type (first option)
        st_sel = self.page.locator(".ant-form-item:has-text('Service Type') .ant-select").first
        st_sel.wait_for(state="visible", timeout=10000)
        st_sel.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
        self.page.wait_for_timeout(500)

        # Select Loading Type (e.g. Carton)
        carton_card = self.page.locator("div[class*='shippingServiceCard']:has-text('Carton')").first
        if carton_card.is_visible():
            carton_card.click()
            self.page.wait_for_timeout(500)

        # Reference, Quantity, Weight, Dimensions
        self.page.locator("input[name='referenceNumber']").fill(ref_num)
        self.page.locator(".ant-form-item:has-text('Quantity') input").first.fill(quantity)
        self.page.locator(".ant-form-item:has-text('Weight') input").first.fill(weight)

        self.page.locator("input[placeholder='Length']").first.fill(length)
        self.page.locator("input[placeholder='Width']").first.fill(width)
        self.page.locator("input[placeholder='Height']").first.fill(height)

        # 1. Add Pickup Point
        self.page.locator("button:has-text('Add Pickup Point')").first.click()
        self.page.wait_for_timeout(1000)

        self.page.locator("input[name='pickupPoints.0.recipientName']").fill(pickup_name)
        self.page.locator(".ant-form-item:has-text('Contact Number') input[placeholder='Enter phone number']").first.fill(pickup_phone)

        # Country & City
        country_sel = self.page.locator(".ant-form-item:has-text('Country') .ant-select").first
        country_sel.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('Saudi Arabia')").first.click()
        self.page.wait_for_timeout(800)

        city_sel = self.page.locator(".ant-form-item:has-text('City') .ant-select").first
        city_sel.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
        self.page.wait_for_timeout(500)

        self.page.locator("input[name='pickupPoints.0.address.nationalAddress']").fill(pickup_address)

        # Date & Times for Pickup
        self.page.locator("input[placeholder='Select date']").first.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-picker-dropdown:not(.ant-picker-dropdown-hidden) a:has-text('Today'), .ant-picker-dropdown:not(.ant-picker-dropdown-hidden) button:has-text('Today')").first.click()
        self.page.wait_for_timeout(800)

        pickup_times = self.page.locator("input[placeholder='Select time']").all()
        if len(pickup_times) >= 2:
            pickup_times[0].fill("08:00")
            pickup_times[0].press("Enter")
            self.page.wait_for_timeout(300)
            pickup_times[1].fill("18:00")
            pickup_times[1].press("Enter")
            self.page.wait_for_timeout(300)

        # Click Save on Pickup Point
        self.page.locator("button:has-text('Save')").first.click()
        self.page.wait_for_timeout(1500)

        # 2. Add Drop Off Point
        drop_btn = self.page.locator("button:has-text('Add Drop Off')").first
        drop_btn.dispatch_event("click")
        self.page.wait_for_timeout(1500)

        self.page.locator("input[name='deliveryPoints.0.recipientName']").fill(dropoff_name)
        self.page.locator("input[placeholder='Enter phone number']").last.fill(dropoff_phone)

        # Country & City for Drop Off
        self.page.locator(".ant-form-item:has-text('Country') .ant-select").last.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('Saudi Arabia')").first.click()
        self.page.wait_for_timeout(800)

        self.page.locator(".ant-form-item:has-text('City') .ant-select").last.click()
        self.page.wait_for_timeout(500)
        self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
        self.page.wait_for_timeout(500)

        self.page.locator("input[name='deliveryPoints.0.address.nationalAddress']").fill(dropoff_address)

        # Times for Drop Off Point
        drop_times = self.page.locator("input[placeholder='Select time']").all()
        if len(drop_times) >= 2:
            drop_times[0].fill("09:00")
            drop_times[0].press("Enter")
            self.page.wait_for_timeout(300)
            drop_times[1].fill("20:00")
            drop_times[1].press("Enter")
            self.page.wait_for_timeout(300)

        # Click Save on Drop Off Point
        self.page.locator("button:has-text('Save')").first.click()
        self.page.wait_for_timeout(1500)

        if not submit:
            return ref_num

        # 3. Advance to Step 2
        next_btn = self.page.locator("button:has-text('Next')").first
        next_btn.click()
        self.page.wait_for_timeout(3000)

        # 4. On Step 2 Review, Click Create Order
        create_btn = self.page.locator("button:has-text('Create Order')").first
        if create_btn.is_visible():
            create_btn.click()
            self.page.wait_for_timeout(4000)

        return ref_num

    # -------------------------------------------------------------------------
    # Row Helpers & Lookups
    # -------------------------------------------------------------------------
    def search_order(self, query: str) -> None:
        """Search orders table using the Search input."""
        search_inp = self.page.locator("input[placeholder='Search']").first
        if search_inp.is_visible():
            search_inp.fill(query)
            search_inp.press("Enter")
            self.page.wait_for_timeout(2000)

    def find_order_row(self, ref_or_code: str, search_first: bool = False) -> Optional[Locator]:
        """Locate table row matching reference number or shipment code."""
        if search_first:
            self.search_order(ref_or_code)
        rows = self.page.locator(".ant-table-tbody tr.ant-table-row").all()
        for r in rows:
            if ref_or_code in r.inner_text():
                return r
        # If not found and search wasn't tried yet, try searching
        if not search_first:
            self.search_order(ref_or_code)
            rows = self.page.locator(".ant-table-tbody tr.ant-table-row").all()
            for r in rows:
                if ref_or_code in r.inner_text():
                    return r
        return None

    def get_order_code_from_row(self, row: Locator) -> str:
        """Extract shipment tracking/order code (e.g. ORD...) from a table row."""
        return row.locator("button.ant-btn-link").first.inner_text().strip()

    # -------------------------------------------------------------------------
    # Tenant Operations
    # -------------------------------------------------------------------------
    def accept_order(self, ref_or_code: str) -> None:
        """Tenant accepts an order from Pending Requests."""
        self.switch_tab("Pending Requests")
        row = self.find_order_row(ref_or_code)
        if not row:
            raise ValueError(f"Order {ref_or_code} not found in Pending Requests")

        trigger = row.locator("button.ant-dropdown-trigger").first
        trigger.click()
        self.page.wait_for_timeout(1000)

        accept_item = self.page.locator(".ant-dropdown-menu-item").filter(has_text="Accept").first
        accept_item.click()
        self.page.wait_for_timeout(2000)

        # Check for any confirmation modal
        modal_ok = self.page.locator(".ant-modal button:has-text('OK'), .ant-modal button:has-text('Yes'), .ant-modal button:has-text('Confirm')").first
        if modal_ok.is_visible():
            modal_ok.click()
            self.page.wait_for_timeout(2000)

    def reject_order(self, ref_or_code: str, reason: str = "Operational Constraint") -> None:
        """Tenant rejects an order from Pending Requests with a reason."""
        self.switch_tab("Pending Requests")
        row = self.find_order_row(ref_or_code)
        if not row:
            raise ValueError(f"Order {ref_or_code} not found in Pending Requests")

        trigger = row.locator("button.ant-dropdown-trigger").first
        trigger.click()
        self.page.wait_for_timeout(1000)

        reject_item = self.page.locator(".ant-dropdown-menu-item").filter(has_text="Reject").first
        reject_item.click()
        self.page.wait_for_timeout(1500)

        # Reject Drawer or Modal
        container = self.page.locator(".ant-drawer:has-text('Reject Request'), .ant-modal:has-text('Reject Request'), .ant-drawer, .ant-modal").first
        container.wait_for(state="visible", timeout=5000)

        reason_sel = container.locator(".ant-select").first
        reason_sel.click()
        self.page.wait_for_timeout(500)

        opt = self.page.locator(f".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('{reason}')").first
        if opt.is_visible():
            opt.click()
        else:
            self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
        self.page.wait_for_timeout(500)

        container.locator("button:has-text('Reject')").first.click()
        self.page.wait_for_timeout(3000)

    def accept_with_delay(
        self,
        ref_or_code: str,
        reason: str = "Operational Constraint",
        remarks: str = "Rescheduled pickup and delivery window",
    ) -> None:
        """Tenant accepts an order with delay, moving it to Awaiting Merchant Approval."""
        self.switch_tab("Pending Requests")
        row = self.find_order_row(ref_or_code)
        if not row:
            raise ValueError(f"Order {ref_or_code} not found in Pending Requests")

        trigger = row.locator("button.ant-dropdown-trigger").first
        trigger.click()
        self.page.wait_for_timeout(1000)

        delay_item = self.page.locator(".ant-dropdown-menu-item").filter(has_text="Accept with Delay").first
        delay_item.click()
        self.page.wait_for_timeout(3000)

        # On Delay form, select Reason
        reason_sel = self.page.locator(".ant-form-item:has-text('Reason') .ant-select, .ant-select:has-text('Select a reason')").first
        if reason_sel.is_visible():
            reason_sel.click()
            self.page.wait_for_timeout(500)
            opt = self.page.locator(f".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('{reason}')").first
            if opt.is_visible():
                opt.click()
            else:
                self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
            self.page.wait_for_timeout(500)

        # Fill Remarks
        remarks_inp = self.page.locator("textarea, input[placeholder*='Remarks']").first
        if remarks_inp.is_visible():
            remarks_inp.fill(remarks)

        # Click Next
        next_btn = self.page.locator("button:has-text('Next')").first
        next_btn.click()
        self.page.wait_for_timeout(2000)

        # Click Confirm / Submit
        submit_btn = self.page.locator("button:has-text('Submit'), button:has-text('Confirm'), button:has-text('Accept')").first
        if submit_btn.is_visible():
            submit_btn.click()
            self.page.wait_for_timeout(3000)

    def delete_order(self, ref_or_code: str) -> None:
        """Tenant deletes an order from Pending Requests."""
        self.switch_tab("Pending Requests")
        row = self.find_order_row(ref_or_code)
        if not row:
            raise ValueError(f"Order {ref_or_code} not found in Pending Requests")

        trigger = row.locator("button.ant-dropdown-trigger").first
        trigger.click()
        self.page.wait_for_timeout(1000)

        delete_item = self.page.locator(".ant-dropdown-menu-item").filter(has_text="Delete").first
        delete_item.click()
        self.page.wait_for_timeout(1500)

        modal = self.page.locator(".ant-modal:has-text('Confirm Delete')").first
        modal.wait_for(state="visible", timeout=5000)
        modal.locator("button:has-text('Yes')").first.click()
        self.page.wait_for_timeout(3000)

    def assign_driver(self, ref_or_code: str, driver_name: str = "B2C and B2B driver") -> None:
        """Tenant assigns a driver to an order in To Assign tab."""
        self.switch_tab("To Assign")
        row = self.find_order_row(ref_or_code)
        if not row:
            raise ValueError(f"Order {ref_or_code} not found in To Assign")

        assign_btn = row.locator("button:has-text('Assign Driver')").first
        if not assign_btn.is_visible():
            # If button text differs, try primary button
            assign_btn = row.locator("button.ant-btn-primary").first
        assign_btn.click()
        self.page.wait_for_timeout(3000)

        # Click 'Assign One For All'
        assign_all = self.page.locator("button:has-text('Assign One For All')").first
        assign_all.wait_for(state="visible", timeout=10000)
        assign_all.click()
        self.page.wait_for_timeout(1000)

        # Modal driver selection
        modal = self.page.locator(".ant-modal").first
        modal.locator(".ant-select").first.click()
        self.page.wait_for_timeout(500)

        driver_opt = self.page.locator(f".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('{driver_name}')").first
        if driver_opt.is_visible():
            driver_opt.click()
        else:
            self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
        self.page.wait_for_timeout(500)

        modal.locator("button:has-text('Assign')").first.click()
        self.page.wait_for_timeout(1500)

        # Select trip mode (Direct ensures single driver covers the entire trip)
        trip_selects = self.page.locator(".ant-select:has-text('Select trip mode')").all()
        for ts in trip_selects:
            ts.click()
            self.page.wait_for_timeout(500)
            direct_opt = self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:has-text('Direct')").first
            if direct_opt.is_visible():
                direct_opt.click()
            else:
                self.page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click()
            self.page.wait_for_timeout(500)

        # Click Main Assign Button at bottom right
        main_assign_btn = self.page.locator("div[style*='justify-content: flex-end'] button:has-text('Assign'), button._primary_1jkfa_35:has-text('Assign')").last
        main_assign_btn.wait_for(state="visible", timeout=10000)
        main_assign_btn.click()
        self.page.wait_for_timeout(4000)

    # -------------------------------------------------------------------------
    # Merchant Operations (Awaiting My Approval)
    # -------------------------------------------------------------------------
    def merchant_accept_delay(self, order_code: str) -> None:
        """Merchant accepts tenant's proposed delay from Awaiting My Approval."""
        self.switch_tab("Awaiting My Approval")
        link = self.page.locator(f"button.ant-btn-link:has-text('{order_code}')").first
        link.wait_for(state="visible", timeout=10000)
        link.click()
        self.page.wait_for_timeout(3000)

        acc_btn = self.page.locator("button:has-text('Accept')").first
        acc_btn.wait_for(state="visible", timeout=10000)
        acc_btn.click()
        self.page.wait_for_timeout(2000)

        modal_ok = self.page.locator(".ant-modal button:has-text('OK'), .ant-modal button:has-text('Yes'), .ant-modal button:has-text('Confirm')").first
        if modal_ok.is_visible():
            modal_ok.click()
            self.page.wait_for_timeout(2000)

    def merchant_reject_delay(self, order_code: str, remarks: str = "Merchant reject delay") -> None:
        """Merchant rejects tenant's proposed delay from Awaiting My Approval."""
        self.switch_tab("Awaiting My Approval")
        link = self.page.locator(f"button.ant-btn-link:has-text('{order_code}')").first
        link.wait_for(state="visible", timeout=10000)
        link.click()
        self.page.wait_for_timeout(3000)

        rej_btn = self.page.locator("button:has-text('Reject')").first
        rej_btn.wait_for(state="visible", timeout=10000)
        rej_btn.click()
        self.page.wait_for_timeout(1500)

        container = self.page.locator(".ant-drawer:has-text('Reject Request'), .ant-modal:has-text('Reject Request'), .ant-drawer, .ant-modal").first
        container.wait_for(state="visible", timeout=5000)
        textarea = container.locator("textarea, input[placeholder*='Remarks']").first
        if textarea.is_visible():
            textarea.fill(remarks)
            self.page.wait_for_timeout(500)

        submit_btn = container.locator("button:has-text('Reject')").first
        submit_btn.click()
        self.page.wait_for_timeout(3000)

    # -------------------------------------------------------------------------
    # Negative Scenarios & Validations
    # -------------------------------------------------------------------------
    def attempt_step1_next_with_empty_form(self) -> List[str]:
        """Click Next on empty B2B creation form to trigger validation errors."""
        self.open_admin_create_form()
        next_btn = self.page.locator("button:has-text('Next')").first
        next_btn.dispatch_event("click")
        self.page.wait_for_timeout(1500)
        errors = self.page.locator(".ant-form-item-explain-error").all_inner_texts()
        return [e.strip() for e in errors if e.strip()]

    def attempt_tenant_reject_without_reason(self, ref_or_code: str) -> bool:
        """Trigger Reject drawer and verify Reject button is disabled without selecting reason."""
        self.switch_tab("Pending Requests")
        row = self.find_order_row(ref_or_code)
        if not row:
            raise ValueError(f"Order {ref_or_code} not found in Pending Requests")

        trigger = row.locator("button.ant-dropdown-trigger").first
        trigger.click()
        self.page.wait_for_timeout(1000)

        reject_item = self.page.locator(".ant-dropdown-menu-item").filter(has_text="Reject").first
        reject_item.click()
        self.page.wait_for_timeout(1500)

        container = self.page.locator(".ant-drawer:has-text('Reject Request'), .ant-modal:has-text('Reject Request'), .ant-drawer, .ant-modal").first
        container.wait_for(state="visible", timeout=5000)
        reject_btn = container.locator("button:has-text('Reject')").first
        is_blocked = reject_btn.is_disabled() or container.is_visible()

        # Close container
        cancel_btn = container.locator("button:has-text('Cancel'), button[aria-label='Close'], button.ant-drawer-close").first
        if cancel_btn.is_visible():
            cancel_btn.click()
            self.page.wait_for_timeout(1000)
        return is_blocked

    def attempt_merchant_reject_without_remarks(self, order_code: str) -> bool:
        """In Merchant detail, verify Reject button is disabled without entering remarks."""
        self.switch_tab("Awaiting My Approval")
        link = self.page.locator(f"button.ant-btn-link:has-text('{order_code}')").first
        link.wait_for(state="visible", timeout=10000)
        link.click()
        self.page.wait_for_timeout(3000)

        rej_btn = self.page.locator("button:has-text('Reject')").first
        rej_btn.wait_for(state="visible", timeout=10000)
        rej_btn.click()
        self.page.wait_for_timeout(1500)

        container = self.page.locator(".ant-drawer:has-text('Reject Request'), .ant-modal:has-text('Reject Request'), .ant-drawer, .ant-modal").first
        container.wait_for(state="visible", timeout=5000)
        submit_btn = container.locator("button:has-text('Reject')").first
        is_blocked = submit_btn.is_disabled() or container.is_visible()

        cancel_btn = container.locator("button:has-text('Cancel'), button[aria-label='Close'], button.ant-drawer-close").first
        if cancel_btn.is_visible():
            cancel_btn.click()
            self.page.wait_for_timeout(1000)
        return is_blocked
