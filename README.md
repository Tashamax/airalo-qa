# Airalo QA Coding Exercise

Automated test suite covering UI and API for the Airalo platform, built with Python, Pytest, and Playwright.

---

## Project Structure

```
airalo-qa/
├── api_tests/
│   └── test_airalo_api.py    # Partner API: auth, order submission, eSIM retrieval
├── ui_tests/
│   └── test_japan_esim.py    # UI: Japan 7-day unlimited eSIM price verification
├── screenshots/              # Auto-generated on UI test run
├── conftest.py               # Shared pytest hooks: output formatting
├── pytest.ini                # Pytest configuration
├── .env                      # Credentials (not committed)
├── .env.example              # Credentials template
└── requirements.txt
```

---

## Setup

```bash
# Install dependencies
pip3 install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure credentials
cp .env.example .env
# Fill in AIRALO_CLIENT_ID and AIRALO_CLIENT_SECRET in .env
```

---
## Running Tests

```bash
# All tests
python3 -m pytest -v

# API tests only
python3 -m pytest api_tests/ -v

# UI tests only
python3 -m pytest ui_tests/ --headed
```
---

## Test Coverage

### API — `test_airalo_api.py`
Base URL: `https://partners-api.airalo.com/v2`

| Class | Test | Description |
|---|---|---|
| `TestAuthentication` | valid credentials return token | OAuth2 token is issued for valid credentials |
| `TestAuthentication` | invalid credentials are rejected | API returns 4xx for bad credentials |
| `TestSubmitOrder` | order has correct quantity | POST /orders returns 6 eSIMs |
| `TestSubmitOrder` | order has correct package | Package ID matches requested value |
| `TestSubmitOrder` | each sim has iccid | Every eSIM in the order has a valid iccid |
| `TestGetEsimDetails` | each esim is retrievable | GET /sims/{iccid} returns correct eSIM for each order item |

### UI — `test_japan_esim.py`
| Test | Description |
|---|---|
| price matches buy now button | Navigates to Japan → Unlimited → 7 days and verifies the package price equals the Buy Now total |

---

## Approach

**API:** Session-scoped fixtures obtain the token and place the order once, shared across all tests. Keeps the suite fast and avoids redundant API calls. Covers both positive and negative authentication scenarios.

**UI:** Playwright handles cookie consent and browser notification popups automatically. Price extraction is currency-agnostic (supports £, $, €). A screenshot is saved on each run as visual proof of the result.
