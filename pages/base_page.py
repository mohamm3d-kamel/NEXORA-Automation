from typing import Union
from playwright.sync_api import Page, Locator, expect
from config.settings import settings

class BasePage:
    """Base class for all Page Objects in the Nexora automation framework."""

    def __init__(self, page: Page):
        self.page = page
        self.default_timeout = settings.DEFAULT_TIMEOUT
        self.apply_zoom(settings.DEFAULT_ZOOM)

    def apply_zoom(self, zoom: str = "67%") -> None:
        """Inject and enforce zoom level across page lifecycle."""
        try:
            self.page.context.add_init_script(f"""
                function setAppZoom() {{
                    if (document.documentElement) document.documentElement.style.zoom = '{zoom}';
                    if (document.body) document.body.style.zoom = '{zoom}';
                }}
                setAppZoom();
                window.addEventListener('DOMContentLoaded', setAppZoom);
                window.addEventListener('load', setAppZoom);
            """)
        except Exception:
            pass
        try:
            self.page.evaluate(f"if (document.body) document.body.style.zoom = '{zoom}';")
        except Exception:
            pass

    def navigate(self, url: str) -> None:
        """Navigate to a specified URL and enforce zoom."""
        self.page.goto(url, wait_until="domcontentloaded", timeout=self.default_timeout)
        try:
            self.page.evaluate(f"if (document.body) document.body.style.zoom = '{settings.DEFAULT_ZOOM}';")
        except Exception:
            pass

    @property
    def current_url(self) -> str:
        """Returns the current page URL."""
        return self.page.url

    @property
    def title(self) -> str:
        """Returns current page title."""
        return self.page.title()

    def wait_for_url(self, url_pattern: str, timeout: int = None) -> None:
        """Wait until page URL matches the pattern."""
        self.page.wait_for_url(url_pattern, timeout=timeout or self.default_timeout)

    def wait_for_load(self, state: str = "networkidle") -> None:
        """Wait for page load state."""
        self.page.wait_for_load_state(state, timeout=self.default_timeout)

    def take_screenshot(self, filepath: str) -> None:
        """Capture screenshot to the given path."""
        self.page.screenshot(path=filepath, full_page=True)

    def resolve_locator(self, target: Union[str, Locator]) -> Locator:
        """Helper to resolve selector string or return locator directly."""
        if isinstance(target, str):
            return self.page.locator(target)
        return target

    def click(self, target: Union[str, Locator]) -> None:
        """Click on an element."""
        locator = self.resolve_locator(target)
        locator.wait_for(state="visible", timeout=self.default_timeout)
        locator.click()

    def fill(self, target: Union[str, Locator], text: str) -> None:
        """Fill text into an input field."""
        locator = self.resolve_locator(target)
        locator.wait_for(state="visible", timeout=self.default_timeout)
        locator.fill(text)

    def clear(self, target: Union[str, Locator]) -> None:
        """Clear text from an input field."""
        locator = self.resolve_locator(target)
        locator.fill("")

    def get_text(self, target: Union[str, Locator]) -> str:
        """Retrieve inner text of an element."""
        locator = self.resolve_locator(target)
        locator.wait_for(state="visible", timeout=self.default_timeout)
        return locator.inner_text().strip()

    def is_visible(self, target: Union[str, Locator], timeout: int = 5000) -> bool:
        """Check if an element is visible within timeout."""
        locator = self.resolve_locator(target)
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False
