import re
import logging

from playwright.sync_api import Page, Locator
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

# Maps plan tab names to their stable data-testid values
_TAB_TESTID = {
    "Data": "segmented-control_tab-data",
    "Unlimited": "segmented-control_tab-unlimited",
    "Voice": "segmented-control_tab-voice",
}


class JapanEsimPage:

    def __init__(self, page: Page) -> None:
        self._page = page

    def wait_for_page(self) -> "JapanEsimPage":
        self._page.wait_for_url("**/japan**", timeout=30_000)
        # Scroll down so plan tabs and package cards enter the viewport
        self._page.keyboard.press("PageDown")
        return self

    def select_plan_tab(self, tab_name: str) -> None:
        """Click a plan type tab by its stable data-testid attribute."""
        testid = _TAB_TESTID.get(tab_name)
        if testid:
            tab = self._page.locator(f'[data-testid="{testid}"]')
        else:
            # Fallback: match by exact visible text for unknown tab names
            tab = self._page.get_by_role("tab", name=tab_name, exact=True)
        expect(tab).to_be_visible(timeout=10_000)
        tab.click()
        expect(self._package_buttons).not_to_have_count(0)

    @property
    def _package_buttons(self) -> Locator:
        """All package selection buttons on the page."""
        return self._page.locator('[data-testid="package-grouped-packages_package-button"]')

    def _get_package_button(self, duration_label: str) -> Locator:
        """
        Find the package button for a given duration (e.g. '7 days').
        Each button carries aria-label="Select <plan> - <duration> for <price>."
        which reliably encodes the duration label.
        """
        btn = self._page.locator(
            f'[data-testid="package-grouped-packages_package-button"]'
            f'[aria-label*="{duration_label}"]'
        )
        expect(btn).to_be_visible()
        return btn

    def get_package_card(self, duration_label: str) -> Locator:
        """Return the package button locator (used by callers to extract price)."""
        return self._get_package_button(duration_label)

    def get_card_price_text(self, card: Locator) -> str:
        price_el = card.locator('[data-testid="price_amount"]')
        expect(price_el).to_be_visible()
        return price_el.inner_text()

    def select_package(self, duration_label: str) -> None:
        """Click the package button and wait for the buy-now panel to appear."""
        btn = self._get_package_button(duration_label)
        btn.scroll_into_view_if_needed()
        btn.click()
        self._page.screenshot(path="screenshots/debug_after_card_click.png")
        logger.info("URL after card click: %s", self._page.url)
        expect(self._buy_now_section).to_be_visible(timeout=15_000)

    @property
    def _buy_now_section(self) -> Locator:
        """
        The sticky cart footer — mounted dynamically via Nuxt teleport.
        Identified by its stable ARIA attributes: role=dialog + aria-live=polite.
        """
        return self._page.locator("[role='dialog'][aria-live='polite']")

    def get_buy_now_price_text(self) -> str:
        section = self._buy_now_section
        expect(section).to_be_visible(timeout=15_000)
        price_el = section.locator('[data-testid="price_amount"]')
        expect(price_el).to_be_visible()
        return price_el.inner_text()

    def take_screenshot(self, path: str) -> None:
        self._page.screenshot(path=path, full_page=False)
        logger.info("Screenshot saved to %s", path)
