from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


MOCK_COINS = [
    {
        "id": "passing-coin",
        "symbol": "pass",
        "name": "Passing Coin",
        "image": None,
        "current_price": 1.0,
        "market_cap": 5_000_000,
        "market_cap_rank": 150,
        "fully_diluted_valuation": 20_000_000,
        "total_volume": 200_000,
        "total_supply": 1_000_000,
        "max_supply": 1_000_000,
        "circulating_supply": 900_000,
        "price_change_percentage_24h": 1.5,
    },
    {
        "id": "top-ranked-coin",
        "symbol": "top",
        "name": "Top Ranked Coin",
        "image": None,
        "current_price": 1.0,
        "market_cap": 10_000_000,
        "market_cap_rank": 10,
        "fully_diluted_valuation": 20_000_000,
        "total_volume": 200_000,
        "total_supply": 1_000_000,
        "max_supply": 1_000_000,
        "circulating_supply": 900_000,
        "price_change_percentage_24h": 1.5,
    },
]


def test_projects_endpoint_filters_and_serializes(monkeypatch):
    async def fake_fetch_markets():
        return MOCK_COINS, False

    monkeypatch.setattr(main, "fetch_coingecko_markets", fake_fetch_markets)

    response = client.get("/api/projects")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["source"] == "coingecko"
    assert body["cached"] is False
    assert body["projects"][0]["id"] == "passing-coin"
    assert body["projects"][0]["tvl"] == 80_000.0
    assert body["projects"][0]["preview_listing"] is True


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
