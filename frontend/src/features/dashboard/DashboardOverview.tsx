import React, { useEffect, useState } from 'react'
import {
  Server,
  Layers,
  AlertTriangle,
  Activity,
  Code2,
  RefreshCw,
  CheckCircle2,
  Clock,
  ArrowRight,
} from 'lucide-react'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { Button } from '../../components/common/Button'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { fetchAgents, fetchJobs, fetchArtifacts, fetchDetections } from '../../api'
import { Agent, Job, Artifact, Detection } from '../../types'
import { NavTab } from '../../components/layout/Sidebar'

interface DashboardOverviewProps {
  onNavigate: (tab: NavTab, filterContext?: { jobId?: string; agentId?: string; type?: string }) => void
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ onNavigate }) => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [detections, setDetections] = useState<Detection[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [agentsRes, jobsRes, artifactsRes, detectionsRes] = await Promise.all([
        fetchAgents(),
        fetchJobs(),
        fetchArtifacts({ limit: 10 }),
        fetchDetections({ limit: 10 }),
      ])
      setAgents(agentsRes.items || [])
      setJobs(jobsRes || [])
      setArtifacts(artifactsRes.items || [])
      setDetections(detectionsRes.items || [])
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve telemetry overview from management server.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const onlineAgents = agents.filter((a) => a.status === 'online').length
  const activeJobs = jobs.filter((j) => j.status === 'queued' || j.status === 'running').length
  const criticalDetections = detections.filter(
    (d) => d.severity.toLowerCase() === 'critical' || d.severity.toLowerCase() === 'high'
  ).length

  if (isLoading) {
    return <LoadingSpinner label="Loading operational dashboard metrics..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Forensic Triage Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time fleet visibility, evidence ingestion metrics, and threat correlation status.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
          <Button variant="primary" size="sm" onClick={() => onNavigate('editor')}>
            <Code2 className="w-3.5 h-3.5" />
            New Investigation
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={loadData} />}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="hover:border-slate-700 transition-colors cursor-pointer" onClick={() => onNavigate('fleet')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Fleet Coverage</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">
                {onlineAgents} <span className="text-xs font-normal text-slate-500">/ {agents.length} online</span>
              </p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-cyan-950/40 border border-cyan-800/40 flex items-center justify-center text-cyan-400">
              <Server className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-[11px] text-cyan-400 font-mono">
            <span>Inspect fleet agents</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Card>

        <Card className="hover:border-slate-700 transition-colors cursor-pointer" onClick={() => onNavigate('deployments')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Forensic Jobs</p>
              <p className="text-2xl font-bold text-slate-100 mt-1">
                {activeJobs} <span className="text-xs font-normal text-slate-500">active ({jobs.length} total)</span>
              </p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-blue-950/40 border border-blue-800/40 flex items-center justify-center text-blue-400">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-[11px] text-blue-400 font-mono">
            <span>View job dispatch queue</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Card>

        <Card className="hover:border-slate-700 transition-colors cursor-pointer" onClick={() => onNavigate('results')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Artifacts Ingested</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{artifacts.length}</p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-950/40 border border-emerald-800/40 flex items-center justify-center text-emerald-400">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-[11px] text-emerald-400 font-mono">
            <span>Browse forensic artifacts</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Card>

        <Card className="hover:border-slate-700 transition-colors cursor-pointer" onClick={() => onNavigate('threats')}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">Correlated Detections</p>
              <p className="text-2xl font-bold text-rose-400 mt-1">
                {detections.length}{' '}
                {criticalDetections > 0 && (
                  <span className="text-xs font-semibold text-rose-500">({criticalDetections} High/Crit)</span>
                )}
              </p>
            </div>
            <div className="w-10 h-10 rounded-lg bg-rose-950/40 border border-rose-800/40 flex items-center justify-center text-rose-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-[11px] text-rose-400 font-mono">
            <span>Triage detections</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </Card>
      </div>

      {/* Collector Architecture Status */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Endpoint Collector Architecture
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Read-only collector status across Go agent runtime.
            </p>
          </div>
          <Badge variant="info">Phase 6 Verified</Badge>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 text-xs">
          {[
            { name: 'processes', type: 'real' },
            { name: 'connections', type: 'real' },
            { name: 'autoruns', type: 'real' },
            { name: 'scheduled_tasks', type: 'real' },
            { name: 'users', type: 'real' },
            { name: 'sessions', type: 'real' },
            { name: 'files', type: 'placeholder' },
            { name: 'drivers', type: 'placeholder' },
            { name: 'services', type: 'placeholder' },
            { name: 'event_logs', type: 'placeholder' },
          ].map((col) => (
            <div
              key={col.name}
              className={`p-2.5 rounded-lg border flex items-center justify-between font-mono text-[11px] ${
                col.type === 'real'
                  ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                  : 'bg-slate-900/50 border-slate-800 text-slate-500'
              }`}
            >
              <span>{col.name}</span>
              {col.type === 'real' ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              ) : (
                <span className="text-[9px] px-1 py-0.5 rounded bg-slate-800 border border-slate-700">stub</span>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Dual Column: Recent Jobs & Recent Threats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-slate-200 font-mono">Recent Jobs</h3>
            </div>
            <Button variant="ghost" size="sm" onClick={() => onNavigate('deployments')}>
              View All
            </Button>
          </div>

          {jobs.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">No forensic jobs executed yet.</p>
          ) : (
            <div className="space-y-2.5">
              {jobs.slice(0, 5).map((job) => (
                <div
                  key={job.id}
                  onClick={() => onNavigate('deployments', { jobId: job.id })}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-cyan-400">{job.id}</span>
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
                    <p className="text-[11px] text-slate-400">
                      Target: <span className="text-slate-300 font-mono">{job.target_agents.join(', ') || 'N/A'}</span>
                    </p>
                  </div>
                  <div className="text-right text-[11px] text-slate-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(job.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Threat Detections */}
        <Card>
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <h3 className="text-sm font-semibold text-slate-200 font-mono">Recent Detections</h3>
            </div>
            <Button variant="ghost" size="sm" onClick={() => onNavigate('threats')}>
              View All
            </Button>
          </div>

          {detections.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">No threat detections recorded.</p>
          ) : (
            <div className="space-y-2.5">
              {detections.slice(0, 5).map((det) => (
                <div
                  key={det.id}
                  onClick={() => onNavigate('threats', { jobId: det.job_id, agentId: det.agent_id })}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-200">{det.title}</span>
                      <Badge
                        variant={
                          det.severity.toLowerCase() === 'critical' || det.severity.toLowerCase() === 'high'
                            ? 'danger'
                            : det.severity.toLowerCase() === 'medium'
                            ? 'warning'
                            : 'default'
                        }
                      >
                        {det.severity}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span className="font-mono text-cyan-400">{det.rule_id}</span>
                      <span>•</span>
                      <span>Agent: {det.agent_id}</span>
                    </div>
                  </div>
                  <div className="text-right text-[11px] text-slate-500">
                    {new Date(det.created_at).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
