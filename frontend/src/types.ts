export interface Project {
  id: string
  symbol: string
  name: string
  image?: string | null
  current_price?: number | null
  market_cap: number
  market_cap_rank?: number | null
  fully_diluted_valuation?: number | null
  total_volume: number
  total_supply?: number | null
  max_supply?: number | null
  circulating_supply?: number | null
  tvl: number
  preview_listing: boolean
  price_change_percentage_24h?: number | null
}

export interface ProjectsResponse {
  count: number
  source: string
  cached: boolean
  projects: Project[]
}

export type SortField = 'market_cap' | 'total_volume'
export type SortDirection = 'asc' | 'desc'
