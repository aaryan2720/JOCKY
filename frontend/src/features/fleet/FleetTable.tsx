import React, { useEffect, useState } from 'react'
import {
  Server,
  RefreshCw,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  AlertTriangle,
  Play,
  Copy,
  Check,
} from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { fetchAgents } from '../../api'
import { Agent } from '../../types'
import { NavTab } from '../../components/layout/Sidebar'

interface FleetTableProps {
  onNavigate?: (tab: NavTab, context?: { agentId?: string; jobId?: string }) => void
}

export const FleetTable: React.FC<FleetTableProps> = ({ onNavigate }) => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [copiedFingerprint, setCopiedFingerprint] = useState(false)

  const loadAgents = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetchAgents(statusFilter !== 'all' ? statusFilter : undefined)
      setAgents(response.items || [])
      if (selectedAgent) {
        const updated = (response.items || []).find((a) => a.id === selectedAgent.id)
        if (updated) setSelectedAgent(updated)
      }
    } catch (err: any) {
      setError(err.message || 'Unable to load agents from management server.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadAgents()
  }, [statusFilter])

  const filteredAgents = agents.filter((agent) => {
    const query = searchQuery.toLowerCase()
    return (
      agent.id.toLowerCase().includes(query) ||
      agent.hostname.toLowerCase().includes(query) ||
      agent.os.toLowerCase().includes(query) ||
      (agent.ip_address && agent.ip_address.includes(query)) ||
      (agent.tags && agent.tags.some((t) => t.toLowerCase().includes(query)))
    )
  })

  const onlineCount = agents.filter((a) => a.status === 'online').length

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedFingerprint(true)
    setTimeout(() => setCopiedFingerprint(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight font-mono">Fleet Agents</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time status of enrolled cross-platform forensic collection agents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadAgents}>
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={loadAgents} />}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 font-mono uppercase tracking-wider">Total Enrolled</p>
              <p className="text-2xl font-bold text-slate-100 mt-1 font-mono">{agents.length}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <Server className="w-5 h-5" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 font-mono uppercase tracking-wider">Active Online Agents</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1 font-mono">{onlineCount}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-950/60 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400 font-mono uppercase tracking-wider">Offline / Disconnected</p>
              <p className="text-2xl font-bold text-slate-400 mt-1 font-mono">{agents.length - onlineCount}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-400">
              <XCircle className="w-5 h-5" />
            </div>
          </div>
        </Card>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by ID, hostname, IP, tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900/80 border border-slate-800 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 font-mono"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Status:</span>
          {['all', 'online', 'offline'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 text-xs rounded-md font-mono capitalize transition-colors cursor-pointer ${
                statusFilter === st
                  ? 'bg-cyan-950 border border-cyan-800 text-cyan-300 font-bold'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Main Table */}
      {isLoading ? (
        <LoadingSpinner label="Fetching fleet telemetry..." />
      ) : filteredAgents.length === 0 ? (
        <EmptyState
          icon={<Server className="w-6 h-6 text-slate-500" />}
          title="No agents found"
          description={searchQuery ? 'No agents match your search criteria.' : 'No agents are currently registered with the server.'}
          actionLabel="Refresh Fleet"
          onAction={loadAgents}
        />
      ) : (
        <Card className="p-0 overflow-hidden border-slate-800">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/70 text-slate-400 text-xs uppercase tracking-wider font-mono">
                  <th className="py-3 px-4">Agent ID</th>
                  <th className="py-3 px-4">Hostname</th>
                  <th className="py-3 px-4">Platform</th>
                  <th className="py-3 px-4">IP Address</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Tags</th>
                  <th className="py-3 px-4">Last Seen</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {filteredAgents.map((agent) => {
                  const isSelected = selectedAgent?.id === agent.id
                  return (
                    <tr
                      key={agent.id}
                      onClick={() => setSelectedAgent(agent)}
                      className={`hover:bg-slate-800/40 transition-colors cursor-pointer ${
                        isSelected ? 'bg-cyan-950/20 border-l-2 border-l-cyan-400' : ''
                      }`}
                    >
                      <td className="py-3.5 px-4 font-semibold text-cyan-400">{agent.id}</td>
                      <td className="py-3.5 px-4 text-slate-100 font-medium">{agent.hostname}</td>
                      <td className="py-3.5 px-4">
                        <span className="capitalize text-slate-300 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-[11px]">
                          {agent.os}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">{agent.ip_address || '127.0.0.1'}</td>
                      <td className="py-3.5 px-4">
                        <Badge
                          variant={
                            agent.status === 'online'
                              ? 'success'
                              : agent.status === 'offline'
                              ? 'danger'
                              : 'default'
                          }
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              agent.status === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
                            }`}
                          />
                          {agent.status}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex gap-1 flex-wrap">
                          {agent.tags && agent.tags.length > 0 ? (
                            agent.tags.map((tag) => (
                              <span
                                key={tag}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60"
                              >
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span className="text-slate-600 text-[10px]">—</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 flex items-center gap-1.5">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{agent.last_seen ? new Date(agent.last_seen).toLocaleTimeString() : 'N/A'}</span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedAgent(agent)
                          }}
                        >
                          Details
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Agent Detail Modal / Inspector Drawer */}
      {selectedAgent && (
        <Card className="border-cyan-800/60 bg-[#0d1322]/95 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-cyan-950/70 border border-cyan-800/70 flex items-center justify-center text-cyan-400">
                <Server className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100 font-mono">{selectedAgent.hostname}</h3>
                <p className="text-xs text-slate-400 font-mono">{selectedAgent.id}</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setSelectedAgent(null)}>
              ✕ Close
            </Button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Operating System</span>
              <span className="text-slate-200 capitalize font-medium mt-0.5 block">{selectedAgent.os}</span>
            </div>
            <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-bold">IP Address</span>
              <span className="text-slate-200 font-medium mt-0.5 block">{selectedAgent.ip_address || '127.0.0.1'}</span>
            </div>
            <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Agent Version</span>
              <span className="text-slate-200 font-medium mt-0.5 block">{selectedAgent.version || '0.1.0'}</span>
            </div>
            <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Status</span>
              <div className="mt-0.5">
                <Badge variant={selectedAgent.status === 'online' ? 'success' : 'danger'}>
                  {selectedAgent.status}
                </Badge>
              </div>
            </div>
          </div>

          <div className="p-3 bg-slate-900/70 rounded-lg border border-slate-800 text-xs font-mono flex items-center justify-between gap-3">
            <div className="overflow-hidden">
              <span className="text-slate-500 block text-[10px] uppercase font-bold mb-0.5">Certificate Fingerprint</span>
              <span className="text-cyan-400 break-all font-mono text-[11px]">{selectedAgent.cert_fingerprint || 'N/A'}</span>
            </div>
            {selectedAgent.cert_fingerprint && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(selectedAgent.cert_fingerprint || '')}
                className="shrink-0 text-slate-400 hover:text-white"
              >
                {copiedFingerprint ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedFingerprint ? 'Copied' : 'Copy'}
              </Button>
            )}
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            {onNavigate && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onNavigate('editor', { agentId: selectedAgent.id })}
                >
                  <Play className="w-3.5 h-3.5" />
                  Investigate Agent with JOCKY
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onNavigate('results', { agentId: selectedAgent.id })}
                >
                  <Layers className="w-3.5 h-3.5" />
                  View Agent Artifacts
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onNavigate('threats', { agentId: selectedAgent.id })}
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  View Agent Detections
                </Button>
              </>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}

