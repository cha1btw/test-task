import type { Project, SortDirection, SortField } from '../types'

interface Props {
  projects: Project[]
  sortField: SortField
  sortDirection: SortDirection
  onSortFieldChange: (field: SortField) => void
}

function formatUsd(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(value)
}

function SortableHeader({
  label,
  field,
  sortField,
  sortDirection,
  onSortFieldChange,
}: {
  label: string
  field: SortField
  sortField: SortField
  sortDirection: SortDirection
  onSortFieldChange: (field: SortField) => void
}) {
  const isActive = sortField === field
  return (
    <th
      scope="col"
      onClick={() => onSortFieldChange(field)}
      className="cursor-pointer select-none px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-700"
    >
      {label} {isActive ? (sortDirection === 'desc' ? '↓' : '↑') : ''}
    </th>
  )
}

export default function ProjectsTable({ projects, sortField, sortDirection, onSortFieldChange }: Props) {
  if (projects.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-12 text-center text-slate-500">
        No projects match the current filters.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              Project
            </th>
            <SortableHeader
              label="Market Cap"
              field="market_cap"
              sortField={sortField}
              sortDirection={sortDirection}
              onSortFieldChange={onSortFieldChange}
            />
            <th scope="col" className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
              FDV
            </th>
            <SortableHeader
              label="24h Volume"
              field="total_volume"
              sortField={sortField}
              sortDirection={sortDirection}
              onSortFieldChange={onSortFieldChange}
            />
            <th scope="col" className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
              TVL (est.)
            </th>
            <th scope="col" className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
              24h %
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {projects.map((p) => (
            <tr key={p.id} className="hover:bg-slate-50">
              <td className="whitespace-nowrap px-4 py-3">
                <div className="flex items-center gap-3">
                  {p.image && <img src={p.image} alt={p.name} className="h-6 w-6 rounded-full" />}
                  <div>
                    <p className="text-sm font-medium text-slate-900">{p.name}</p>
                    <p className="text-xs uppercase text-slate-400">{p.symbol}</p>
                  </div>
                </div>
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">{formatUsd(p.market_cap)}</td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">
                {formatUsd(p.fully_diluted_valuation)}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">{formatUsd(p.total_volume)}</td>
              <td className="whitespace-nowrap px-4 py-3 text-right text-sm text-slate-700">{formatUsd(p.tvl)}</td>
              <td
                className={`whitespace-nowrap px-4 py-3 text-right text-sm font-medium ${
                  (p.price_change_percentage_24h ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-600'
                }`}
              >
                {p.price_change_percentage_24h?.toFixed(2) ?? '—'}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
