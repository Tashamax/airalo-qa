import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://partners-api.airalo.com/v2"
PACKAGE_ID = "moshi-moshi-7days-1gb"
ORDER_QUANTITY = 6
ESIM_INCLUDE = "order,order.status,order.user,sim.usage"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def auth_token():
    response = requests.post(
        f"{BASE_URL}/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("AIRALO_CLIENT_ID"),
            "client_secret": os.getenv("AIRALO_CLIENT_SECRET"),
        },
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return response.json()["data"]["access_token"]


@pytest.fixture(scope="session")
def order(auth_token):
    response = requests.post(
        f"{BASE_URL}/orders",
        data={"quantity": ORDER_QUANTITY, "package_id": PACKAGE_ID},
        headers={"Authorization": f"Bearer {auth_token}", "Accept": "application/json"},
    )
    assert response.status_code == 200, f"Order failed: {response.text}"
    return response.json()["data"]


@pytest.fixture(scope="session")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Accept": "application/json"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuthentication:

    def test_valid_credentials_return_token(self):
        response = requests.post(
            f"{BASE_URL}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.getenv("AIRALO_CLIENT_ID"),
                "client_secret": os.getenv("AIRALO_CLIENT_SECRET"),
            },
            headers={"Accept": "application/json"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["access_token"]

    def test_invalid_credentials_are_rejected(self):
        response = requests.post(
            f"{BASE_URL}/token",
            data={"grant_type": "client_credentials", "client_id": "bad", "client_secret": "bad"},
            headers={"Accept": "application/json"},
        )
        assert response.status_code in [400, 401, 422]


# ── Order Tests ───────────────────────────────────────────────────────────────

class TestSubmitOrder:

    def test_order_has_correct_quantity(self, order):
        assert len(order["sims"]) == ORDER_QUANTITY

    def test_order_has_correct_package(self, order):
        assert order["package_id"] == PACKAGE_ID

    def test_each_sim_has_iccid(self, order):
        for sim in order["sims"]:
            assert sim.get("iccid"), f"Missing iccid in sim: {sim}"


# ── eSIM Detail Tests ─────────────────────────────────────────────────────────

class TestGetEsimDetails:

    def test_each_esim_is_retrievable(self, order, headers):
        for sim in order["sims"]:
            response = requests.get(
                f"{BASE_URL}/sims/{sim['iccid']}",
                headers=headers,
                params={"include": ESIM_INCLUDE},
            )
            assert response.status_code == 200
            assert response.json()["data"]["iccid"] == sim["iccid"]
