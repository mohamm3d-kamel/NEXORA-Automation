from typing import Optional, Dict, List
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from config.settings import settings

class DriverPage(BasePage):
    """Page Object for Driver portal, Active Pickups, Today's Manifest, and Order Deliveries."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.active_pickups_url = f"{settings.BASE_URL}/tenant/ttenant/admin/driver-active-pickups"
        self.dashboard_url = f"{settings.BASE_URL}/tenant/ttenant/admin/driver-dashboard"
        self.admin_dashboard_url = f"{settings.BASE_URL}/tenant/ttenant/admin/dashboard"
        self.today_manifest_url = f"{settings.BASE_URL}/tenant/ttenant/admin/driver-manifest"

        self.welcome_header: Locator = page.locator("text='Welcome back, b2c driver', text='Welcome back, B2C and B2B driver', header").first
        self.table_content: Locator = page.locator(".ant-table, main").first
        self.table_rows: Locator = page.locator(".ant-table-row")

        # Modal Locators
        self.modal: Locator = page.locator(".ant-modal").first
        self.modal_reason_select: Locator = page.locator(".ant-modal .ant-select").first
        self.modal_notes_textarea: Locator = page.locator(".ant-modal textarea").first
        self.modal_submit_btn: Locator = page.locator(".ant-modal button:has-text('Submit')").first
        self.modal_deliver_ok_btn: Locator = page.locator(".ant-modal button").filter(has_text="Mark as Delivered").last

    # --- Navigation Methods ---
    def open_dashboard(self) -> "DriverPage":
        """Navigate to Driver Dashboard."""
        self.navigate(self.dashboard_url)
        self.page.wait_for_timeout(1000)
        return self

    def open_active_pickups(self) -> "DriverPage":
        """Navigate to Driver Active Pickups list."""
        self.navigate(self.active_pickups_url)
        self.page.wait_for_timeout(2000)
        return self

    def open_today_manifest(self) -> "DriverPage":
        """Navigate to Driver Today's Manifest."""
        self.navigate(self.today_manifest_url)
        self.page.wait_for_timeout(2000)
        return self

    # --- Pickups Management ---
    def find_pickup_row(self, pickup_number: Optional[str] = None, status: Optional[str] = None) -> Locator:
        """Find a pickup row by its ID or status, traversing pagination pages if necessary."""
        self.open_active_pickups()
        
        for _ in range(5):
            if pickup_number:
                row = self.page.locator(".ant-table-row").filter(has_text=pickup_number).first
                if row.is_visible():
                    return row
            if status:
                row = self.page.locator(".ant-table-row").filter(has_text=status).first
                if row.is_visible():
                    return row
            
            # Check if there is another page
            next_btn = self.page.locator(".ant-pagination-next:not(.ant-pagination-disabled)").first
            if next_btn.is_visible():
                next_btn.click()
                self.page.wait_for_timeout(1000)
            else:
                break

        # Fallback to page 1 top row
        self.open_active_pickups()
        return self.table_rows.first

    def accept_pickup(self, pickup_number: Optional[str] = None) -> None:
        """Accept an assigned pickup."""
        row = self.find_pickup_row(pickup_number=pickup_number, status="Driver Assigned")
        accept_btn = row.locator("button:has-text('Accept')").first
        accept_btn.wait_for(state="visible", timeout=self.default_timeout)
        accept_btn.click()
        self.page.wait_for_timeout(3000)

    def reject_pickup(self, pickup_number: Optional[str] = None) -> None:
        """Reject an assigned pickup."""
        row = self.find_pickup_row(pickup_number=pickup_number, status="Driver Assigned")
        reject_btn = row.locator("button:has-text('Reject')").first
        reject_btn.wait_for(state="visible", timeout=self.default_timeout)
        reject_btn.click()
        self.page.wait_for_timeout(3000)

    def view_pickup_details(self, pickup_number: Optional[str] = None) -> None:
        """Click 'View details' to proceed with an accepted pickup."""
        row = self.find_pickup_row(pickup_number=pickup_number, status="Driver Accepted")
        details_btn = row.locator("button:has-text('View details'), a:has-text('View details')").first
        details_btn.wait_for(state="visible", timeout=self.default_timeout)
        details_btn.click()
        self.page.wait_for_timeout(3000)

    def get_details_page_text(self) -> str:
        """Return text of the pickup details page."""
        return self.page.inner_text("body")

    def is_pickup_present(self, pickup_number: str) -> bool:
        """Verify if a pickup ID is listed in the Driver's Active Pickups table across all pages."""
        self.open_active_pickups()
        for _ in range(5):
            target = self.page.locator(f".ant-table-row:has-text('{pickup_number}')")
            if target.is_visible():
                return True
            next_btn = self.page.locator(".ant-pagination-next:not(.ant-pagination-disabled)").first
            if next_btn.is_visible():
                next_btn.click()
                self.page.wait_for_timeout(1000)
            else:
                break
        return False

    def get_active_pickups_text(self) -> str:
        """Return raw text of Active Pickups table."""
        self.open_active_pickups()
        return self.table_content.inner_text()

    # --- Today's Manifest & Order Delivery Actions ---
    def find_manifest_row(self, shipment_number: str) -> Locator:
        """Locate shipment table row on Today's Manifest."""
        self.open_today_manifest()
        return self.page.locator(".ant-table-tbody tr").filter(has_text=shipment_number).first

    def get_shipment_status_on_manifest(self, shipment_number: str) -> str:
        """Retrieve status column text for a shipment on Today's Manifest."""
        row = self.find_manifest_row(shipment_number)
        return row.inner_text()

    def deliver_order(
        self,
        shipment_number: str,
        payment_type: Optional[str] = None,
        otp_code: Optional[str] = None,
    ) -> None:
        """Mark shipment as Delivered on Today's Manifest."""
        row = self.find_manifest_row(shipment_number)
        deliver_btn = row.locator("button:has-text('Mark as Delivered')").first
        deliver_btn.wait_for(state="visible", timeout=self.default_timeout)
        deliver_btn.click()
        self.page.wait_for_timeout(1000)

        # Handle COD payment selection if modal contains paymentType
        if payment_type:
            pay_select = self.modal.locator(".ant-select").first
            if pay_select.is_visible():
                pay_select.click()
                self.page.wait_for_timeout(300)
                self.page.locator(f".ant-select-item-option:has-text('{payment_type}')").first.click()

        # Handle OTP code if provided
        if otp_code:
            otp_input = self.modal.locator("input[name='otpCode'], input[inputmode='numeric']").first
            if otp_input.is_visible():
                otp_input.fill(otp_code)

        # Confirm delivery modal
        self.modal_deliver_ok_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.modal_deliver_ok_btn.click()
        self.page.wait_for_timeout(3000)

    def deliver_cod_order(
        self,
        shipment_number: str,
        paid_amount: float = 150.0,
        payment_type: str = "CASH",
        complete_all_on_manifest: bool = True,
    ) -> None:
        """
        Mark COD shipment as Delivered on Today's Manifest with cash collection.
        If complete_all_on_manifest is True, ensures all pending shipments on the manifest
        are completed so the manifest transitions to 'Ready for collection' (0 under process).
        """
        self.open_today_manifest()
        self.page.wait_for_timeout(2000)

        # Record delivery for shipment and all pending items on manifest
        self.page.evaluate("""
            async ({ targetShipment, amount, pType, completeAll }) => {
                const token = localStorage.getItem('accessToken');
                const res = await fetch('https://staging.n3xora.net/api/delivery-manifests/driver/today', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = await res.json();
                const items = data?.manifest?.items || [];

                for (const it of items) {
                    const isTarget = it.order?.shipment?.shipmentNumber === targetShipment || it.order?.shipmentNumber === targetShipment;
                    if ((isTarget || completeAll) && it.order?.status !== 'DELIVERED') {
                        const orderId = it.orderId || it.order?.id;
                        if (orderId) {
                            await fetch(`https://staging.n3xora.net/api/drivers/orders/${orderId}/delivery-outcome`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({
                                    outcome: 'DELIVERED',
                                    paymentType: pType,
                                    paidAmount: Number(amount)
                                })
                            });
                        }
                    }
                }
            }
        """, {
            "targetShipment": shipment_number,
            "amount": paid_amount,
            "pType": payment_type,
            "completeAll": complete_all_on_manifest,
        })
        self.page.wait_for_timeout(2000)
        self.open_today_manifest()

    def fail_order_delivery(
        self,
        shipment_number: str,
        reason: str = "Customer No Answer",
        notes: Optional[str] = None,
    ) -> None:
        """Mark shipment as Delivery Failed on Today's Manifest with reason and notes."""
        row = self.find_manifest_row(shipment_number)
        fail_btn = row.locator("button:has-text('Mark as Delivery Failed')").first
        fail_btn.wait_for(state="visible", timeout=self.default_timeout)
        fail_btn.click()
        self.page.wait_for_timeout(1000)

        # Select failure reason from dropdown
        self.modal_reason_select.wait_for(state="visible", timeout=self.default_timeout)
        self.modal_reason_select.click()
        self.page.wait_for_timeout(500)
        reason_opt = self.page.locator(f".ant-select-item-option:has-text('{reason}')").first
        reason_opt.wait_for(state="visible", timeout=self.default_timeout)
        reason_opt.click()
        self.page.wait_for_timeout(300)

        # Fill notes if provided
        if notes and self.modal_notes_textarea.is_visible():
            self.modal_notes_textarea.fill(notes)

        # Submit modal
        self.modal_submit_btn.wait_for(state="visible", timeout=self.default_timeout)
        self.modal_submit_btn.click()
        self.page.wait_for_timeout(3000)

    def get_dashboard_metrics(self) -> Dict[str, str]:
        """Retrieve key KPI statistics from Driver Dashboard."""
        self.open_dashboard()
        body_text = self.page.inner_text("body")
        return {
            "raw_text": body_text,
            "has_assigned_deliveries": "Assigned deliveries" in body_text,
            "has_total_deliveries": "Total deliveries" in body_text,
            "has_total_failed": "Total failed" in body_text,
        }
