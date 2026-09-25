import { useEffect, useMemo, useState } from 'react'
import { fetchProjects } from './api'
import type { Project, SortDirection, SortField } from './types'
import Spinner from './components/Spinner'
import ErrorBanner from './components/ErrorBanner'
import Toolbar from './components/Toolbar'
import ProjectsTable from './components/ProjectsTable'

type Status = 'loading' | 'success' | 'error'

export default function App() {
  const [status, setStatus] = useState<Status>('loading')
  const [errorMessage, setErrorMessage] = useState('')
  const [projects, setProjects] = useState<Project[]>([])
  const [cached, setCached] = useState(false)

  const [search, setSearch] = useState('')
  const [maxFdv, setMaxFdv] = useState('')
  const [sortField, setSortField] = useState<SortField>('market_cap')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const loadProjects = () => {
    setStatus('loading')
    setErrorMessage('')
    fetchProjects()
      .then((res) => {
        setProjects(res.projects)
        setCached(res.cached)
        setStatus('success')
      })
      .catch((err: Error) => {
        setErrorMessage(err.message || 'Unknown error')
        setStatus('error')
      })
  }

  useEffect(() => {
    loadProjects()
  }, [])

  const visibleProjects = useMemo(() => {
    let result = [...projects]

    if (search.trim()) {
      const term = search.trim().toLowerCase()
      result = result.filter(
        (p) => p.name.toLowerCase().includes(term) || p.symbol.toLowerCase().includes(term),
      )
    }

    const fdvCeiling = parseFloat(maxFdv)
    if (!Number.isNaN(fdvCeiling) && maxFdv !== '') {
      result = result.filter(
        (p) => p.fully_diluted_valuation !== null && p.fully_diluted_valuation !== undefined && p.fully_diluted_valuation < fdvCeiling,
      )
    }

    result.sort((a, b) => {
      const aVal = a[sortField] ?? 0
      const bVal = b[sortField] ?? 0
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
    })

    return result
  }, [projects, search, maxFdv, sortField, sortDirection])

  const handleSortFieldChange = (field: SortField) => {
    if (field === sortField) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-6">
          <h1 className="text-2xl font-bold text-slate-900">Crypto Projects</h1>
          <p className="mt-1 text-sm text-slate-500">
            Filtered listings sourced from CoinGecko via the local backend.
            {status === 'success' && cached && <span className="ml-2 text-amber-600">(served from cache)</span>}
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {status === 'loading' && <Spinner />}

        {status === 'error' && <ErrorBanner message={errorMessage} onRetry={loadProjects} />}

        {status === 'success' && (
          <>
            <Toolbar
              search={search}
              onSearchChange={setSearch}
              maxFdv={maxFdv}
              onMaxFdvChange={setMaxFdv}
              sortField={sortField}
              sortDirection={sortDirection}
              onSortFieldChange={handleSortFieldChange}
              onToggleSortDirection={() => setSortDirection((p) => (p === 'asc' ? 'desc' : 'asc'))}
              resultCount={visibleProjects.length}
            />
            <ProjectsTable
              projects={visibleProjects}
              sortField={sortField}
              sortDirection={sortDirection}
              onSortFieldChange={handleSortFieldChange}
            />
          </>
        )}
      </main>
    </div>
  )
}
