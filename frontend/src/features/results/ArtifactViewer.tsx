import React, { useEffect, useState } from 'react'
import {
  Layers,
  Search,
  RefreshCw,
  Clock,
  Filter,
  Eye,
  FileCode,
} from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { fetchArtifacts } from '../../api'
import { Artifact } from '../../types'
import { NavTab } from '../../components/layout/Sidebar'

interface ArtifactViewerProps {
  initialJobId?: string
  initialAgentId?: string
  initialType?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  initialJobId,
  initialAgentId,
  initialType,
  onNavigate,
}) => {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<string>(initialType || 'all')
  const [jobIdFilter, setJobIdFilter] = useState<string>(initialJobId || '')
  const [agentIdFilter, setAgentIdFilter] = useState<string>(initialAgentId || '')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null)
  const [showRawJson, setShowRawJson] = useState(false)

  const loadArtifacts = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await fetchArtifacts({
        jobId: jobIdFilter || undefined,
        agentId: agentIdFilter || undefined,
        type: typeFilter !== 'all' ? typeFilter : undefined,
        limit: 200,
      })
      setArtifacts(res.items || [])
    } catch (err: any) {
      setError(err.message || 'Unable to retrieve artifacts from server.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadArtifacts()
  }, [typeFilter, jobIdFilter, agentIdFilter])

  const filteredArtifacts = artifacts.filter((art) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    const matchBase =
      art.id.toLowerCase().includes(q) ||
      art.type.toLowerCase().includes(q) ||
      art.agent_id.toLowerCase().includes(q) ||
      art.job_id.toLowerCase().includes(q)
    if (matchBase) return true

    // Check inside data fields
    try {
      const dataStr = JSON.stringify(art.data).toLowerCase()
      return dataStr.includes(q)
    } catch {
      return false
    }
  })

  const getCollectorBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case 'process':
        return <Badge variant="info">process</Badge>
      case 'connection':
      case 'network':
      case 'network_connection':
        return <Badge variant="default">connection</Badge>
      case 'autorun':
        return <Badge variant="warning">autorun</Badge>
      case 'scheduled_task':
        return <Badge variant="info">scheduled_task</Badge>
      case 'user':
        return <Badge variant="success">user</Badge>
      case 'session':
        return <Badge variant="outline">session</Badge>
      default:
        return <Badge variant="default">{type}</Badge>
    }
  }

  const renderArtifactSummary = (art: Artifact) => {
    const d = art.data || {}
    switch (art.type.toLowerCase()) {
      case 'process':
        return (
          <span>
            PID <strong className="text-cyan-400">{d.pid ?? 'N/A'}</strong> —{' '}
            <span className="text-slate-200">{d.name || d.executable_path || 'unknown'}</span>
            {d.signature_status && (
              <span className={`ml-2 text-[10px] px-1 py-0.5 rounded ${
                d.signature_status === 'unsigned' ? 'bg-rose-950/60 text-rose-400' : 'bg-slate-800 text-slate-400'
              }`}>
                {d.signature_status}
              </span>
            )}
          </span>
        )
      case 'connection':
      case 'network':
      case 'network_connection':
        return (
          <span>
            {d.protocol || 'TCP'} {d.local_address || d.local_ip}:{d.local_port} →{' '}
            <strong className="text-slate-200">{d.remote_address || d.remote_ip || d.dest_ip}:{d.remote_port || d.dest_port}</strong>
            {d.state && <span className="ml-2 text-slate-500">({d.state})</span>}
          </span>
        )
      case 'autorun':
        return (
          <span>
            <strong className="text-amber-400">{d.name || 'Autorun'}</strong>: {d.command || d.location || 'N/A'}
          </span>
        )
      case 'scheduled_task':
        return (
          <span>
            <strong className="text-cyan-400">{d.name || d.path || 'Task'}</strong> — Action: {d.action || 'N/A'}
          </span>
        )
      case 'user':
        return (
          <span>
            User: <strong className="text-emerald-400">{d.username}</strong> (UID: {d.uid ?? d.sid ?? 'N/A'}, Shell: {d.shell || 'N/A'})
          </span>
        )
      case 'session':
        return (
          <span>
            Session: <strong className="text-slate-200">{d.username}</strong> on {d.terminal || d.session_name || 'tty'} ({d.state || 'Active'})
          </span>
        )
      default:
        return <span>{JSON.stringify(d).slice(0, 80)}...</span>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Forensic Artifacts</h1>
          <p className="text-sm text-slate-400 mt-1">
            Read-only evidence telemetry collected across fleet processes, connections, persistence, and identities.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadArtifacts}>
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={loadArtifacts} />}

      {/* Filters Bar */}
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mr-1">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            Artifact Type:
          </span>
          {[
            'all',
            'process',
            'connection',
            'autorun',
            'scheduled_task',
            'user',
            'session',
          ].map((type) => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              className={`px-2.5 py-1 text-xs rounded-md font-mono capitalize transition-colors ${
                typeFilter === type
                  ? 'bg-cyan-950 border border-cyan-800 text-cyan-400'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Search & ID Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search evidence fields, names, paths..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          <div>
            <input
              type="text"
              placeholder="Filter by Job ID (e.g. job-78a9c2b0)..."
              value={jobIdFilter}
              onChange={(e) => setJobIdFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 font-mono"
            />
          </div>

          <div>
            <input
              type="text"
              placeholder="Filter by Agent ID..."
              value={agentIdFilter}
              onChange={(e) => setAgentIdFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 font-mono"
            />
          </div>
        </div>
      </div>

      {/* Main Artifacts Table */}
      {isLoading ? (
        <LoadingSpinner label="Loading collected artifacts from database..." />
      ) : filteredArtifacts.length === 0 ? (
        <EmptyState
          icon={<Layers className="w-6 h-6 text-slate-500" />}
          title="No forensic artifacts found"
          description={
            jobIdFilter || agentIdFilter || typeFilter !== 'all' || searchQuery
              ? 'No artifacts match the current filter criteria.'
              : 'No artifacts have been ingested yet. Execute a JOCKY investigation to collect evidence.'
          }
          actionLabel="Clear Filters"
          onAction={() => {
            setTypeFilter('all')
            setJobIdFilter('')
            setAgentIdFilter('')
            setSearchQuery('')
          }}
        />
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/50 text-slate-400 text-xs uppercase tracking-wider font-mono">
                  <th className="py-3 px-4">Artifact ID</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Agent</th>
                  <th className="py-3 px-4">Job ID</th>
                  <th className="py-3 px-4">Evidence Summary</th>
                  <th className="py-3 px-4">Collected At</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {filteredArtifacts.map((art) => (
                  <tr
                    key={art.id}
                    onClick={() => setSelectedArtifact(art)}
                    className="hover:bg-slate-800/30 transition-colors cursor-pointer"
                  >
                    <td className="py-3.5 px-4 font-semibold text-slate-300">{art.id}</td>
                    <td className="py-3.5 px-4">{getCollectorBadge(art.type)}</td>
                    <td className="py-3.5 px-4 text-cyan-400">{art.agent_id}</td>
                    <td className="py-3.5 px-4 text-slate-400">{art.job_id}</td>
                    <td className="py-3.5 px-4 text-slate-300 max-w-md truncate">
                      {renderArtifactSummary(art)}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(art.collected_at).toLocaleTimeString()}</span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedArtifact(art)
                        }}
                      >
                        <Eye className="w-3 h-3" />
                        View
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Detail Inspection Modal / Drawer */}
      {selectedArtifact && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl max-h-[85vh] overflow-y-auto border-cyan-800/60 bg-[#0d1322] shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <Layers className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-sm font-bold text-slate-100 font-mono">{selectedArtifact.id}</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    {getCollectorBadge(selectedArtifact.type)}
                    <span className="text-xs text-slate-400 font-mono">Agent: {selectedArtifact.agent_id}</span>
                  </div>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedArtifact(null)}>
                ✕ Close
              </Button>
            </div>

            {/* Artifact Normalized Fields */}
            <div className="space-y-3 font-mono text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Originating Job</span>
                  <span className="text-cyan-400 font-medium">{selectedArtifact.job_id}</span>
                </div>
                <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                  <span className="text-slate-500 block text-[10px] uppercase">Collection Timestamp</span>
                  <span className="text-slate-200 font-medium">
                    {new Date(selectedArtifact.collected_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Data Table */}
              <div className="p-3 bg-slate-900/80 rounded-lg border border-slate-800 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                  <span className="text-slate-400 font-bold uppercase text-[10px]">
                    Normalized Telemetry Fields
                  </span>
                  <button
                    onClick={() => setShowRawJson(!showRawJson)}
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                  >
                    <FileCode className="w-3 h-3" />
                    <span>{showRawJson ? 'Structured View' : 'Raw JSON'}</span>
                  </button>
                </div>

                {showRawJson ? (
                  <pre className="text-[11px] text-slate-300 bg-slate-950 p-3 rounded overflow-x-auto border border-slate-800">
                    {JSON.stringify(selectedArtifact.data, null, 2)}
                  </pre>
                ) : (
                  <div className="space-y-1.5 divide-y divide-slate-800/60">
                    {Object.entries(selectedArtifact.data || {}).map(([key, val]) => (
                      <div key={key} className="pt-1.5 flex items-start justify-between gap-4">
                        <span className="text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="text-slate-200 text-right break-all">
                          {typeof val === 'boolean'
                            ? val ? 'true' : 'false'
                            : typeof val === 'object' && val !== null
                            ? JSON.stringify(val)
                            : String(val ?? '—')}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Cross Links */}
            {onNavigate && (
              <div className="pt-2 border-t border-slate-800 flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedArtifact(null)
                    onNavigate('deployments', { jobId: selectedArtifact.job_id })
                  }}
                >
                  Jump to Job Feed
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedArtifact(null)
                    onNavigate('threats', { jobId: selectedArtifact.job_id, agentId: selectedArtifact.agent_id })
                  }}
                >
                  View Related Detections
                </Button>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
