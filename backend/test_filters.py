"""
Lightweight sanity tests for the filtering logic (no network calls).
Run with: pytest test_filters.py  (or) python -m pytest
"""

from main import passes_filters, mock_tvl, mock_preview_listing


def make_coin(**overrides):
    base = {
        "id": "test-coin",
        "market_cap": 5_000_000,
        "market_cap_rank": 150,  # > 100 -> preview_listing mocked True
        "fully_diluted_valuation": 20_000_000,
        "total_volume": 200_000,  # tvl mock = 200_000 * 0.4 = 80_000 > 50_000
        "max_supply": 1_000_000,
        "total_supply": 1_000_000,
    }
    base.update(overrides)
    return base


def test_valid_coin_passes():
    coin = make_coin()
    tvl = mock_tvl(coin)
    preview = mock_preview_listing(coin)
    assert passes_filters(coin, tvl, preview) is True


def test_zero_market_cap_fails():
    coin = make_coin(market_cap=0)
    assert passes_filters(coin, mock_tvl(coin), mock_preview_listing(coin)) is False


def test_top_100_rank_fails_preview_listing():
    coin = make_coin(market_cap_rank=10)
    assert mock_preview_listing(coin) is False
    assert passes_filters(coin, mock_tvl(coin), mock_preview_listing(coin)) is False


def test_mismatched_supply_fails():
    coin = make_coin(max_supply=1_000_000, total_supply=999_000)
    assert passes_filters(coin, mock_tvl(coin), mock_preview_listing(coin)) is False


def test_null_supply_fails():
    coin = make_coin(max_supply=None, total_supply=1_000_000)
    assert passes_filters(coin, mock_tvl(coin), mock_preview_listing(coin)) is False


def test_fdv_too_high_fails():
    coin = make_coin(fully_diluted_valuation=150_000_000)
    assert passes_filters(coin, mock_tvl(coin), mock_preview_listing(coin)) is False


def test_low_volume_fails():
    coin = make_coin(total_volume=10_000)
    tvl = mock_tvl(coin)  # 10_000 * 0.4 = 4_000, also fails TVL
    assert passes_filters(coin, tvl, mock_preview_listing(coin)) is False


def test_low_tvl_fails_even_with_ok_volume():
    # volume just above 50k but tvl proxy (0.4x) still below 50k threshold
    coin = make_coin(total_volume=100_000)  # tvl = 40_000 < 50_000
    tvl = mock_tvl(coin)
    assert tvl == 40_000.0
    assert passes_filters(coin, tvl, mock_preview_listing(coin)) is False
