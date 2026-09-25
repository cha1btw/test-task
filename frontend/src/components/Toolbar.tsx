import type { SortDirection, SortField } from '../types'

interface Props {
  search: string
  onSearchChange: (value: string) => void
  maxFdv: string
  onMaxFdvChange: (value: string) => void
  sortField: SortField
  sortDirection: SortDirection
  onSortFieldChange: (field: SortField) => void
  onToggleSortDirection: () => void
  resultCount: number
}

export default function Toolbar({
  search,
  onSearchChange,
  maxFdv,
  onMaxFdvChange,
  sortField,
  sortDirection,
  onSortFieldChange,
  onToggleSortDirection,
  resultCount,
}: Props) {
  return (
    <div className="mb-6 flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm md:flex-row md:items-end md:justify-between">
      <div className="flex flex-col gap-4 md:flex-row md:items-end">
        <div className="flex flex-col gap-1">
          <label htmlFor="search" className="text-xs font-medium text-slate-500">
            Search by name
          </label>
          <input
            id="search"
            type="text"
            placeholder="e.g. eth"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-48 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="max-fdv" className="text-xs font-medium text-slate-500">
            Max FDV ($)
          </label>
          <input
            id="max-fdv"
            type="number"
            min={0}
            placeholder="e.g. 50000000"
            value={maxFdv}
            onChange={(e) => onMaxFdvChange(e.target.value)}
            className="w-48 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor="sort-field" className="text-xs font-medium text-slate-500">
            Sort by
          </label>
          <div className="flex gap-2">
            <select
              id="sort-field"
              value={sortField}
              onChange={(e) => onSortFieldChange(e.target.value as SortField)}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="market_cap">Market Cap</option>
              <option value="total_volume">24h Volume</option>
            </select>
            <button
              onClick={onToggleSortDirection}
              title="Toggle sort direction"
              className="rounded-md border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50"
            >
              {sortDirection === 'desc' ? '↓ Desc' : '↑ Asc'}
            </button>
          </div>
        </div>
      </div>

      <p className="text-sm text-slate-500">{resultCount} project{resultCount === 1 ? '' : 's'}</p>
    </div>
  )
}
