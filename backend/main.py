"""
Crypto Projects API
--------------------
FastAPI backend that fetches cryptocurrency market data from CoinGecko,
applies a set of business-defined filters, and exposes the result via
a single REST endpoint: GET /api/projects

See README.md at the project root for assumptions around fields that
CoinGecko's free tier does not provide (preview_listing, TVL).
"""

import time
from typing import Optional

import httpx
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
CACHE_TTL_SECONDS = 90  # within the recommended 60-120s window
CACHE_MAXSIZE = 8
REQUEST_TIMEOUT = 15.0

# Filter thresholds (business rules from the spec)
MIN_MCAP = 0
MAX_FDV = 100_000_000
MIN_VOLUME_24H = 50_000
MIN_TVL = 50_000

# --------------------------------------------------------------------------
# App setup
# --------------------------------------------------------------------------

app = FastAPI(
    title="Crypto Projects API",
    description="Filtered cryptocurrency project listings sourced from CoinGecko.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory TTL cache. Key -> raw CoinGecko response (list of dicts).
# This is what protects us from CoinGecko's aggressive free-tier rate limits:
# multiple frontend requests within CACHE_TTL_SECONDS are served from memory
# instead of hitting CoinGecko again.
_cache: TTLCache = TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL_SECONDS)
_CACHE_KEY = "coingecko_markets"

# Fallback: last known-good data, kept indefinitely (no TTL) so that if
# CoinGecko is down or rate-limiting us AND the TTL cache has expired,
# we can still serve something useful instead of a hard failure.
_last_good_data: Optional[list] = None
_last_good_timestamp: Optional[float] = None


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------

class Project(BaseModel):
    id: str
    symbol: str
    name: str
    image: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: float
    market_cap_rank: Optional[int] = None
    fully_diluted_valuation: Optional[float] = None
    total_volume: float
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    tvl: float
    preview_listing: bool
    price_change_percentage_24h: Optional[float] = None


class ProjectsResponse(BaseModel):
    count: int
    source: str
    cached: bool
    projects: list[Project]


# --------------------------------------------------------------------------
# Data fetching (with caching + graceful degradation)
# --------------------------------------------------------------------------

async def fetch_coingecko_markets() -> tuple[list, bool]:
    """
    Returns (data, was_cached).
    Fetches from CoinGecko's /coins/markets endpoint, using the in-memory
    TTL cache first. Falls back to the last known-good dataset if CoinGecko
    errors out (e.g. 429 Too Many Requests) and the cache is empty/expired.
    """
    global _last_good_data, _last_good_timestamp

    if _CACHE_KEY in _cache:
        return _cache[_CACHE_KEY], True

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(f"{COINGECKO_BASE_URL}/coins/markets", params=params)

        if resp.status_code == 429:
            # Rate limited: serve stale cache if we have it, else error.
            if _last_good_data is not None:
                return _last_good_data, True
            raise HTTPException(
                status_code=503,
                detail="CoinGecko rate limit hit and no cached data is available yet. Please retry shortly.",
            )

        resp.raise_for_status()
        data = resp.json()

        _cache[_CACHE_KEY] = data
        _last_good_data = data
        _last_good_timestamp = time.time()
        return data, False

    except httpx.RequestError as exc:
        # Network-level failure (DNS, timeout, connection refused, etc.)
        if _last_good_data is not None:
            return _last_good_data, True
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach CoinGecko and no cached data is available: {exc}",
        )
    except httpx.HTTPStatusError as exc:
        if _last_good_data is not None:
            return _last_good_data, True
        raise HTTPException(
            status_code=502,
            detail=f"CoinGecko returned an error: {exc.response.status_code}",
        )


# --------------------------------------------------------------------------
# Field mocking helpers (documented assumptions — see README)
# --------------------------------------------------------------------------

