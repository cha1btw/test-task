# Crypto Projects — Full Stack Assessment

A full-stack application that fetches cryptocurrency market data from
CoinGecko, filters it against a set of business rules on the backend, and
displays it in a searchable, filterable, sortable table on the frontend.

- **Backend:** Python 3.10+ / FastAPI / httpx / cachetools
- **Frontend:** React 18 / Vite / TypeScript / Tailwind CSS

```
crypto-app/
├── backend/
│   ├── main.py            # FastAPI app: fetch, cache, filter, serve
│   ├── test_filters.py    # Unit tests for the filter logic (no network)
│   ├── requirements.txt
│   └── .gitignore
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── components/
│   │       ├── Toolbar.tsx
│   │       ├── ProjectsTable.tsx
│   │       ├── Spinner.tsx
│   │       └── ErrorBanner.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── ...
└── README.md
```

---

## 1. Setup Instructions

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`, with interactive
Swagger docs at `http://localhost:8000/docs`.

Run the (network-free) unit tests for the filter logic:

```bash
pip install pytest
pytest test_filters.py -v
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`. It expects the
backend to be running at `http://localhost:8000` (see `src/api.ts`).

---

## 2. Completed Features

**Backend**
- [x] `GET /api/projects` REST endpoint, auto-documented via Swagger (`/docs`)
- [x] Fetches live data from CoinGecko's `/coins/markets` endpoint
- [x] In-memory TTL cache (`cachetools.TTLCache`, 90s TTL) to absorb
      CoinGecko's aggressive free-tier rate limiting
- [x] Graceful fallback to the last known-good dataset if CoinGecko returns
      `429` or is unreachable, instead of a hard failure
- [x] Full filter pipeline applied server-side:
  - Market Cap > 0
  - `preview_listing == true` (mocked — see Assumptions)
  - Max Supply == Total Supply (nulls excluded, not treated as equal)
  - FDV < $100,000,000
  - 24h Volume > $50,000
  - TVL > $50,000 (mocked — see Assumptions)
- [x] CORS configured for `http://localhost:5173` and `http://127.0.0.1:5173`
- [x] Typed response models via Pydantic
- [x] Unit tests for the filter logic (`test_filters.py`) that run without
      any network access

**Frontend**
- [x] Fetches exclusively from the local backend — no direct CoinGecko calls
- [x] Clean table view (project, market cap, FDV, 24h volume, TVL, 24h %)
- [x] Search by name or symbol, case-insensitive, partial match (`eth` → Ethereum)
- [x] Client-side FDV filter (numeric input, "show only below this value")
- [x] Sortable columns for Market Cap and 24h Volume (click header or use
      the dropdown; click again to flip direction)
- [x] Loading spinner while fetching
- [x] Error banner with a Retry button if the backend call fails
- [x] "Served from cache" indicator when the backend returns cached data
- [x] Responsive, functional Tailwind styling

---

## 3. Assumptions & Limitations

### Rate limiting
CoinGecko's free/public API returns `429 Too Many Requests` under light,
unauthenticated load. To handle this:

1. **In-memory TTL cache** (`cachetools.TTLCache`, 90 seconds) sits in front
   of every outbound call to CoinGecko. Repeated frontend requests within
   that window are served from memory — CoinGecko is called at most once
   every 90 seconds regardless of how many users hit `/api/projects`.
2. **Stale-fallback on error:** if CoinGecko responds with `429` (or a
   network error occurs) and the TTL cache has expired, the backend falls
   back to the last successfully fetched dataset (`_last_good_data`) rather
   than failing the request outright. Only if there is truly no data yet
   (e.g. very first request happens to hit a rate limit) does the endpoint
   return a `503` with a clear error message.
3. The API response includes a `cached: true/false` flag so the frontend
   can surface this to the user (shown as "served from cache" in the header).

### `preview_listing`
CoinGecko's free `/coins/markets` endpoint has no `preview_listing` field —
this concept doesn't exist in their public API. **Mocked assumption:** a
coin is treated as a "preview listing" if its `market_cap_rank` is outside
the top 100 (i.e. `rank > 100`, or `rank` is missing). The reasoning: an
established, top-100 coin is not a "preview" of anything — it's already a
fully mainstream listing — whereas smaller/newer coins map reasonably to a
"preview" or "not yet fully listed" status for the purposes of this
exercise. This is implemented in `main.py::mock_preview_listing()` and is
clearly labeled as a documented assumption in code comments.

### Total Value Locked (TVL)
TVL is a DeFi-protocol-specific metric (on-chain locked liquidity) that
lives on DeFiLlama / CoinGecko's separate DeFi endpoints and doesn't apply
to most coins (e.g. it's meaningless for Bitcoin). It is **not** part of
`/coins/markets`. **Mocked assumption:** TVL is approximated as
`24h_trading_volume × 0.4`, implemented in `main.py::mock_tvl()`. This is a
deterministic stand-in chosen so the filter pipeline (`TVL > $50,000`) is
exercised meaningfully during evaluation. In a production system this
would be replaced with a real lookup against DeFiLlama's `/protocols`
endpoint (matched by project slug/contract), which only returns values for
actual DeFi protocols.

### Max Supply == Total Supply
Both `max_supply` and `total_supply` must be **present (non-null) and
equal** to pass. If either value is missing (which is common — many coins
have no fixed max supply), the project is excluded rather than treated as
a pass. This is a stricter, more defensible reading of "handle nulls
carefully" than assuming equality when data is absent.

### Data freshness / scope
- The backend pulls up to 250 coins per CoinGecko page (`per_page=250`,
  `page=1`, sorted by market cap descending) — CoinGecko's free tier caps
  `per_page` at 250. Given the filters (FDV < $100M, top-100-excluded via
  the `preview_listing` mock), this range comfortably covers the segment
  of the market the filters are targeting.
- No API key is required or used; if you have a CoinGecko Demo/Pro API key,
  it can be added as a header in `fetch_coingecko_markets()` in `main.py` to
  raise the real rate limits.

### AI workflow

AI coding assistants were used to scaffold the FastAPI and React structure,
draft the filtering and UI logic, and review the implementation against the
requirements. The code, assumptions around unavailable CoinGecko fields,
tests, CORS behavior, and local runtime checks were reviewed and corrected
manually.

### Out of scope (given the time limit)
- No persistent database — caching is in-memory only and resets on server
  restart.
- No authentication/authorization (not required by the spec).
- No pagination on the frontend (dataset size after filtering is small
  enough for a single page).
