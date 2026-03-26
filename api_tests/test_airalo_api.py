import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://partners-api.airalo.com/v2"
PACKAGE_ID = "moshi-moshi-7days-1gb"
ORDER_QUANTITY = 6
ESIM_INCLUDE = "order,order.status,order.user,sim.usage"

# Avoids Cloudflare bot detection on CI runner IPs
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract(response: requests.Response, *keys: str):
    """
    Safely navigate nested keys in a JSON response.
    Raises a descriptive AssertionError on missing keys or invalid JSON
    instead of an unhandled KeyError/ValueError.
    """
    try:
        body = response.json()
    except ValueError as exc:
        raise AssertionError(
            f"Response is not valid JSON.\n"
            f"Status: {response.status_code}\n"
            f"Body (first 500 chars): {response.text[:500]}"
        ) from exc

    current = body
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            available = list(current.keys()) if isinstance(current, dict) else type(current).__name__
            raise AssertionError(
                f"Expected key '{key}' not found in response.\n"
                f"Available keys: {available}\n"
                f"Full response body: {body}"
            )
        current = current[key]
    return current


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def env_config() -> dict:
    """
    Validate required environment variables upfront.
    Raises immediately with a clear message rather than silently passing
    None into API requests.
    """
    missing = [v for v in ("AIRALO_CLIENT_ID", "AIRALO_CLIENT_SECRET") if not os.getenv(v)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}.\n"
            "Copy .env.example to .env and fill in your credentials."
        )
    return {
        "client_id": os.environ["AIRALO_CLIENT_ID"],
        "client_secret": os.environ["AIRALO_CLIENT_SECRET"],
    }


@pytest.fixture(scope="session")
def auth_token(env_config: dict) -> str:
    response = requests.post(
        f"{BASE_URL}/token",
        data={
            "grant_type": "client_credentials",
            "client_id": env_config["client_id"],
            "client_secret": env_config["client_secret"],
        },
        headers=DEFAULT_HEADERS,
    )
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return _extract(response, "data", "access_token")


@pytest.fixture(scope="session")
def order(auth_token: str) -> dict:
    response = requests.post(
        f"{BASE_URL}/orders",
        data={"quantity": ORDER_QUANTITY, "package_id": PACKAGE_ID},
        headers={**DEFAULT_HEADERS, "Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200, f"Order failed: {response.text}"
    return _extract(response, "data")


@pytest.fixture(scope="session")
def headers(auth_token: str) -> dict:
    return {**DEFAULT_HEADERS, "Authorization": f"Bearer {auth_token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuthentication:

    def test_valid_credentials_return_token(self, auth_token: str):
        # Reuses the session-scoped fixture to avoid a duplicate token call
        # which can trigger Cloudflare rate limiting on CI runner IPs
        assert auth_token, "access_token should be non-empty"

    def test_invalid_credentials_are_rejected(self):
        response = requests.post(
            f"{BASE_URL}/token",
            data={"grant_type": "client_credentials", "client_id": "bad", "client_secret": "bad"},
            headers=DEFAULT_HEADERS,
        )
        assert response.status_code in [400, 401, 422], (
            f"Expected a 4xx status for invalid credentials, got {response.status_code}"
        )


# ── Order Tests ───────────────────────────────────────────────────────────────

class TestSubmitOrder:

    def test_order_has_correct_quantity(self, order: dict):
        sims = order.get("sims", [])
        assert len(sims) == ORDER_QUANTITY, (
            f"Expected {ORDER_QUANTITY} SIMs, got {len(sims)}"
        )

    def test_order_has_correct_package(self, order: dict):
        assert order.get("package_id") == PACKAGE_ID, (
            f"Expected package_id '{PACKAGE_ID}', got '{order.get('package_id')}'"
        )

    def test_each_sim_has_iccid(self, order: dict):
        for sim in order["sims"]:
            assert sim.get("iccid"), f"Missing iccid in SIM: {sim}"

    def test_order_response_message_is_success(self, auth_token: str):
        response = requests.post(
            f"{BASE_URL}/orders",
            data={"quantity": 1, "package_id": PACKAGE_ID},
            headers={**DEFAULT_HEADERS, "Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        message = _extract(response, "meta", "message")
        assert message, "meta.message should be non-empty on a successful order"


# ── eSIM Detail Tests ─────────────────────────────────────────────────────────

class TestGetEsimDetails:

    def test_each_esim_is_retrievable(self, order: dict, headers: dict):
        for sim in order["sims"]:
            response = requests.get(
                f"{BASE_URL}/sims/{sim['iccid']}",
                headers=headers,
                params={"include": ESIM_INCLUDE},
            )
            assert response.status_code == 200, (
                f"GET /sims/{sim['iccid']} returned {response.status_code}: {response.text}"
            )
            data = _extract(response, "data")
            assert data.get("iccid") == sim["iccid"], (
                f"Response iccid '{data.get('iccid')}' does not match requested '{sim['iccid']}'"
            )
            assert _extract(response, "meta", "message"), (
                f"meta.message missing for SIM {sim['iccid']}"
            )

    def test_each_esim_has_required_properties(self, order: dict, headers: dict):
        required_fields = {"iccid", "lpa", "qrcode", "apn_type", "apn_value"}
        for sim in order["sims"]:
            response = requests.get(
                f"{BASE_URL}/sims/{sim['iccid']}",
                headers=headers,
                params={"include": ESIM_INCLUDE},
            )
            assert response.status_code == 200
            data = _extract(response, "data")
            missing = required_fields - set(data.keys())
            assert not missing, (
                f"SIM {sim['iccid']} is missing required fields: {missing}\n"
                f"Available fields: {list(data.keys())}"
            )
