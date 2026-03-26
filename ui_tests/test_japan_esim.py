import pytest
from playwright.sync_api import Page

from ui_tests.pages.home_page import HomePage
from ui_tests.pages.japan_page import JapanEsimPage
from ui_tests.utils import extract_price


@pytest.fixture(scope="session")
def context(browser):
    ctx = browser.new_context(permissions=[])
    yield ctx
    ctx.close()


@pytest.fixture
def page(context):
    p = context.new_page()
    yield p
    p.close()


def test_japan_7day_unlimited_price_matches_buy_now(page: Page):
    """
    Verify that the price shown on the Japan 7-day Unlimited eSIM package card
    matches the total price displayed next to the Buy Now button.
    """
    home = HomePage(page)
    home.navigate()
    home.search_country("Japan")
    home.select_country_result("Japan")

    japan = JapanEsimPage(page)
    japan.wait_for_page()
    japan.select_plan_tab("Unlimited")

    card = japan.get_package_card("7 days")
    card_price_text = japan.get_card_price_text(card)
    card_price = extract_price(card_price_text)
    assert card_price, f"Could not parse price from package card: '{card_price_text}'"

    japan.select_package("7 days")

    buy_now_price_text = japan.get_buy_now_price_text()
    buy_now_price = extract_price(buy_now_price_text)
    assert buy_now_price, f"Could not parse price from Buy Now panel: '{buy_now_price_text}'"

    japan.take_screenshot("screenshots/japan_7day_unlimited_price_verification.png")

    assert card_price == buy_now_price, (
        f"Price mismatch — card: {card_price_text} | Buy Now: {buy_now_price_text}"
    )
