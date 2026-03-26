Here's the updated README:

---

# Airalo QA Coding Exercise

Automated test suite covering UI and API for the Airalo platform, built with Python, Pytest, and Playwright.

---

## Project Structure

```
airalo-qa/
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI: separate API and UI jobs
├── api_tests/
│   └── test_airalo_api.py        # Partner API: auth, order submission, eSIM retrieval
├── ui_tests/
│   ├── pages/
│   │   ├── home_page.py          # Page object: home page navigation and search
│   │   └── japan_page.py         # Page object: Japan eSIM package selection and price
│   ├── test_japan_esim.py        # UI: Japan 7-day unlimited eSIM price verification
│   └── utils.py                  # Price extraction helper
├── screenshots/                  # Auto-generated on UI test run
├── results/                      # JUnit XML test results (auto-generated)
├── conftest.py                   # Shared pytest hooks: output formatting
├── pytest.ini                    # Pytest configuration
├── .env                          # Credentials (not committed)
├── .env.example                  # Credentials template
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

# UI tests only (headless)
python3 -m pytest ui_tests/ -v

# UI tests with browser visible (local development)
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
| `TestGetEsimDetails` | each esim is retrievable with required properties | GET /sims/{iccid} returns correct eSIM, validates iccid, meta.message, and required fields (lpa, qrcode, apn_type, apn_value) |

### UI — `test_japan_esim.py`
| Test | Description |
|---|---|
| japan 7day unlimited price matches buy now | Navigates to Japan → Unlimited → 7 days and verifies the package price equals the Buy Now total |

---

## CI/CD

GitHub Actions runs on every push and pull request to `main`, with two parallel jobs:

| Job | What it runs | Artifacts |
|---|---|---|
| `api-tests` | `pytest api_tests/` with secrets injected | `results/api-results.xml` |
| `ui-tests` | `pytest ui_tests/` with Playwright (headless Chromium) | `results/ui-results.xml`, `screenshots/` |

Secrets required in the repository settings: `AIRALO_CLIENT_ID`, `AIRALO_CLIENT_SECRET`.

---

## Approach

**API:** Session-scoped fixtures obtain the token and place the order once, shared across all tests. Keeps the suite fast and avoids redundant API calls. Covers both positive and negative authentication scenarios.

**UI:** Uses the Page Object Model (`pages/`) to separate navigation logic from test assertions. Playwright handles cookie consent and browser notification popups automatically. Price extraction is currency-agnostic (supports £, $, €). A screenshot is saved on each run as visual proof of the result.