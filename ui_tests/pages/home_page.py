import re
import logging

from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

COOKIE_ACCEPT_TIMEOUT_MS = 5_000


class HomePage:
    URL = "https://www.airalo.com"

    def __init__(self, page: Page) -> None:
        self._page = page
        # Airalo uses a custom search component — the hint text is a <span>
        # overlay, not a real placeholder attribute. Use role/CSS selectors
        # that target the actual input element regardless of visual styling.
        self._search_input: Locator = page.locator(
            "input[placeholder*='eSIM' i], "
            "input[placeholder*='where' i], "
            "[role='combobox'], "
            "[role='searchbox'], "
            "input[type='search']"
        ).first

    def navigate(self) -> "HomePage":
        self._page.goto(self.URL, wait_until="load", timeout=60_000)
        self._dismiss_cookie_banner()
        return self

    def _dismiss_cookie_banner(self) -> None:
        accept_btn = self._page.get_by_role(
            "button", name=re.compile(r"^accept$", re.IGNORECASE)
        )
        try:
            accept_btn.wait_for(state="visible", timeout=COOKIE_ACCEPT_TIMEOUT_MS)
            accept_btn.click()
            expect(accept_btn).not_to_be_visible(timeout=3_000)
            logger.debug("Cookie banner dismissed")
        except PlaywrightTimeoutError:
            logger.debug("Cookie banner not present — continuing")

    def search_country(self, country: str) -> None:
        expect(self._search_input).to_be_visible(timeout=20_000)
        self._search_input.click()
        self._search_input.fill(country)

    def select_country_result(self, country: str) -> None:
        """Click the dropdown result that matches the country name (including flag emoji)."""
        result = self._page.locator("li, [role='option']").filter(
            has_text=re.compile(rf"\b{re.escape(country)}\b", re.IGNORECASE)
        ).first
        expect(result).to_be_visible()
        result.click()
