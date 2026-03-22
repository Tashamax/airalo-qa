import re
import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def context(browser):
    context = browser.new_context(permissions=[])
    yield context
    context.close()


@pytest.fixture
def page(context):
    page = context.new_page()
    yield page
    page.close()


def extract_price(text):
    """Extract numeric price — supports £, $, €."""
    match = re.search(r"[£$€]([\d.]+)", text)
    return match.group(1) if match else None


def test_japan_7day_unlimited_price_matches_buy_now(page: Page):
    """
    Verify that the price of the Japan 7-day Unlimited eSIM package
    matches the price displayed next to the Buy Now button.
    """

    # Step 1: Open Airalo's website
    page.goto("https://www.airalo.com")
    page.wait_for_load_state("domcontentloaded")

    # Step 2: Accept cookie consent popup
    try:
        accept_btn = page.get_by_role("button", name=re.compile("^accept$", re.IGNORECASE))
        accept_btn.wait_for(state="visible", timeout=5000)
        accept_btn.click()
        page.wait_for_timeout(1000)
    except Exception:
        pass

    # Step 3: Search for Japan
    search_input = page.get_by_placeholder("Where do you need an eSIM?")
    search_input.wait_for(state="visible", timeout=10000)
    search_input.click()
    search_input.fill("Japan")
    page.wait_for_timeout(1000)

    # Step 4: Click Japan in the dropdown
    japan_result = page.locator("li, div[role='option'], a").filter(
        has_text=re.compile(r"^Japan$", re.IGNORECASE)
    ).first
    japan_result.wait_for(state="visible", timeout=10000)
    japan_result.click()

    # Step 5: Wait for Japan page and scroll down
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)
    page.keyboard.press("PageDown")
    page.wait_for_timeout(1000)

    # Step 6: Click the Unlimited tab
    unlimited_tab = page.locator("text=Unlimited").first
    unlimited_tab.wait_for(state="visible", timeout=10000)
    unlimited_tab.click()
    page.wait_for_timeout(1000)

    # Step 7: Find "7 days" heading then get the next sibling card
    seven_day_heading = page.locator("text=/^7 days$/i").first
    seven_day_heading.wait_for(state="visible", timeout=10000)
    seven_day_card = seven_day_heading.locator("xpath=following-sibling::*[1]")

    # Step 8: Get the price from the card
    package_price_text = seven_day_card.locator("text=/[£$€][\\d.]+/").first.inner_text()
    package_amount = extract_price(package_price_text)
    assert package_amount, f"Could not extract price from card: '{package_price_text}'"

    # Step 9: Click the card to select it
    seven_day_card.click()
    page.wait_for_timeout(1000)

    # Step 10: Get the Buy Now total price
    buy_now_price_text = page.locator("text=/Total/").locator("..").locator("text=/[£$€][\\d.]+/").first.inner_text()
    buy_now_amount = extract_price(buy_now_price_text)
    assert buy_now_amount, f"Could not extract Buy Now price: '{buy_now_price_text}'"

    # Step 11: Screenshot before assertion — captures the result state
    page.screenshot(path="screenshots/japan_7day_unlimited_price_verification.png", full_page=False)

    # Step 12: Assert prices match
    assert package_amount == buy_now_amount, (
        f"Price mismatch! Card: {package_price_text} | Buy Now: {buy_now_price_text}"
    )

    print(f"\n✅ Price verified: {package_price_text} matches Buy Now button")
