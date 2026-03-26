import re
import logging

from playwright.sync_api import Page, Locator
from playwright.sync_api import expect

logger = logging.getLogger(__name__)


class JapanEsimPage:

    def __init__(self, page: Page) -> None:
        self._page = page

    def wait_for_page(self) -> "JapanEsimPage":
        self._page.wait_for_load_state("networkidle", timeout=30_000)
        # Scroll down so plan tabs and package cards enter the viewport
        self._page.keyboard.press("PageDown")
        return self

    def select_plan_tab(self, tab_name: str) -> None:
        """
        Click a plan type tab (e.g. 'Unlimited').
        Uses get_by_text(exact=True) which matches any element type whose
        full text is exactly tab_name — no DOM structure assumptions needed.
        """
        tab = self._page.get_by_text(tab_name, exact=True).first
        expect(tab).to_be_visible(timeout=10_000)
        tab.click()
        expect(self._package_cards).not_to_have_count(0)

    @property
    def _package_cards(self) -> Locator:
        """All visible package cards on the page."""
        return self._page.locator("div, li, article").filter(
            has=self._page.locator("text=/[£$€][\\d.]+/")
        )

    def get_package_card(self, duration_label: str) -> Locator:
        """
        Find the package card for a given duration (e.g. '7 days').
        Uses a container filter instead of XPath sibling traversal.
        """
        card = self._page.locator("div, li, article").filter(
            has=self._page.locator(f"text=/^{re.escape(duration_label)}$/i")
        ).filter(
            has=self._page.locator("text=/[£$€][\\d.]+/")
        ).first
        expect(card).to_be_visible()
        return card

    def get_card_price_text(self, card: Locator) -> str:
        price_el = card.locator("text=/[£$€][\\d.]+/").last
        expect(price_el).to_be_visible()
        return price_el.inner_text()

    def select_package(self, duration_label: str) -> None:
        """Click a package card and wait for the buy-now panel to appear."""
        card = self.get_package_card(duration_label)
        card.click()
        expect(self._buy_now_button).to_be_visible(timeout=10_000)

    @property
    def _buy_now_button(self) -> Locator:
        """The Buy Now button — matched by text regardless of element type."""
        return self._page.get_by_text("Buy now", exact=True).first

    @property
    def _buy_now_section(self) -> Locator:
        """
        The sticky footer containing the Buy Now button and total price.
        Scoped to a container that holds the Buy Now text — avoids
        brittle parent traversal with locator('..').
        """
        return self._page.locator("div, footer, section").filter(
            has=self._page.get_by_text("Buy now", exact=True)
        ).last

    def get_buy_now_price_text(self) -> str:
        price_el = self._buy_now_section.locator("text=/[£$€][\\d.]+/").first
        expect(price_el).to_be_visible()
        return price_el.inner_text()

    def take_screenshot(self, path: str) -> None:
        self._page.screenshot(path=path, full_page=False)
        logger.info("Screenshot saved to %s", path)
