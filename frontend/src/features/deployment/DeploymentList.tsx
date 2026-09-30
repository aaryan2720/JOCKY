import React, { useEffect, useState } from 'react'
import {
  Activity,
  RefreshCw,
  Clock,
  Radio,
  Layers,
  AlertTriangle,
  Terminal,
} from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { fetchJobs, fetchJob } from '../../api'
import { Job } from '../../types'
import { useJobWebSocket } from '../../hooks/useJobWebSocket'
import { NavTab } from '../../components/layout/Sidebar'

interface DeploymentListProps {
  initialJobId?: string
  onNavigate?: (tab: NavTab, context?: { jobId?: string; agentId?: string }) => void
}

export const DeploymentList: React.FC<DeploymentListProps> = ({ initialJobId, onNavigate }) => {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJobId, setSelectedJobId] = useState<string | null>(initialJobId || null)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const loadJobs = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchJobs(undefined, statusFilter !== 'all' ? statusFilter : undefined)
      setJobs(data || [])
      if (!selectedJobId && data && data.length > 0) {
        setSelectedJobId(data[0].id)
      }
    } catch (err: any) {
      setError(err.message || 'Unable to retrieve jobs history.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadJobs()
  }, [statusFilter])

  useEffect(() => {
    if (selectedJobId) {
      fetchJob(selectedJobId)
        .then((job) => setSelectedJob(job))
        .catch(() => {})
    }
  }, [selectedJobId])

  // Live WebSocket for selected job
  const { status: wsStatus, events: liveEvents, clearEvents } = useJobWebSocket(selectedJobId || undefined, {
    onMessage: (msg) => {
      if (msg.event === 'job_status' && msg.status && selectedJob) {
        setSelectedJob((prev) => (prev ? { ...prev, status: msg.status || prev.status } : null))
      }
    },
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Forensic Jobs & Live Stream</h1>
          <p className="text-sm text-slate-400 mt-1">
            Dispatch queue, execution status, and live WebSocket telemetry feeds from endpoint agents.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadJobs}>
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
          {onNavigate && (
            <Button variant="primary" size="sm" onClick={() => onNavigate('editor')}>
              New Dispatch
            </Button>
          )}
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={loadJobs} />}

      {/* Main Layout: Jobs List + Live Telemetry Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Jobs List (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-300 font-mono">Job History</h2>
            <div className="flex gap-1">
              {['all', 'queued', 'running', 'completed'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-0.5 text-[11px] rounded font-mono capitalize transition-colors ${
                    statusFilter === st
                      ? 'bg-cyan-950 border border-cyan-800 text-cyan-400'
                      : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {isLoading ? (
            <LoadingSpinner label="Loading execution history..." />
          ) : jobs.length === 0 ? (
            <EmptyState
              icon={<Activity className="w-6 h-6 text-slate-500" />}
              title="No jobs recorded"
              description="No investigations have been dispatched yet. Write and dispatch a JOCKY script in the editor."
              actionLabel="Go to Editor"
              onAction={() => onNavigate && onNavigate('editor')}
            />
          ) : (
            <div className="space-y-2.5">
              {jobs.map((job) => {
                const isSelected = selectedJobId === job.id
                return (
                  <div
                    key={job.id}
                    onClick={() => {
                      setSelectedJobId(job.id)
                      clearEvents()
                    }}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-cyan-950/20 border-cyan-800/80 shadow-md shadow-cyan-950/30'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs font-bold text-cyan-400">{job.id}</span>
                      <Badge
                        variant={
                          job.status === 'completed'
                            ? 'success'
                            : job.status === 'running'
                            ? 'info'
                            : job.status === 'failed'
                            ? 'danger'
                            : 'default'
                        }
                      >
                        {job.status}
                      </Badge>
                    </div>

                    <div className="text-xs text-slate-400 space-y-1 font-mono">
                      <p>
                        Target: <span className="text-slate-200">{job.target_agents.join(', ') || 'N/A'}</span>
                      </p>
                      {job.plan?.collectors && (
                        <p className="text-[11px] text-slate-500">
                          Collectors: {job.plan.collectors.map((c) => c.target).join(', ')}
                        </p>
                      )}
                    </div>

                    <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(job.created_at).toLocaleTimeString()}</span>
                      </div>
                      {isSelected && (
                        <span className="text-cyan-400 font-mono text-[10px] flex items-center gap-1">
                          <Radio className="w-2.5 h-2.5 animate-pulse" />
                          Streaming
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Live Monitoring Feed (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {selectedJob ? (
            <div className="space-y-4">
              {/* Job Details Card */}
              <Card className="space-y-4 border-slate-800">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-100 font-mono">{selectedJob.id}</h3>
                      <Badge
                        variant={
                          selectedJob.status === 'completed'
                            ? 'success'
                            : selectedJob.status === 'running'
                            ? 'info'
                            : selectedJob.status === 'failed'
                            ? 'danger'
                            : 'default'
                        }
                      >
                        {selectedJob.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">
                      Created: {new Date(selectedJob.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge
                      variant={
                        wsStatus === 'connected'
                          ? 'success'
                          : wsStatus === 'connecting'
                          ? 'warning'
                          : 'default'
                      }
                    >
                      <Radio
                        className={`w-3 h-3 ${wsStatus === 'connected' ? 'text-emerald-400 animate-pulse' : ''}`}
                      />
                      <span>WS: {wsStatus}</span>
                    </Badge>
                  </div>
                </div>

                {/* Plan Metadata */}
                <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                  <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Target Agent(s)</span>
                    <span className="text-slate-200 font-medium">{selectedJob.target_agents.join(', ')}</span>
                  </div>
                  <div className="p-2.5 bg-slate-900/60 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Plan Collectors</span>
                    <span className="text-cyan-400 font-medium">
                      {selectedJob.plan?.collectors
                        ? selectedJob.plan.collectors.map((c) => c.target).join(', ')
                        : 'Default Fleet Sweep'}
                    </span>
                  </div>
                </div>

                {/* Quick Triage Buttons */}
                {onNavigate && (
                  <div className="flex items-center gap-3 pt-1 border-t border-slate-800">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onNavigate('results', { jobId: selectedJob.id })}
                    >
                      <Layers className="w-3.5 h-3.5" />
                      Inspect Artifacts for this Job
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onNavigate('threats', { jobId: selectedJob.id })}
                    >
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Inspect Detections for this Job
                    </Button>
                  </div>
                )}
              </Card>

              {/* Live WebSocket Event Stream Terminal */}
              <Card className="p-0 overflow-hidden border-slate-800 bg-[#090d16]">
                <div className="px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between font-mono text-xs">
                  <div className="flex items-center gap-2 text-cyan-400">
                    <Terminal className="w-4 h-4" />
                    <span>Live Event Stream (/ws/jobs/{selectedJob.id})</span>
                  </div>
                  <span className="text-[11px] text-slate-500">{liveEvents.length} events received</span>
                </div>

                <div className="p-4 space-y-2 font-mono text-xs max-h-[380px] overflow-y-auto">
                  {liveEvents.length === 0 ? (
                    <div className="py-8 text-center text-slate-500 space-y-1">
                      <p>Subscribed to WebSocket feed. Awaiting agent telemetry events...</p>
                      <p className="text-[10px] text-slate-600">
                        Artifacts ingested for job {selectedJob.id} will stream here live.
                      </p>
                    </div>
                  ) : (
                    liveEvents.map((evt, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 space-y-1"
                      >
                        <div className="flex items-center justify-between text-[11px]">
                          <span
                            className={`font-semibold uppercase tracking-wider ${
                              evt.event === 'threat_detected'
                                ? 'text-rose-400'
                                : evt.event === 'artifact_collected'
                                ? 'text-emerald-400'
                                : evt.event === 'connected'
                                ? 'text-cyan-400'
                                : 'text-slate-300'
                            }`}
                          >
                            [{evt.event}]
                          </span>
                          <span className="text-slate-500">
                            {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'Just now'}
                          </span>
                        </div>

                        {evt.message && <p className="text-slate-300">{evt.message}</p>}

                        {evt.event === 'artifact_collected' && evt.payload && (
                          <div className="text-[11px] text-slate-400 bg-slate-950 p-2 rounded border border-slate-800/60">
                            <span className="text-emerald-400 font-semibold">{evt.payload.type}</span> from{' '}
                            <span className="text-slate-300">{evt.agent_id}</span>
                            <pre className="text-[10px] text-slate-500 mt-1 overflow-x-auto">
                              {JSON.stringify(evt.payload.data || evt.payload, null, 2)}
                            </pre>
                          </div>
                        )}

                        {evt.event === 'threat_detected' && evt.detection && (
                          <div className="text-[11px] text-rose-300 bg-rose-950/30 p-2 rounded border border-rose-800/50">
                            <span className="font-bold text-rose-400">{evt.detection.title}</span> ({evt.detection.rule_id})
                            <p className="text-[10px] text-rose-300/80 mt-0.5">{evt.detection.description}</p>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </Card>
            </div>
          ) : (
            <EmptyState
              icon={<Activity className="w-6 h-6 text-slate-500" />}
              title="Select a job"
              description="Click on a job from the history list to open its live telemetry feed and inspect execution details."
            />
          )}
        </div>
      </div>
    </div>
  )
}