def mock_preview_listing(coin: dict) -> bool:
    """
    ASSUMPTION: CoinGecko's free /coins/markets endpoint has no concept of
    'preview_listing'. We approximate it: coins ranked outside the top 100
    by market cap are treated as 'preview' (i.e. newer / smaller / not yet
    a fully established, top-tier listing). Top-100 coins are considered
    already fully listed, not previews. This is a deterministic, documented
    stand-in so the filter pipeline is exercised meaningfully.
    """
    rank = coin.get("market_cap_rank")
    if rank is None:
        return True
    return rank > 100


def mock_tvl(coin: dict) -> float:
    """
    ASSUMPTION: TVL (Total Value Locked) is a DeFi-protocol metric that
    CoinGecko's /coins/markets endpoint does not return (it lives on
    DeFiLlama / CoinGecko's separate DeFi endpoints, and only applies to
    protocols with on-chain locked liquidity, not all coins). To keep the
    pipeline deterministic and testable without a second paid data source,
    we derive a stand-in TVL as a fixed fraction of 24h trading volume:

        tvl = total_volume * 0.4

    This is clearly a proxy, not real TVL, and is documented as such in the
    README. In a production system this would be replaced with a real call
    to DeFiLlama's /protocols endpoint (or CoinGecko's DeFi-specific
    endpoints) keyed by project slug.
    """
    volume = coin.get("total_volume") or 0
    return round(volume * 0.4, 2)


# --------------------------------------------------------------------------
# Filtering logic
# --------------------------------------------------------------------------

def passes_filters(coin: dict, tvl: float, preview_listing: bool) -> bool:
    mcap = coin.get("market_cap")
    fdv = coin.get("fully_diluted_valuation")
    volume = coin.get("total_volume")
    max_supply = coin.get("max_supply")
    total_supply = coin.get("total_supply")

    # 1. Market Cap > 0
    if mcap is None or mcap <= MIN_MCAP:
        return False

    # 2. preview_listing must be True (mocked field)
    if not preview_listing:
        return False

    # 3. Max Supply == Total Supply, only when BOTH exist (handle nulls)
    if max_supply is None or total_supply is None:
        return False
    if max_supply != total_supply:
        return False

    # 4. FDV < $100M (must exist to be evaluated)
    if fdv is None or fdv >= MAX_FDV:
        return False

    # 5. 24h Volume > $50k
    if volume is None or volume <= MIN_VOLUME_24H:
        return False

    # 6. TVL > $50k
    if tvl <= MIN_TVL:
        return False

    return True


def build_project(coin: dict) -> Project:
    tvl = mock_tvl(coin)
    preview_listing = mock_preview_listing(coin)
    return Project(
        id=coin.get("id"),
        symbol=coin.get("symbol"),
        name=coin.get("name"),
        image=coin.get("image"),
        current_price=coin.get("current_price"),
        market_cap=coin.get("market_cap"),
        market_cap_rank=coin.get("market_cap_rank"),
        fully_diluted_valuation=coin.get("fully_diluted_valuation"),
        total_volume=coin.get("total_volume"),
        total_supply=coin.get("total_supply"),
        max_supply=coin.get("max_supply"),
        circulating_supply=coin.get("circulating_supply"),
        tvl=tvl,
        preview_listing=preview_listing,
        price_change_percentage_24h=coin.get("price_change_percentage_24h"),
    )


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/projects", response_model=ProjectsResponse)
async def get_projects(
    limit: int = Query(default=250, ge=1, le=250, description="Max raw coins fetched from CoinGecko before filtering"),
):
    """
    Returns the list of cryptocurrency projects from CoinGecko after applying
    all filter criteria (market cap, preview_listing, supply equality, FDV,
    24h volume, TVL). See README.md for details on mocked fields.
    """
    raw_data, cached = await fetch_coingecko_markets()

    filtered_projects: list[Project] = []
    for coin in raw_data[:limit]:
        tvl = mock_tvl(coin)
        preview_listing = mock_preview_listing(coin)
        if passes_filters(coin, tvl, preview_listing):
            filtered_projects.append(build_project(coin))

    return ProjectsResponse(
        count=len(filtered_projects),
        source="coingecko",
        cached=cached,
        projects=filtered_projects,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
